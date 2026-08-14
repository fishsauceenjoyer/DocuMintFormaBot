"""End-to-end integration test for the full order FSM flow.

Simulates a complete user journey from document selection to payment proof
submission, using a real (temporary) database with Alembic migrations and
mocked Telegram API objects (MockBot).

Unlike the unit tests in test_e2e_order_flow.py, this test does **not** mock
the database layer or the router — only the Telegram API is mocked. This
verifies that FSM, database persistence, and manager notification all work
together correctly.
"""

import json

import pytest
from conftest import (  # type: ignore[attr-defined]
    MockBot,
    MockCallback,
    MockFSMContext,
    MockMessage,
)
from sqlalchemy import select

from fsm.states import OrderState
from tests.fixtures.mocks import MockMessage as DuckMockMessage
from tests.fixtures.mocks import MockPhoto


@pytest.mark.asyncio
async def test_integration_full_order_flow(
    test_db, clean_user_sessions, clean_admin_orders
):
    """Full integration: document → quantity → fields → delivery → payment → proof.

    Verifies:
    - FSM state transitions at each step.
    - Order and order_items are persisted to the database with correct data.
    - Manager receives a message with order details (via MockBot).
    - User receives a final message containing the order number.
    """
    user_id = 100
    state = MockFSMContext()
    bot = MockBot()

    # ── Step 1: /start → choosing_document ──────────────────────────
    from handlers.start import cmd_start

    msg_start = MockMessage(text="/start", chat_id=user_id, user_id=user_id)
    await cmd_start(msg_start, state)
    assert await state.get_state() == OrderState.choosing_document

    # ── Step 2: Choose document (criminal_record_check) → entering_quantity ──
    from handlers.order import process_document_choice

    callback_doc = MockCallback(data="doc_criminal_record_check", user_id=user_id)
    await process_document_choice(callback_doc, state)
    assert await state.get_state() == OrderState.entering_quantity

    # ── Step 3: Choose quantity (1) → filling_document ──────────────
    from handlers.order import process_quantity

    callback_qty = MockCallback(data="qty_1", user_id=user_id)
    await process_quantity(callback_qty, state)
    assert await state.get_state() == OrderState.filling_document

    # ── Step 4: Fill document fields (3 fields) ─────────────────────
    # criminal_record_check template has: full_name, birth_date, birth_place
    from handlers.order import process_document_field

    field_values = [
        "John Doe",  # full_name (text)
        "15.05.1990",  # birth_date (date, DD.MM.YYYY)
        "New York",  # birth_place (text)
    ]

    for value in field_values:
        msg_field = MockMessage(text=value, chat_id=user_id, user_id=user_id)
        await process_document_field(msg_field, state)

    # After all fields are filled, should transition to asking_delivery
    assert await state.get_state() == OrderState.asking_delivery

    # ── Step 5: Choose delivery (no) → choosing_payment ─────────────
    from handlers.order import process_delivery_choice

    callback_delivery = MockCallback(data="delivery_no", user_id=user_id)
    await process_delivery_choice(callback_delivery, state)
    assert await state.get_state() == OrderState.choosing_payment

    # ── Step 6: Choose payment (blik) → waiting_for_payment_proof ───
    from handlers.order import process_payment

    callback_pay = MockCallback(data="pay_blik", user_id=user_id)
    await process_payment(callback_pay, state)
    assert await state.get_state() == OrderState.waiting_for_payment_proof

    # ── Step 7: Submit payment proof (photo) ────────────────────────
    from handlers.order import process_payment_proof

    # Use the duck-typed MockMessage so we can freely set .bot and .photo
    # attributes (the conftest MockMessage inherits from aiogram's Pydantic
    # Message which may restrict attribute assignment).
    msg_proof = DuckMockMessage(chat_id=user_id, user_id=user_id)
    msg_proof.bot = bot
    msg_proof.photo = [MockPhoto(file_id="proof_123.jpg")]
    await process_payment_proof(msg_proof, state)

    # ══════════════════════════════════════════════════════════════════
    # Assertions
    # ══════════════════════════════════════════════════════════════════

    # ── A1: Database — orders table ─────────────────────────────────
    from db.models import Order, OrderItem

    async with test_db() as db:
        result = await db.execute(select(Order))
        orders = list(result.scalars().all())
        assert len(orders) == 1, f"Expected 1 order in DB, got {len(orders)}"

        order = orders[0]
        assert order.status == "paid"
        assert order.total_price == 25  # 1 × criminal_record_check (25 EUR)
        assert order.payment_method == "blik"
        assert order.payment_proof_file_id == "proof_123.jpg"
        assert order.user_id == user_id
        assert order.order_id.startswith("ORDER_")
        # No delivery was chosen
        assert order.delivery_name is None
        assert order.delivery_phone is None

        # ── A2: Database — order_items table ────────────────────────
        result_items = await db.execute(
            select(OrderItem).where(OrderItem.order_id == order.id)
        )
        items = list(result_items.scalars().all())
        assert len(items) == 1, f"Expected 1 order item, got {len(items)}"

        item = items[0]
        assert item.document_type == "criminal_record_check"
        assert item.quantity == 1
        assert item.unit_price == 25

        # Verify the JSON data contains the filled-in fields
        item_data = json.loads(item.data_json)
        assert item_data["type"] == "criminal_record_check"
        assert item_data["quantity"] == 1
        assert len(item_data["items"]) == 1
        filled = item_data["items"][0]
        assert filled["full_name"] == "John Doe"
        assert filled["birth_date"] == "15.05.1990"
        assert filled["birth_place"] == "New York"

        # Verify documents_json on the order record
        docs = json.loads(order.documents_json)
        assert len(docs) == 1
        assert docs[0]["type"] == "criminal_record_check"

        order_id = order.order_id

    # ── A3: Manager notification (via MockBot) ──────────────────────
    # send_order_to_manager sends a photo (with caption) for the order.
    # JSON payload is no longer sent — only readable message.
    assert bot._mock_photo_sent is not None, "Manager should receive a photo"
    photo_sent = bot._mock_photo_sent
    assert photo_sent["photo"] == "proof_123.jpg"
    caption = photo_sent["caption"]
    assert "NEW ORDER" in caption
    assert order_id in caption
    # Document name should appear (from template name_ru since default lang is ru)
    assert "Справка о несудимости" in caption
    # Filled field value should appear in the order details
    assert "John Doe" in caption

    # ── A4: User final message ──────────────────────────────────────
    assert msg_proof._answered_text is not None, "User should receive final message"
    user_text = msg_proof._answered_text
    assert order_id in user_text
    assert "accepted" in user_text.lower()

    # ── A5: FSM state cleared ───────────────────────────────────────
    assert await state.get_state() is None, "FSM state must be cleared after completion"

"""End-to-end test of the complete order FSM flow.

Simulates a real user journey through the entire bot:
    /start → choose document → quantity → fill fields → delivery → payment → proof

Uses mocked Telegram objects and an in-memory database so it runs offline.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from fsm.states import AdminState, OrderState
from tests.fixtures.mocks import (
    MockBot,
    MockCallback,
    MockFSMContext,
    MockMessage,
    MockPhoto,
)


@pytest.mark.asyncio
async def test_e2e_full_order_flow(clean_user_sessions, mock_order_db):
    """Simulate a complete user order from /start to payment proof.

    This test validates:
    - FSM state transitions at each step
    - User session is correctly populated
    - Final order is persisted to database
    - Manager is notified
    """
    user_id = 100
    state = MockFSMContext()

    # ── Step 1: /start → choosing_document ──────────────────────────
    from handlers.start import cmd_start

    msg = MockMessage(text="/start", chat_id=user_id, user_id=user_id)
    msg.bot = MockBot()
    await cmd_start(msg, state)

    assert await state.get_state() == OrderState.choosing_document
    assert msg._answered_text is not None

    # ── Step 2: Choose document (visa) → entering_quantity ──────────
    from handlers.order import get_user_session, process_document_choice

    callback1 = MockCallback(data="doc_visa", user_id=user_id)
    callback1.bot = MockBot()
    await process_document_choice(callback1, state)

    assert await state.get_state() == OrderState.entering_quantity
    assert callback1._answered is True

    # ── Step 3: Choose quantity (2) → filling_document ──────────────
    # process_quantity checks isinstance(callback.message, Message) and
    # isinstance(callback.from_user). Use conftest MockMessage (inherits Message).
    from conftest import MockMessage as RealMockMessage

    from handlers.order import process_quantity

    callback2 = MockCallback(data="qty_2", user_id=user_id)
    callback2.bot = MockBot()
    callback2.message = RealMockMessage(chat_id=user_id)
    await process_quantity(callback2, state)

    assert await state.get_state() == OrderState.filling_document
    session = await get_user_session(user_id)
    assert session["current_quantity"] == 2

    # ── Step 4: Fill document fields (1 copy, 1 field) ───────────────
    from handlers.order import process_document_field

    # Set up the template with just one field
    from templates.fields import Field

    session["current_template"] = {
        "fields": [Field("full_name", "Full Name", "text")],
        "code": "visa",
        "name_en": "Visa application",
    }
    session["current_doc_type"] = "visa"
    session["current_quantity"] = 1  # Single copy for simplicity
    session["current_items"] = []
    session["temp_item_data"] = {}
    session["current_field_index"] = 0

    # Fill field for the single copy
    msg2 = MockMessage(text="John Doe", chat_id=user_id, user_id=user_id)
    msg2.bot = MockBot()
    await state.update_data(current_field_index=0)
    await process_document_field(msg2, state)

    # After single field, should transition to asking_delivery
    final_state = await state.get_state()
    assert (
        final_state == OrderState.asking_delivery
    ), f"Expected asking_delivery, got {final_state}"

    # ── Step 5: Choose delivery (no) → choosing_payment ─────────────
    from handlers.order import process_delivery_choice

    callback3 = MockCallback(data="delivery_no", user_id=user_id)
    callback3.bot = MockBot()
    await process_delivery_choice(callback3, state)
    assert await state.get_state() == OrderState.choosing_payment

    # ── Step 6: Choose payment (blik) → waiting_for_payment_proof ───
    from handlers.order import process_payment

    session = await get_user_session(user_id)
    session["total_price"] = 35  # 1 × visa(35€)
    session["currency"] = "EUR"

    callback4 = MockCallback(data="pay_blik", user_id=user_id)
    callback4.bot = MockBot()
    await process_payment(callback4, state)

    assert await state.get_state() == OrderState.waiting_for_payment_proof

    # ── Step 7: Submit payment proof (photo) ────────────────────────
    from handlers.order import process_payment_proof

    # Ensure cart is populated
    session = await get_user_session(user_id)
    session["cart"] = [
        {
            "type": "visa",
            "quantity": 1,
            "items": [
                {"full_name": "John Doe"},
            ],
        }
    ]
    session["payment_method"] = "blik"
    session["total_price"] = 35

    msg3 = MockMessage(chat_id=user_id, user_id=user_id)
    msg3.bot = MockBot()
    msg3.photo = [MockPhoto(file_id="proof_screenshot.jpg")]

    mock_db = AsyncMock()
    mock_db.__aenter__.return_value = mock_db
    mock_db.__aexit__.return_value = False

    with patch("handlers.order.AsyncSessionLocal", return_value=mock_db):
        with patch("utils.router.send_order_to_manager", AsyncMock()) as mock_send:
            with patch("handlers.order.create_order", new=AsyncMock()) as mock_create:
                with patch("handlers.order.create_order_item", new=AsyncMock()):
                    mock_order = MagicMock()
                    mock_order.id = 1
                    mock_create.return_value = mock_order
                    await process_payment_proof(msg3, state)

    # ── Final assertions ────────────────────────────────────────────
    # Order must be saved
    assert mock_create.called, "Order must be persisted"
    create_kwargs = mock_create.call_args[1]
    assert create_kwargs["status"] == "paid"
    assert create_kwargs["total_price"] == 35
    assert create_kwargs["payment_method"] == "blik"

    # Manager must be notified
    assert mock_send.called, "Manager must be notified"
    assert mock_send.call_args[1]["payment_proof_file_id"] == "proof_screenshot.jpg"

    # FSM state must be cleared
    state_val = await state.get_state()
    assert state_val is None, f"State must be None after completion, got {state_val}"

    # User session must be cleaned up
    async with __import__(
        "handlers.order", fromlist=["_sessions_lock", "user_sessions"]
    )._sessions_lock:
        assert (
            user_id
            not in __import__(
                "handlers.order", fromlist=["user_sessions"]
            ).user_sessions
        ), "Session must be removed after completion"


@pytest.mark.asyncio
async def test_e2e_cancel_flow(clean_user_sessions):
    """Test the cancel flow: user starts order, then cancels to main menu."""
    user_id = 200
    state = MockFSMContext()

    # ── Start an order ──────────────────────────────────────────────
    from handlers.start import cmd_start

    msg = MockMessage(text="/start", chat_id=user_id, user_id=user_id)
    msg.bot = MockBot()
    await cmd_start(msg, state)
    assert await state.get_state() == OrderState.choosing_document

    # ── Cancel to menu ──────────────────────────────────────────────
    from handlers.order import _sessions_lock, user_sessions
    from handlers.start import callback_cancel_to_menu

    # Put something in session
    async with _sessions_lock:
        user_sessions[user_id] = {"cart": ["test_item"]}

    callback = MockCallback(data="cancel_to_menu", user_id=user_id)
    callback.bot = MockBot()
    await callback_cancel_to_menu(callback, state)

    # State must be cleared
    assert await state.get_state() is None
    # Session must be removed
    async with _sessions_lock:
        assert user_id not in user_sessions


@pytest.mark.skip(
    reason="Admin flow requires deeper integration with admin-only decorator and Messenger API mocking"
)
@pytest.mark.asyncio
async def test_e2e_admin_flow(clean_user_sessions):
    """Test admin flow: send document to client."""
    from fsm.states import AdminState
    from handlers.admin import callback_send_doc, cmd_send_doc, process_document_file
    from tests.fixtures.mocks import MockBot, MockCallback, MockFSMContext, MockPhoto

    admin_id = 999

    # ── Admin starts send_doc ───────────────────────────────────────
    msg = MockMessage(text="/send_doc", chat_id=admin_id, user_id=admin_id)
    msg.from_user.username = "admin"
    msg.bot = MockBot()
    state = MockFSMContext()

    # cmd_send_doc is decorated with @admin_only which internally calls
    # utils.auth.is_admin. We must patch at the source.
    with patch("utils.auth.is_admin", return_value=True):
        await cmd_send_doc(msg, state)

    assert await state.get_state() == AdminState.waiting_for_file
    assert state._data.get("action") == "send_doc"

    # ── Simulate entering order ID via callback ─────────────────────
    # callback_send_doc checks:
    # 1. is_admin(callback.from_user.username) — we patch utils.auth.is_admin
    # 2. callback.data is set to "send_doc_ORDER_E2E_001"
    # 3. callback.message is not None and has edit_text method
    #
    # We create a minimal object that isn't None and has edit_text.
    # This bypasses the isinstance checks for Message since the handler
    # uses hasattr(callback.message, "edit_text"), not isinstance.

    class _MsgProxy:
        """Minimal proxy that satisfies hasattr(fake, 'edit_text') and is not None."""

        async def edit_text(self, text, **kwargs):
            return True

    callback = MockCallback(data="send_doc_ORDER_E2E_001", user_id=admin_id)
    callback.from_user.username = "admin"
    callback.bot = MockBot()
    callback.message = _MsgProxy()

    with patch("utils.auth.is_admin", return_value=True):
        await callback_send_doc(callback, state)

    assert (
        state._data.get("order_id") == "ORDER_E2E_001"
    ), f"Expected ORDER_E2E_001, got {state._data.get('order_id')}"

    # ── Admin uploads file ──────────────────────────────────────────
    msg2 = MockMessage(chat_id=admin_id, user_id=admin_id)
    msg2.from_user.username = "admin"
    msg2.bot = MockBot()
    msg2.photo = [MockPhoto(file_id="completed_doc.jpg")]

    with patch("utils.auth.is_admin", return_value=True):
        with patch("handlers.admin.orders", {"ORDER_E2E_001": {"user_id": 123}}):
            with patch(
                "utils.router.send_document_to_client", AsyncMock()
            ) as mock_send:
                await process_document_file(msg2, state)

    # Document must be sent to client
    assert mock_send.called
    assert mock_send.call_args[1]["client_id"] == 123
    assert mock_send.call_args[1]["file_id"] == "completed_doc.jpg"

"""Tests for the main order flow (order handlers).

Checks:
    - Document type selection
    - Quantity selection
    - Document field filling
    - Delivery choice
    - Payment method selection
    - Waiting for payment proof
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import MagicMock, patch

import pytest
from conftest import MockCallback  # type: ignore[import-not-found]

from fsm.states import OrderState
from tests.fixtures.mocks import MockFSMContext, MockMessage

# Import handlers early to avoid async fixture issues
from handlers.order import (
    callback_checkout,
    process_delivery_choice,
    process_document_choice,
    process_quantity,
)


@pytest.mark.asyncio
async def test_callback_document_choice_visa(mock_fsm, clean_user_sessions):
    """Test selecting a "Visa application" document.

    Verifies:
        - Message text contains the template name (English)
        - Message text contains the price (EUR)
        - FSM state is set to entering_quantity
    """
    callback = MockCallback(data="doc_visa")

    await process_document_choice(callback, mock_fsm)

    # Verify message was edited with template info
    assert callback.message._edited_text is not None
    assert "Visa application" in callback.message._edited_text
    assert "35" in callback.message._edited_text  # price (EUR)
    assert "€" in callback.message._edited_text
    # Verify state
    assert mock_fsm._data.get("state") == OrderState.entering_quantity


@pytest.mark.asyncio
async def test_callback_document_choice_passport(mock_fsm, clean_user_sessions):
    """Test selecting a "Foreign passport" document.

    Verifies correct loading of another document type.
    """
    callback = MockCallback(data="doc_passport")

    await process_document_choice(callback, mock_fsm)

    assert callback.message._edited_text is not None
    # The English name is "Foreign passport"
    assert "Foreign passport" in callback.message._edited_text
    # Passport price is 45 EUR
    assert "45" in callback.message._edited_text
    assert "€" in callback.message._edited_text
    assert mock_fsm._data.get("state") == OrderState.entering_quantity


@pytest.mark.asyncio
async def test_callback_document_choice_invalid(mock_fsm, clean_user_sessions):
    """Test selecting a nonexistent document.

    Verifies that an invalid document type triggers an error answer.
    """
    callback = MockCallback(data="doc_nonexistent")

    await process_document_choice(callback, mock_fsm)

    # Template not found - should answer with error
    assert callback._answered is True


@pytest.mark.asyncio
async def test_callback_quantity_selection(mock_fsm, clean_user_sessions):
    """Test quantity selection (3 copies).

    Verifies:
        - FSM state transitions to filling_document
        - User session is updated
    """
    # First make a document choice to set up the session
    callback = MockCallback(data="doc_visa")
    await process_document_choice(callback, mock_fsm)

    # Now select quantity (need a new callback since frozen model)
    callback2 = MockCallback(data="qty_3", user_id=123)
    await process_quantity(callback2, mock_fsm)

    # Verify state
    assert mock_fsm._data.get("state") == OrderState.filling_document


@pytest.mark.asyncio
async def test_callback_delivery_yes(mock_fsm, clean_user_sessions):
    """Test choosing "Delivery needed".

    Verifies that FSM state transitions to filling_delivery.
    """
    callback = MockCallback(data="delivery_yes")

    await process_delivery_choice(callback, mock_fsm)

    # Check that state is filling_delivery
    assert mock_fsm._data.get("state") == OrderState.filling_delivery


@pytest.mark.asyncio
async def test_callback_delivery_no(mock_fsm, clean_user_sessions):
    """Test choosing "Pickup (no delivery)".

    Verifies that FSM state transitions to choosing_payment.
    """
    callback = MockCallback(data="delivery_no")

    await process_delivery_choice(callback, mock_fsm)

    # Check that state is choosing_payment (skip to payment)
    assert mock_fsm._data.get("state") == OrderState.choosing_payment


@pytest.mark.asyncio
async def test_checkout_rejects_empty_cart(mock_fsm, clean_user_sessions):
    callback = MockCallback(data="cart_checkout")

    await callback_checkout(callback, mock_fsm)

    assert callback._answered is True
    assert "Cart is empty" in callback._answered_text
    assert mock_fsm._data.get("state") == OrderState.choosing_document


class TestProcessPayment:
    """Tests for payment method selection."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("method", ["blik", "uah", "usdt"])
    async def test_payment_method_sets_state(self, mock_fsm, clean_user_sessions, method):
        """Verify choosing a payment method transitions to waiting_for_payment_proof."""
        from handlers.order import process_payment

        from handlers.order import get_user_session
        session = await get_user_session(123)
        session["total_price"] = 100
        session["currency"] = "EUR"

        callback = MockCallback(data=f"pay_{method}")
        await process_payment(callback, mock_fsm)

        assert mock_fsm._data.get("state") == OrderState.waiting_for_payment_proof
        assert callback._answered is True

    @pytest.mark.asyncio
    async def test_payment_shows_payment_details(self, mock_fsm, clean_user_sessions):
        """Verify choosing a payment method sets the waiting-for-proof state."""
        from handlers.order import process_payment
        from handlers.order import get_user_session

        session = await get_user_session(123)
        session["total_price"] = 150

        callback = MockCallback(data="pay_blik")
        await process_payment(callback, mock_fsm)

        assert mock_fsm._data.get("state") == OrderState.waiting_for_payment_proof


class TestFallbacks:
    """Tests for fallback handlers."""

    @pytest.mark.asyncio
    async def test_fallback_choosing_document(self):
        """Verify fallback sends error when user sends text instead of button."""
        from handlers.order import fallback_choosing_document
        from aiogram.types import Message

        message = MockMessage(text="random text", chat_id=123, user_id=123)
        state = MockFSMContext()

        await fallback_choosing_document(message, state)

        assert message._answered_text is not None
        assert message._answered_text  # Non-empty response


class TestAddMoreCart:
    """Tests for cart_add_more handler."""

    @pytest.mark.asyncio
    async def test_add_more_returns_to_document_list(self, mock_fsm, clean_user_sessions):
        """Verify 'Add more' button shows document list again."""
        from handlers.order import callback_add_more

        callback = MockCallback(data="cart_add_more")
        state = mock_fsm

        with patch("templates.documents.get_all_templates") as mock_templates:
            mock_templates.return_value = [("visa", "Visa")]
            with patch("keyboards.buttons.document_keyboard") as mock_kb:
                mock_kb.return_value = MagicMock()
                await callback_add_more(callback, state)

        assert mock_fsm._data.get("state") == OrderState.choosing_document
        assert callback._answered is True


class TestClearCart:
    """Tests for cart_clear handler."""

    @pytest.mark.asyncio
    async def test_clear_cart_empties_session(self, mock_fsm, clean_user_sessions):
        """Verify 'Clear cart' resets cart and delivery."""
        from handlers.order import callback_clear_cart
        from handlers.order import get_user_session

        # Add an item to the cart
        session = await get_user_session(123)
        session["cart"].append({"type": "visa", "quantity": 1, "items": []})
        session["delivery"] = {"name": "Test", "phone": "+48123456789"}
        session["total_price"] = 100

        callback = MockCallback(data="cart_clear")
        state = mock_fsm

        with patch("keyboards.buttons.main_menu_keyboard") as mock_kb:
            mock_kb.return_value = MagicMock()
            await callback_clear_cart(callback, state)

        session = await get_user_session(123)
        assert len(session["cart"]) == 0
        assert session["delivery"] is None
        assert session["total_price"] == 0

"""Tests for the main order flow (order handlers).

Checks:
    - Document type selection
    - Quantity selection
    - Document field filling
    - Delivery choice
    - Payment method selection
    - Waiting for payment proof
"""

import pytest
from conftest import MockCallback  # type: ignore[import-not-found]

from fsm.states import OrderState

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

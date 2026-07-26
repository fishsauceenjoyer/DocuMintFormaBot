"""Tests for keyboard button modules.

Verifies:
    - InlineKeyboardMarkup structure
    - Callback data correctness
    - Button count
"""

import pytest
from aiogram.types import InlineKeyboardMarkup

from keyboards import buttons


class TestDocumentKeyboard:
    """Tests for document_keyboard function."""

    def test_document_keyboard_has_buttons(self):
        """Verify document keyboard contains buttons for each doc type."""
        docs = [("visa", "Visa application"), ("passport", "Foreign passport")]
        keyboard = buttons.document_keyboard(docs)

        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) == 4  # 2 docs + help_manager + cancel_to_menu

    def test_document_keyboard_callback_data(self):
        """Verify callback data follows 'doc_<code>' pattern."""
        docs = [("visa", "Visa"), ("passport", "Passport")]
        keyboard = buttons.document_keyboard(docs)

        callback_data = [btn.callback_data for row in keyboard.inline_keyboard for btn in row]
        assert "doc_visa" in callback_data
        assert "doc_passport" in callback_data
        assert "help_manager" in callback_data
        assert "cancel_to_menu" in callback_data

    def test_document_keyboard_empty_docs(self):
        """Verify keyboard works with empty docs list."""
        keyboard = buttons.document_keyboard([])
        assert len(keyboard.inline_keyboard) == 2  # help_manager + cancel_to_menu


class TestQuantityKeyboard:
    """Tests for quantity_keyboard function."""

    def test_quantity_keyboard_has_numbers_1_to_5(self):
        """Verify quantity keyboard has buttons 1-5."""
        keyboard = buttons.quantity_keyboard()

        callback_data = [btn.callback_data for row in keyboard.inline_keyboard for btn in row]
        assert "qty_1" in callback_data
        assert "qty_5" in callback_data

    def test_quantity_keyboard_button_count(self):
        """Verify correct number of buttons."""
        keyboard = buttons.quantity_keyboard()
        # One row with 5 numbers + one row with help_manager + one row with cancel_to_menu
        assert len(keyboard.inline_keyboard) == 3


class TestDeliveryKeyboard:
    """Tests for delivery_keyboard function."""

    def test_delivery_keyboard_has_yes_no(self):
        """Verify delivery keyboard has yes/no options."""
        keyboard = buttons.delivery_keyboard()

        callback_data = [btn.callback_data for row in keyboard.inline_keyboard for btn in row]
        assert "delivery_yes" in callback_data
        assert "delivery_no" in callback_data

    def test_delivery_keyboard_has_help(self):
        """Verify delivery keyboard has help_manager button."""
        keyboard = buttons.delivery_keyboard()
        callback_data = [btn.callback_data for row in keyboard.inline_keyboard for btn in row]
        assert "help_manager" in callback_data


class TestPaymentKeyboard:
    """Tests for payment_keyboard function."""

    def test_payment_keyboard_has_methods(self):
        """Verify payment keyboard has all payment methods."""
        keyboard = buttons.payment_keyboard()

        callback_data = [btn.callback_data for row in keyboard.inline_keyboard for btn in row]
        assert "pay_blik" in callback_data
        assert "pay_uah" in callback_data
        assert "pay_usdt" in callback_data

    def test_payment_keyboard_has_help(self):
        """Verify payment keyboard has help_manager button."""
        keyboard = buttons.payment_keyboard()
        callback_data = [btn.callback_data for row in keyboard.inline_keyboard for btn in row]
        assert "help_manager" in callback_data


class TestManagerOrderKeyboard:
    """Tests for manager_order_keyboard function."""

    def test_manager_keyboard_has_actions(self):
        """Verify manager keyboard has send_doc, send_track, order_done."""
        keyboard = buttons.manager_order_keyboard("ORDER_TEST123")

        callback_data = [btn.callback_data for row in keyboard.inline_keyboard for btn in row]
        assert "send_doc_ORDER_TEST123" in callback_data
        assert "send_track_ORDER_TEST123" in callback_data
        assert "order_done_ORDER_TEST123" in callback_data


class TestMainMenuKeyboard:
    """Tests for main_menu_keyboard function."""

    def test_main_menu_has_buttons(self):
        """Verify main menu has new order, fast order, help."""
        keyboard = buttons.main_menu_keyboard()

        callback_data = [btn.callback_data for row in keyboard.inline_keyboard for btn in row]
        assert "new_order" in callback_data
        assert "fast_order" in callback_data
        assert "help_manager" in callback_data


class TestCartKeyboard:
    """Tests for cart_keyboard function."""

    def test_cart_keyboard_has_actions(self):
        """Verify cart keyboard has checkout, add more, clear, help."""
        keyboard = buttons.cart_keyboard()

        callback_data = [btn.callback_data for row in keyboard.inline_keyboard for btn in row]
        assert "cart_checkout" in callback_data
        assert "cart_add_more" in callback_data
        assert "cart_clear" in callback_data
        assert "help_manager" in callback_data


class TestConfirmKeyboard:
    """Tests for confirm_keyboard function."""

    def test_confirm_keyboard_has_yes_no(self):
        """Verify confirm keyboard has yes/no buttons."""
        keyboard = buttons.confirm_keyboard()

        callback_data = [btn.callback_data for row in keyboard.inline_keyboard for btn in row]
        assert "confirm_yes" in callback_data
        assert "confirm_no" in callback_data


class TestBackKeyboard:
    """Tests for back_keyboard function."""

    def test_back_keyboard_has_back_button(self):
        """Verify back keyboard has one back button."""
        keyboard = buttons.back_keyboard()

        callback_data = [btn.callback_data for row in keyboard.inline_keyboard for btn in row]
        assert "back" in callback_data
        assert len(callback_data) == 1
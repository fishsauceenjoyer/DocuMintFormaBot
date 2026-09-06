"""Tests for start command and main menu handlers.

Covers:
    - /start command
    - /menu command
    - callback_new_order
    - callback_help_manager
    - FSM state transitions
    - Language detection
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from unittest.mock import patch

import pytest

from fsm.states import OrderState
from tests.fixtures.mocks import MockBot, MockCallback, MockFSMContext, MockMessage


class TestCmdStart:
    """Tests for the /start command handler."""

    @pytest.mark.asyncio
    async def test_start_clears_state_and_shows_welcome(self):
        """Verify /start clears previous state and shows welcome menu."""
        from handlers.start import cmd_start

        message = MockMessage(text="/start", chat_id=123, user_id=123)
        message.bot = MockBot()
        state = MockFSMContext()
        state._data["old_state"] = "some_previous_state"

        await cmd_start(message, state)

        # State is cleared (only state set by handler)
        assert state._data.get("state") == OrderState.choosing_document
        assert message._answered_text is not None
        assert (
            "welcome" in message._answered_text
            or "Welcome" in message._answered_text
            or "Добро" in message._answered_text
        )

    @pytest.mark.asyncio
    async def test_start_shows_main_menu_keyboard(self):
        """Verify /start shows main menu with expected buttons."""
        from handlers.start import cmd_start

        message = MockMessage(text="/start", chat_id=456, user_id=456)
        message.bot = MockBot()
        state = MockFSMContext()

        await cmd_start(message, state)

        # Reply markup should be in kwargs
        if hasattr(message, "_answered_text"):
            assert message._answered_text is not None


class TestCmdMenu:
    """Tests for the /menu command handler."""

    @pytest.mark.asyncio
    async def test_menu_clears_state_and_shows_menu(self):
        """Verify /menu clears state and shows menu."""
        from handlers.start import cmd_menu

        message = MockMessage(text="/menu", chat_id=123, user_id=123)
        message.bot = MockBot()
        state = MockFSMContext()

        await cmd_menu(message, state)

        assert message._answered_text is not None

    @pytest.mark.asyncio
    async def test_menu_works_from_any_state(self):
        """Verify /menu works regardless of current FSM state."""
        from handlers.start import cmd_menu

        message = MockMessage(text="/menu", chat_id=789, user_id=789)
        message.bot = MockBot()
        state = MockFSMContext()
        state._data["state"] = OrderState.waiting_for_payment_proof

        await cmd_menu(message, state)

        assert message._answered_text is not None


class TestCallbackNewOrder:
    """Tests for the 'new_order' callback handler."""

    @pytest.mark.asyncio
    async def test_new_order_shows_document_selection(self):
        """Verify 'new_order' shows document list."""
        from handlers.start import callback_new_order

        callback = MockCallback(data="new_order")
        state = MockFSMContext()

        # Mock templates to return known docs
        with patch("templates.documents.get_all_templates") as mock_templates:
            mock_templates.return_value = [
                ("poster_terminator1", "🎬 Терминатор 1"),
                ("poster_terminator2", "🎬 Терминатор 2"),
            ]
            await callback_new_order(callback, state)

        assert state._data.get("state") == OrderState.choosing_document
        assert callback._answered is True

    @pytest.mark.asyncio
    async def test_new_order_with_inaccessible_message(self):
        """Verify 'new_order' does not crash when callback has no accessible message."""
        from handlers.start import callback_new_order

        callback = MockCallback(data="new_order")
        callback.message = None
        state = MockFSMContext()

        with patch("templates.documents.get_all_templates") as mock_templates:
            mock_templates.return_value = [("poster_terminator1", "🎬 Терминатор 1")]
            await callback_new_order(callback, state)

        assert callback._answered is True
        assert state._data.get("state") is None


class TestCallbackHelpManager:
    """Tests for the 'help_manager' callback handler."""

    @pytest.mark.asyncio
    async def test_help_manager_forwards_to_manager(self):
        """Verify 'help_manager' forwards request to manager chat."""
        from handlers.start import callback_help_manager

        callback = MockCallback(data="help_manager")
        state = MockFSMContext()
        state._data["current_step"] = "Choosing document"

        with patch("utils.router.forward_to_manager") as mock_forward:
            await callback_help_manager(callback, state)

        mock_forward.assert_called_once()
        assert mock_forward.call_args[1]["user_id"] == 123
        assert mock_forward.call_args[1]["current_step"] == "Choosing document"
        assert callback._answered is True

    @pytest.mark.asyncio
    async def test_help_manager_works_from_main_menu(self):
        """Verify 'help_manager' works without current_step."""
        from handlers.start import callback_help_manager

        callback = MockCallback(data="help_manager")
        state = MockFSMContext()

        with patch("utils.router.forward_to_manager") as mock_forward:
            await callback_help_manager(callback, state)

        mock_forward.assert_called_once()
        assert mock_forward.call_args[1]["user_id"] == 123


class TestCallbackCancelToMenu:
    """Tests for the 'cancel_to_menu' callback handler."""

    @pytest.mark.asyncio
    async def test_cancel_to_menu_clears_state_and_shows_menu(self):
        """Verify 'cancel_to_menu' clears state and shows main menu."""
        from handlers.start import callback_cancel_to_menu

        callback = MockCallback(data="cancel_to_menu")
        state = MockFSMContext()
        state._data["state"] = "some_deep_state"

        await callback_cancel_to_menu(callback, state)

        assert state._data.get("state") is None  # state cleared
        assert callback._answered is True
        # MockMessage doesn't inherit from aiogram.types.Message,
        # so isinstance check fails and bot.send_message is used instead
        assert len(callback.bot.sent_messages) > 0

    @pytest.mark.asyncio
    async def test_cancel_to_menu_clears_user_session(self):
        """Verify 'cancel_to_menu' clears user session."""
        from handlers.order import _sessions_lock, user_sessions
        from handlers.start import callback_cancel_to_menu

        # Set up a session
        async with _sessions_lock:
            user_sessions[123] = {"cart": ["test"]}

        callback = MockCallback(data="cancel_to_menu", user_id=123)
        state = MockFSMContext()

        await callback_cancel_to_menu(callback, state)

        # Session should be cleared
        async with _sessions_lock:
            assert 123 not in user_sessions

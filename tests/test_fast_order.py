"""Tests for fast-order handlers with mocked Telegram API.

Uses mock objects instead of the real Telegram API to test callback
and message handling logic without a live bot connection.
"""

import datetime
import os
import sys
from unittest.mock import patch

import pytest
from aiogram.types import Chat, InaccessibleMessage, Message, User

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fsm.states import OrderState  # noqa: E402


class MockBot:
    """Mock bot that stores sent messages locally for assertions."""

    _mock_message_sent: dict | None = None

    def __init__(self):
        pass

    async def send_message(self, chat_id, text, **kwargs):
        """Simulate sending a message, storing parameters locally."""
        self._mock_message_sent = {"chat_id": chat_id, "text": text, "kwargs": kwargs}
        return Message(
            message_id=123,
            date=datetime.datetime.now(),
            chat=Chat(id=chat_id, type="private"),
            from_user=User(id=chat_id, is_bot=False, first_name="Test"),
        )


class MockMessage:
    """Mock Message that stores edited / answered text for verification."""

    text: str | None
    message_id: int
    _edited_text: str | None = None
    _answered_text: str | None = None

    def __init__(self, text=None, message_id=1, chat_id=123):
        self.text = text
        self.message_id = message_id
        self.chat = Chat(id=chat_id, type="private")
        self.from_user = User(
            id=chat_id, is_bot=False, first_name="Test", username="testuser"
        )
        self.bot = MockBot()

    async def edit_text(self, text, **kwargs):
        """Simulate editing the message text."""
        self._edited_text = text
        return True

    async def answer(self, text, **kwargs):
        """Simulate answering the message."""
        self._answered_text = text
        return True


class MockCallback:
    """Mock callback query with configurable message accessibility."""

    def __init__(self, message_accessible=True):
        self.from_user = User(
            id=123, is_bot=False, first_name="Test", username="testuser"
        )

        if message_accessible:
            self.message = MockMessage()
        else:
            self.message = InaccessibleMessage(
                message_id=1, date=0, chat=Chat(id=123, type="private")
            )

        self.bot = MockBot()

    async def answer(self, text=None, show_alert=None):
        """Simulate answering the callback."""
        self._answered = True
        return True


class MockFSMContext:
    """Mock FSM context that stores state and data in memory."""

    def __init__(self):
        self._data = {}

    async def set_state(self, state):
        self._data["state"] = state

    async def update_data(self, **kwargs):
        self._data.update(kwargs)

    async def clear(self):
        self._data.clear()

    async def get_state(self):
        return self._data.get("state")

    async def get_data(self):
        return self._data.copy()


@pytest.mark.asyncio
async def test_callback_fast_order_accessible_message():
    """Test fast-order callback with an accessible message.

    Verifies the message is edited, contains the welcome text
    (in English, since test user has no language code → default en),
    and the FSM transitions to fast_order_waiting.
    """
    callback = MockCallback(message_accessible=True)
    state = MockFSMContext()

    from handlers.fast_order import callback_fast_order

    await callback_fast_order(callback, state)

    assert isinstance(callback.message, MockMessage)
    assert hasattr(callback.message, "_edited_text")
    assert callback.message._edited_text is not None
    assert "regular customer" in callback.message._edited_text
    assert state._data.get("state") == OrderState.fast_order_waiting


@pytest.mark.asyncio
async def test_callback_fast_order_inaccessible_message():
    """Test fast-order callback with an inaccessible message.

    Verifies the welcome text is sent via bot.send_message
    and the FSM transitions to fast_order_waiting.
    """
    callback = MockCallback(message_accessible=False)
    state = MockFSMContext()

    from handlers.fast_order import callback_fast_order

    await callback_fast_order(callback, state)

    assert callback.bot._mock_message_sent is not None
    assert "regular customer" in callback.bot._mock_message_sent["text"]
    assert state._data.get("state") == OrderState.fast_order_waiting


@pytest.mark.asyncio
async def test_process_fast_order():
    """Test processing a fast-order message.

    Verifies the message is forwarded to the manager with
    "FAST ORDER" header and includes the user's text.
    """
    message = MockMessage(text="Test order: passport", chat_id=123)
    state = MockFSMContext()
    state._data["state"] = OrderState.fast_order_waiting

    from handlers.fast_order import process_fast_order

    with patch("handlers.fast_order.ROUTING", {"default": 555555555}):
        await process_fast_order(message, state)

    assert message.bot._mock_message_sent is not None
    assert "FAST ORDER" in message.bot._mock_message_sent["text"]
    assert "Test order: passport" in message.bot._mock_message_sent["text"]

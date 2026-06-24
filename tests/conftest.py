"""Shared pytest fixtures and Telegram test doubles.

The mocks mimic the aiogram objects used by handlers and record sent/edited
messages locally, so unit tests can exercise FSM logic without Telegram API
network calls.
"""

import datetime
from typing import Any, Dict, Optional

import pytest
from aiogram.types import CallbackQuery, Chat, InaccessibleMessage, Message, User


class MockBot:
    """Мок-объект бота для тестирования."""

    def __init__(self):
        self._mock_message_sent: Optional[dict] = None
        self._mock_photo_sent: Optional[dict] = None
        self._mock_document_sent: Optional[dict] = None
        self.id = 12345  # Bot ID

    async def send_message(self, chat_id, text, **kwargs):
        self._mock_message_sent = {"chat_id": chat_id, "text": text, "kwargs": kwargs}
        return Message(
            message_id=123,
            date=datetime.datetime.now(),
            chat=Chat(id=chat_id, type="private"),
            from_user=User(id=chat_id, is_bot=False, first_name="Test"),
        )

    async def send_photo(self, chat_id, photo, caption=None, **kwargs):
        self._mock_photo_sent = {
            "chat_id": chat_id,
            "photo": photo,
            "caption": caption,
            "kwargs": kwargs,
        }
        return True

    async def send_document(self, chat_id, document, caption=None, **kwargs):
        self._mock_document_sent = {
            "chat_id": chat_id,
            "document": document,
            "caption": caption,
            "kwargs": kwargs,
        }
        return True


class MockMessage(Message):
    """Мок-объект сообщения для тестирования, наследующий от aiogram.types.Message."""

    def __init__(self, text=None, message_id=1, chat_id=123, user_id=123):
        # Create minimal required params for Message
        chat = Chat(id=chat_id, type="private")
        from_user = User(
            id=user_id, is_bot=False, first_name="Test", username="testuser"
        )
        date = datetime.datetime.now()
        # Call parent init with required fields FIRST
        super().__init__(
            message_id=message_id,
            date=date,
            chat=chat,
            from_user=from_user,
            text=text,
        )
        self._edited_text: Optional[str] = None
        self._answered_text: Optional[str] = None

    async def edit_text(self, text, **kwargs):
        """Store edited text locally instead of calling Telegram API."""
        self._edited_text = text
        return True

    async def answer(self, text, **kwargs):
        self._answered_text = text
        return True


class MockCallback(CallbackQuery):
    """CallbackQuery test double that stores callback answers locally."""

    def __init__(self, data=None, message_accessible=True, user_id=123):
        user = User(id=user_id, is_bot=False, first_name="Test", username="testuser")
        if message_accessible:
            msg = MockMessage(chat_id=user_id)
        else:
            msg = InaccessibleMessage(
                message_id=1, date=0, chat=Chat(id=user_id, type="private")
            )

        # Call parent init with required fields
        super().__init__(
            id=f"callback_{user_id}_{datetime.datetime.now().timestamp()}",
            from_user=user,
            chat_instance=f"instance_{user_id}",
            message=msg,
            data=data,
        )
        self._answered: bool = False
        self._answered_text: Optional[str] = None
        self._show_alert: Optional[bool] = None

    async def answer(self, text=None, show_alert=None):
        self._answered = True
        self._answered_text = text
        self._show_alert = show_alert
        return True


class MockFSMContext:
    """Мок-объект контекста FSM для тестирования."""

    def __init__(self):
        self._data: Dict[str, Any] = {}

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


@pytest.fixture
def mock_bot():
    """Фикстура: мок-объект бота."""
    return MockBot()


@pytest.fixture
def mock_fsm():
    """Фикстура: мок-объект FSM контекста."""
    return MockFSMContext()


@pytest.fixture
def mock_callback():
    """Фикстура: мок-объект callback с доступным сообщением."""
    return MockCallback(data="doc_visa", message_accessible=True)


@pytest.fixture
def clean_user_sessions():
    """Фикстура: очищает глобальное хранилище сессий между тестами."""
    from handlers.order import user_sessions

    user_sessions.clear()
    yield
    user_sessions.clear()

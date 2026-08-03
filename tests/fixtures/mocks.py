"""Reusable mock objects for Telegram bot tests.

Duck-typed replacements for aiogram objects. They do NOT inherit from
aiogram Pydantic models (which are frozen), so they can be mutated freely
in tests.
"""

import datetime
from typing import Any, Dict, List, Optional


class MockBot:
    """Mock bot that records sent messages locally for assertions."""

    def __init__(self):
        self.sent_messages: list[dict] = []
        self.sent_photos: list[dict] = []
        self.sent_documents: list[dict] = []
        self.id = 12345

    async def send_message(self, chat_id, text, **kwargs):
        self.sent_messages.append(
            {
                "chat_id": chat_id,
                "text": text,
                "kwargs": kwargs,
            }
        )
        return None

    async def send_photo(self, chat_id, photo, caption=None, **kwargs):
        self.sent_photos.append(
            {
                "chat_id": chat_id,
                "photo": photo,
                "caption": caption,
                "kwargs": kwargs,
            }
        )
        return True

    async def send_document(self, chat_id, document, caption=None, **kwargs):
        self.sent_documents.append(
            {
                "chat_id": chat_id,
                "document": document,
                "caption": caption,
                "kwargs": kwargs,
            }
        )
        return True


class FailingBot:
    """Bot that simulates Telegram API failures."""

    async def send_message(self, *args, **kwargs):
        raise RuntimeError("telegram unavailable")

    async def send_photo(self, *args, **kwargs):
        raise RuntimeError("telegram unavailable")

    async def send_document(self, *args, **kwargs):
        raise RuntimeError("telegram unavailable")


class MockMessage:
    """Mock Message using duck typing."""

    def __init__(self, text=None, message_id=1, chat_id=123, user_id=123):
        self.text = text
        self.message_id = message_id
        self.chat = MockChat(chat_id=chat_id)
        self.from_user = MockUser(user_id=user_id)
        self.bot: Any = MockBot()
        self.photo: Optional[List[Any]] = None
        self.document: Optional[Any] = None
        self._edited_text: Optional[str] = None
        self._answered_text: Optional[str] = None

    async def edit_text(self, text, **kwargs):
        self._edited_text = text
        return True

    async def answer(self, text, **kwargs):
        self._answered_text = text
        return True


class MockCallback:
    """CallbackQuery test double using duck typing."""

    def __init__(self, data=None, message_accessible=True, user_id=123):
        self.from_user = MockUser(user_id=user_id)
        self.chat_instance = f"instance_{user_id}"
        self.data = data
        self.message: Any = (
            MockMessage(chat_id=user_id)
            if message_accessible
            else MockInaccessibleMessage()
        )
        self.bot: Any = MockBot()
        self._answered: bool = False
        self._answered_text: Optional[str] = None
        self._show_alert: Optional[bool] = None

    async def answer(self, text=None, show_alert=None):
        self._answered = True
        self._answered_text = text
        self._show_alert = show_alert
        return True


class MockFSMContext:
    """In-memory FSM context storage for testing."""

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


class MockUser:
    def __init__(self, user_id=123, username="testuser", language_code=None):
        self.id = user_id
        self.username: Optional[str] = username
        self.first_name = "Test"
        self.last_name = None
        self.language_code = language_code
        self.is_bot = False


class MockChat:
    def __init__(self, chat_id=123, type="private"):
        self.id = chat_id
        self.type = type
        self.title = None
        self.username = None
        self.first_name = None


class MockInaccessibleMessage:
    """Stub for InaccessibleMessage."""

    def __init__(self, message_id=1, date=0, chat=None):
        self.message_id = message_id
        self.date = date
        self.chat = chat or MockChat()
        self.from_user = None
        self.text = None

    async def edit_text(self, text, **kwargs):
        return None

    async def answer(self, text, **kwargs):
        return None


class MockPhoto:
    """Minimal stand-in for a Telegram PhotoSize object."""

    def __init__(self, file_id: str = "test_photo_file_id"):
        self.file_id = file_id
        self.file_unique_id = f"unique_{file_id}"

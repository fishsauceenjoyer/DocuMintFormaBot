"""Tests for middleware.

Covers:
    - RegistrationMiddleware: auto-registers new users
    - LoggingMiddleware: logs incoming messages and callbacks
"""

import os
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from aiogram.types import CallbackQuery, Message, User, Chat


class TestRegistrationMiddleware:
    """Tests for the RegistrationMiddleware class."""

    @pytest.mark.asyncio
    async def test_registers_new_user_on_message(self):
        """Verify a new user is created on first message."""
        from utils.middleware import RegistrationMiddleware

        message = Message(
            message_id=1,
            date=datetime.datetime.now(),
            chat=Chat(id=123, type="private"),
            from_user=User(id=123, is_bot=False, first_name="Test", username="newuser"),
            text="/start",
        )

        middleware = RegistrationMiddleware()
        mock_handler = AsyncMock()

        with patch("utils.middleware.get_user_by_username", return_value=None):
            with patch("utils.middleware.create_user") as mock_create_user:
                await middleware(mock_handler, message, {})

        mock_create_user.assert_called_once()
        assert mock_create_user.call_args[1]["username"] == "newuser"
        assert mock_create_user.call_args[1]["chat_id"] == 123
        mock_handler.assert_awaited_once_with(message, {})

    @pytest.mark.asyncio
    async def test_skips_registration_for_existing_user(self):
        """Verify existing user is not re-registered."""
        from utils.middleware import RegistrationMiddleware

        message = Message(
            message_id=1,
            date=datetime.datetime.now(),
            chat=Chat(id=123, type="private"),
            from_user=User(id=123, is_bot=False, first_name="Test", username="existinguser"),
            text="/start",
        )

        existing_user = MagicMock()
        existing_user.chat_id = 123

        middleware = RegistrationMiddleware()
        mock_handler = AsyncMock()

        with patch("utils.middleware.get_user_by_username", return_value=existing_user):
            with patch("utils.middleware.create_user") as mock_create_user:
                await middleware(mock_handler, message, {})

        mock_create_user.assert_not_called()
        mock_handler.assert_awaited_once_with(message, {})

    @pytest.mark.asyncio
    async def test_updates_chat_id_on_change(self):
        """Verify chat_id is updated if it changed."""
        from utils.middleware import RegistrationMiddleware

        message = Message(
            message_id=1,
            date=datetime.datetime.now(),
            chat=Chat(id=456, type="private"),
            from_user=User(id=456, is_bot=False, first_name="Test", username="existinguser"),
            text="/start",
        )

        existing_user = MagicMock()
        existing_user.chat_id = 123  # Old chat_id

        middleware = RegistrationMiddleware()
        mock_handler = AsyncMock()

        with patch("utils.middleware.get_user_by_username", return_value=existing_user):
            with patch("utils.middleware.create_user") as mock_create_user:
                await middleware(mock_handler, message, {})

        mock_create_user.assert_not_called()
        assert existing_user.chat_id == 456
        mock_handler.assert_awaited_once_with(message, {})

    @pytest.mark.asyncio
    async def test_handles_message_without_username(self):
        """Verify middleware handles user without username gracefully."""
        from utils.middleware import RegistrationMiddleware

        message = Message(
            message_id=1,
            date=datetime.datetime.now(),
            chat=Chat(id=123, type="private"),
            from_user=User(id=123, is_bot=False, first_name="Test", username=None),
            text="/start",
        )

        middleware = RegistrationMiddleware()
        mock_handler = AsyncMock()

        with patch("utils.middleware.get_user_by_username") as mock_get:
            with patch("utils.middleware.create_user") as mock_create:
                await middleware(mock_handler, message, {})

        mock_get.assert_not_called()  # Should skip DB check
        mock_create.assert_not_called()
        mock_handler.assert_awaited_once_with(message, {})


class TestLoggingMiddleware:
    """Tests for the LoggingMiddleware class."""

    @pytest.mark.asyncio
    async def test_logs_message_event(self):
        """Verify logging middleware logs text messages."""
        from utils.middleware import LoggingMiddleware

        message = Message(
            message_id=1,
            date=datetime.datetime.now(),
            chat=Chat(id=123, type="private"),
            from_user=User(id=123, is_bot=False, first_name="Test", username="testuser"),
            text="Hello bot",
        )

        middleware = LoggingMiddleware()
        mock_handler = AsyncMock()

        with patch("utils.middleware.logger") as mock_logger:
            await middleware(mock_handler, message, {})

        mock_logger.info.assert_called()
        mock_handler.assert_awaited_once_with(message, {})

    @pytest.mark.asyncio
    async def test_logs_callback_event(self):
        """Verify logging middleware logs callback queries."""
        from utils.middleware import LoggingMiddleware

        user = User(id=123, is_bot=False, first_name="Test", username="testuser")
        chat = Chat(id=123, type="private")
        callback = CallbackQuery(
            id="cb_123",
            from_user=user,
            chat_instance="inst_123",
            data="doc_visa",
        )

        middleware = LoggingMiddleware()
        mock_handler = AsyncMock()

        with patch("utils.middleware.logger") as mock_logger:
            await middleware(mock_handler, callback, {})

        mock_logger.info.assert_called()
        mock_handler.assert_awaited_once_with(callback, {})

    @pytest.mark.asyncio
    async def test_logs_error_and_re_raises(self):
        """Verify logging middleware logs exceptions and re-raises."""
        from utils.middleware import LoggingMiddleware

        message = Message(
            message_id=1,
            date=datetime.datetime.now(),
            chat=Chat(id=123, type="private"),
            from_user=User(id=123, is_bot=False, first_name="Test", username="testuser"),
            text="Hello",
        )

        middleware = LoggingMiddleware()
        mock_handler = AsyncMock(side_effect=ValueError("test error"))

        with patch("utils.middleware.logger") as mock_logger:
            with pytest.raises(ValueError, match="test error"):
                await middleware(mock_handler, message, {})

        mock_logger.error.assert_called_once()
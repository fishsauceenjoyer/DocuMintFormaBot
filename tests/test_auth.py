"""Tests for authentication and authorisation module.

Covers:
    - is_admin function
    - get_admin_username function
    - admin_only decorator
    - Edge cases: None username, case insensitivity
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.fixtures.mocks import MockMessage, MockBot


class TestIsAdmin:
    """Tests for the is_admin function."""

    def test_admin_username_matches(self):
        """Verify is_admin returns True for matching admin username."""
        from utils.auth import is_admin
        with patch("utils.auth.ADMIN_USERNAME", "admin"):
            assert is_admin("admin") is True

    def test_admin_username_case_insensitive(self):
        """Verify is_admin is case-insensitive."""
        from utils.auth import is_admin
        with patch("utils.auth.ADMIN_USERNAME", "Admin"):
            assert is_admin("admin") is True
            assert is_admin("ADMIN") is True
            assert is_admin("Admin") is True

    def test_non_admin_username(self):
        """Verify is_admin returns False for non-admin."""
        from utils.auth import is_admin
        with patch("utils.auth.ADMIN_USERNAME", "admin"):
            assert is_admin("attacker") is False

    def test_none_username(self):
        """Verify is_admin returns False for None username."""
        from utils.auth import is_admin
        with patch("utils.auth.ADMIN_USERNAME", "admin"):
            assert is_admin(None) is False

    def test_none_admin_username_config(self):
        """Verify is_admin returns False when ADMIN_USERNAME is None."""
        from utils.auth import is_admin
        with patch("utils.auth.ADMIN_USERNAME", None):
            assert is_admin("admin") is False

    def test_empty_username(self):
        """Verify is_admin returns False for empty username."""
        from utils.auth import is_admin
        with patch("utils.auth.ADMIN_USERNAME", "admin"):
            assert is_admin("") is False


class TestGetAdminUsername:
    """Tests for the get_admin_username function."""

    def test_returns_admin_username(self):
        """Verify get_admin_username returns configured username."""
        from utils.auth import get_admin_username
        with patch("utils.auth.ADMIN_USERNAME", "admin"):
            assert get_admin_username() == "admin"

    def test_returns_none_when_not_configured(self):
        """Verify get_admin_username returns None when not set."""
        from utils.auth import get_admin_username
        with patch("utils.auth.ADMIN_USERNAME", None):
            assert get_admin_username() is None


class TestAdminOnlyDecorator:
    """Tests for the admin_only decorator."""

    @pytest.mark.asyncio
    async def test_admin_user_passes_through(self):
        """Verify admin user can execute the decorated function."""
        from utils.auth import admin_only
        message = MockMessage(text="/send_doc", chat_id=999, user_id=999)
        message.from_user.username = "admin"
        message.bot = MockBot()

        async_handler = AsyncMock()
        wrapped = admin_only(async_handler)

        with patch("utils.auth.ADMIN_USERNAME", "admin"):
            with patch("utils.auth.is_admin", return_value=True):
                await wrapped(message)

        async_handler.assert_awaited_once_with(message)

    @pytest.mark.asyncio
    async def test_non_admin_user_rejected(self):
        """Verify non-admin user gets rejection message."""
        from utils.auth import admin_only
        message = MockMessage(text="/send_doc", chat_id=123, user_id=123)
        message.from_user.username = "attacker"
        message.bot = MockBot()

        mock_handler = MagicMock()
        wrapped = admin_only(mock_handler)

        with patch("utils.auth.is_admin", return_value=False):
            await wrapped(message)

        mock_handler.assert_not_called()
        assert message._answered_text is not None
        assert "нет прав" in message._answered_text.lower()

    @pytest.mark.asyncio
    async def test_no_user_info(self):
        """Verify decorator handles missing user info."""
        from utils.auth import admin_only
        message = MockMessage(text="/send_doc", chat_id=123, user_id=123)
        # Simulate missing user by setting username to None
        message.from_user.username = None

        mock_handler = MagicMock()
        wrapped = admin_only(mock_handler)

        with patch("utils.auth.ADMIN_USERNAME", "admin"):
            with patch("utils.auth.is_admin", return_value=False):
                await wrapped(message)

        mock_handler.assert_not_called()
        assert message._answered_text is not None

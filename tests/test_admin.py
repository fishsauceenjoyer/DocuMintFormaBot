"""Tests for admin/manager command handlers.

Covers:
    - /send_doc command and callback
    - /track command and callback
    - /orders list command
    - /stats command
    - /help_admin command
    - order_done callback
    - Admin-only access control
    - FSM transitions for file upload and tracking number
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import MagicMock, patch

import pytest

from fsm.states import AdminState
from tests.fixtures.mocks import (
    MockBot,
    MockCallback,
    MockFSMContext,
    MockMessage,
    MockPhoto,
)

# ── Helper: admin message ──────────────────────────────────────────────


def _admin_message(text: str | None = None, chat_id: int = 999) -> MockMessage:
    """Create a MockMessage with admin username."""
    msg = MockMessage(text=text, chat_id=chat_id, user_id=chat_id)
    msg.from_user.username = "admin"
    msg.bot = MockBot()
    return msg


def _non_admin_message(text: str, chat_id: int = 123) -> MockMessage:
    """Create a MockMessage with non-admin username."""
    msg = MockMessage(text=text, chat_id=chat_id, user_id=chat_id)
    msg.from_user.username = "attacker"
    msg.bot = MockBot()
    return msg


# ── /send_doc command ──────────────────────────────────────────────────


class TestCmdSendDoc:
    """Tests for the /send_doc command handler."""

    @pytest.mark.asyncio
    async def test_admin_can_start_send_doc(self):
        """Verify admin receives instruction and FSM state is set."""
        from handlers.admin import cmd_send_doc

        message = _admin_message("/send_doc")
        state = MockFSMContext()

        with patch("utils.auth.ADMIN_USERNAME", "admin"):
            with patch("utils.auth.is_admin", return_value=True):
                await cmd_send_doc(message, state)

        assert state._data.get("state") == AdminState.waiting_for_file
        assert state._data.get("action") == "send_doc"
        assert message._answered_text is not None
        assert "Отправить документ" in message._answered_text

    @pytest.mark.asyncio
    async def test_non_admin_rejected_from_send_doc(self):
        """Verify non-admin gets rejected."""
        from handlers.admin import cmd_send_doc

        message = _non_admin_message("/send_doc")
        state = MockFSMContext()

        with patch("utils.auth.ADMIN_USERNAME", "admin"):
            with patch("utils.auth.is_admin", return_value=False):
                await cmd_send_doc(message, state)

        assert state._data.get("state") is None
        assert "нет прав" in (message._answered_text or "").lower()


# ── callback_send_doc ──────────────────────────────────────────────────


class TestCallbackSendDoc:
    """Tests for the 'send_doc_ORDER' callback handler."""

    @pytest.mark.asyncio
    async def test_callback_send_doc_sets_state(self):
        """Verify callback sets FSM state and stores order_id."""
        from handlers.admin import callback_send_doc

        callback = MockCallback(data="send_doc_ORDER_TEST123")
        callback.from_user.username = "admin"
        state = MockFSMContext()

        with patch("utils.auth.ADMIN_USERNAME", "admin"):
            with patch("utils.auth.is_admin", return_value=True):
                await callback_send_doc(callback, state)

        assert state._data.get("state") == AdminState.waiting_for_file
        assert state._data.get("order_id") == "ORDER_TEST123"
        assert state._data.get("action") == "send_doc"

    @pytest.mark.asyncio
    async def test_callback_send_doc_rejects_non_admin(self):
        """Verify non-admin gets alert."""
        from handlers.admin import callback_send_doc

        callback = MockCallback(data="send_doc_ORDER_TEST123")
        callback.from_user.username = "attacker"
        state = MockFSMContext()

        with patch("utils.auth.ADMIN_USERNAME", "admin"):
            with patch("utils.auth.is_admin", return_value=False):
                await callback_send_doc(callback, state)

        assert callback._answered is True
        assert "нет прав" in (callback._answered_text or "").lower()


# ── process_document_file ──────────────────────────────────────────────


class TestProcessDocumentFile:
    """Tests for uploading a document file as admin."""

    @pytest.mark.asyncio
    async def test_process_photo_file(self):
        """Verify admin can upload a photo as document."""
        from handlers.admin import process_document_file

        message = _admin_message(None)
        message.photo = [MockPhoto(file_id="photo_file_id")]
        state = MockFSMContext()
        state._data["order_id"] = "ORDER_TEST123"
        state._data["action"] = "send_doc"

        with patch("handlers.admin.orders", {"ORDER_TEST123": {"user_id": 123}}):
            with patch("utils.router.send_document_to_client") as mock_send:
                await process_document_file(message, state)

        mock_send.assert_called_once()
        assert mock_send.call_args[1]["client_id"] == 123
        assert mock_send.call_args[1]["file_id"] == "photo_file_id"

    @pytest.mark.asyncio
    async def test_process_document_file(self):
        """Verify admin can upload a document file."""
        from handlers.admin import process_document_file

        message = _admin_message(None)
        message.document = MagicMock()
        message.document.file_id = "doc_file_id"
        state = MockFSMContext()
        state._data["order_id"] = "ORDER_TEST456"
        state._data["action"] = "send_doc"

        with patch("handlers.admin.orders", {"ORDER_TEST456": {"user_id": 456}}):
            with patch("utils.router.send_document_to_client") as mock_send:
                await process_document_file(message, state)

        mock_send.assert_called_once()
        assert mock_send.call_args[1]["client_id"] == 456
        assert mock_send.call_args[1]["file_id"] == "doc_file_id"

    @pytest.mark.asyncio
    async def test_process_no_file_rejected(self):
        """Verify non-file message is rejected."""
        from handlers.admin import process_document_file

        message = _admin_message("just text")
        state = MockFSMContext()
        state._data["order_id"] = "ORDER_TEST123"

        await process_document_file(message, state)

        assert "файл" in (message._answered_text or "").lower()

    @pytest.mark.asyncio
    async def test_process_unknown_order(self):
        """Verify unknown order shows error."""
        from handlers.admin import process_document_file

        message = _admin_message(None)
        message.photo = [MockPhoto(file_id="photo_file_id")]
        state = MockFSMContext()
        state._data["order_id"] = "ORDER_UNKNOWN"

        with patch("handlers.admin.orders", {}):
            await process_document_file(message, state)

        assert "не найден" in (message._answered_text or "")


# ── /track command ─────────────────────────────────────────────────────


class TestCmdTrack:
    """Tests for the /track command handler."""

    @pytest.mark.asyncio
    async def test_track_with_valid_params(self):
        """Verify /track with order and tracking number works."""
        from handlers.admin import cmd_track

        message = _admin_message("/track ORDER_TEST123 TRACK123")
        state = MockFSMContext()

        with patch("utils.auth.is_admin", return_value=True):
            await cmd_track(message, state)

        assert "TRACK123" in (message._answered_text or "")

    @pytest.mark.asyncio
    async def test_track_without_params_shows_help(self):
        """Verify /track without params shows format help."""
        from handlers.admin import cmd_track

        message = _admin_message("/track")
        state = MockFSMContext()

        with patch("utils.auth.is_admin", return_value=True):
            await cmd_track(message, state)

        assert "формате" in (message._answered_text or "")


# ── callback_send_track ────────────────────────────────────────────────


class TestCallbackSendTrack:
    """Tests for the 'send_track_ORDER' callback handler."""

    @pytest.mark.asyncio
    async def test_callback_send_track_sets_state(self):
        """Verify callback sets FSM state for tracking number."""
        from handlers.admin import callback_send_track

        callback = MockCallback(data="send_track_ORDER_TEST123")
        callback.from_user.username = "admin"
        state = MockFSMContext()

        with patch("utils.auth.ADMIN_USERNAME", "admin"):
            with patch("utils.auth.is_admin", return_value=True):
                await callback_send_track(callback, state)

        assert state._data.get("state") == AdminState.waiting_for_tracking
        assert state._data.get("order_id") == "ORDER_TEST123"
        assert state._data.get("action") == "send_track"

    @pytest.mark.asyncio
    async def test_callback_send_track_rejects_non_admin(self):
        """Verify non-admin gets alert."""
        from handlers.admin import callback_send_track

        callback = MockCallback(data="send_track_ORDER_TEST123")
        callback.from_user.username = "attacker"
        state = MockFSMContext()

        with patch("utils.auth.ADMIN_USERNAME", "admin"):
            with patch("utils.auth.is_admin", return_value=False):
                await callback_send_track(callback, state)

        assert callback._answered is True
        assert "нет прав" in (callback._answered_text or "").lower()


# ── process_tracking_number ────────────────────────────────────────────


class TestProcessTrackingNumber:
    """Tests for entering a tracking number as admin."""

    @pytest.mark.asyncio
    async def test_process_tracking_number_sends_to_client(self):
        """Verify tracking number is sent to the client."""
        from handlers.admin import process_tracking_number

        message = _admin_message("TRACK123")
        state = MockFSMContext()
        state._data["order_id"] = "ORDER_TEST123"
        state._data["action"] = "send_track"

        with patch("handlers.admin.orders", {"ORDER_TEST123": {"user_id": 123}}):
            with patch("utils.router.send_tracking_to_client") as mock_send:
                await process_tracking_number(message, state)

        mock_send.assert_called_once()
        assert mock_send.call_args[1]["client_id"] == 123
        assert mock_send.call_args[1]["tracking_number"] == "TRACK123"

    @pytest.mark.asyncio
    async def test_process_tracking_unknown_order(self):
        """Verify unknown order shows error."""
        from handlers.admin import process_tracking_number

        message = _admin_message("TRACK123")
        state = MockFSMContext()
        state._data["order_id"] = "ORDER_UNKNOWN"

        with patch("handlers.admin.orders", {}):
            await process_tracking_number(message, state)

        assert "не найден" in (message._answered_text or "")


# ── callback_order_done ────────────────────────────────────────────────


class TestCallbackOrderDone:
    """Tests for the 'order_done_ORDER' callback handler."""

    @pytest.mark.asyncio
    async def test_order_done_updates_status(self):
        """Verify order status is updated to completed."""
        from handlers.admin import callback_order_done

        callback = MockCallback(data="order_done_ORDER_TEST123")
        callback.from_user.username = "admin"
        state = MockFSMContext()

        orders_store = {"ORDER_TEST123": {"status": "new", "user_id": 123}}

        with patch("utils.auth.ADMIN_USERNAME", "admin"):
            with patch("utils.auth.is_admin", return_value=True):
                with patch("handlers.admin.orders", orders_store):
                    await callback_order_done(callback, state)

        assert orders_store["ORDER_TEST123"]["status"] == "completed"
        assert callback._answered is True

    @pytest.mark.asyncio
    async def test_order_done_rejects_non_admin(self):
        """Verify non-admin cannot mark order as done."""
        from handlers.admin import callback_order_done

        callback = MockCallback(data="order_done_ORDER_TEST123")
        callback.from_user.username = "attacker"
        state = MockFSMContext()

        with patch("utils.auth.ADMIN_USERNAME", "admin"):
            with patch("utils.auth.is_admin", return_value=False):
                await callback_order_done(callback, state)

        assert callback._answered is True
        assert "нет прав" in (callback._answered_text or "").lower()


# ── /orders command ────────────────────────────────────────────────────


class TestCmdOrders:
    """Tests for the /orders command handler."""

    @pytest.mark.asyncio
    async def test_orders_shows_list(self):
        """Verify /orders returns formatted order list."""
        from handlers.admin import cmd_orders_list

        message = _admin_message("/orders")
        state = MockFSMContext()

        mock_db = MagicMock()
        mock_order_1 = MagicMock()
        mock_order_1.order_id = "ORDER_001"
        mock_order_1.status = "paid"
        mock_order_1.total_price = 150
        mock_order_2 = MagicMock()
        mock_order_2.order_id = "ORDER_002"
        mock_order_2.status = "completed"
        mock_order_2.total_price = 200

        mock_db.query.return_value.order_by.return_value.all.return_value = [
            mock_order_1,
            mock_order_2,
        ]

        with patch("utils.auth.is_admin", return_value=True):
            with patch("db.crud.SessionLocal", return_value=mock_db):
                await cmd_orders_list(message, state)

        assert "ORDER_001" in (message._answered_text or "")
        assert "ORDER_002" in (message._answered_text or "")
        assert "paid" in (message._answered_text or "")
        assert "completed" in (message._answered_text or "")

    @pytest.mark.asyncio
    async def test_orders_empty(self):
        """Verify /orders shows empty message when no orders."""
        from handlers.admin import cmd_orders_list

        message = _admin_message("/orders")
        state = MockFSMContext()

        mock_db = MagicMock()
        mock_db.query.return_value.order_by.return_value.all.return_value = []

        with patch("utils.auth.is_admin", return_value=True):
            with patch("db.crud.SessionLocal", return_value=mock_db):
                await cmd_orders_list(message, state)

        assert "нет" in (message._answered_text or "").lower()


# ── /stats command ─────────────────────────────────────────────────────


class TestCmdStats:
    """Tests for the /stats command handler."""

    @pytest.mark.asyncio
    async def test_stats_shows_counts(self):
        """Verify /stats returns formatted statistics."""
        from handlers.admin import cmd_stats

        message = _admin_message("/stats")

        mock_db = MagicMock()
        mock_db.query.return_value.count.side_effect = [10, 2, 3, 1, 1, 1, 1, 1]

        with patch("utils.auth.is_admin", return_value=True):
            with patch("db.crud.SessionLocal", return_value=mock_db):
                await cmd_stats(message)

        assert "Всего" in (message._answered_text or "")
        assert "10" in (message._answered_text or "")


# ── /help_admin command ────────────────────────────────────────────────


class TestCmdHelpAdmin:
    """Tests for the /help_admin command handler."""

    @pytest.mark.asyncio
    async def test_help_admin_shows_commands(self):
        """Verify /help_admin shows available commands."""
        from handlers.admin import cmd_help_admin

        message = _admin_message("/help_admin")

        with patch("utils.auth.is_admin", return_value=True):
            await cmd_help_admin(message)

        assert "/send_doc" in (message._answered_text or "")
        assert "/track" in (message._answered_text or "")
        assert "/orders" in (message._answered_text or "")
        assert "/stats" in (message._answered_text or "")


# ── extract_order_id utility ───────────────────────────────────────────


class TestExtractOrderId:
    """Tests for the extract_order_id helper function."""

    def test_extracts_full_order_id(self):
        from handlers.admin import extract_order_id

        result = extract_order_id("ORDER_ABC123")
        assert result == "ABC123"

    def test_extracts_from_text(self):
        from handlers.admin import extract_order_id

        result = extract_order_id("Some text ORDER_XYZ789 more text")
        assert result == "XYZ789"

    def test_returns_none_for_no_match(self):
        from handlers.admin import extract_order_id

        result = extract_order_id("No order here")
        assert result is None

    def test_case_insensitive(self):
        from handlers.admin import extract_order_id

        result = extract_order_id("order_abc123")
        assert result == "ABC123"

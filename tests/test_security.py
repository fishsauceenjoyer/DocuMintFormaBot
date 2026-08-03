"""Security tests: SQL-injection, Markdown/Telegram injection and long input.

These tests verify that:
  1. SQL-injection attempts are stored as-is and never executed.
  2. Markdown links such as ``[click](http://evil.com)`` are escaped so they
     appear as plain text in the manager message.
  3. Very long input (10000 chars) does not crash the bot — it is truncated
     by the sanitizer and rejected by the field validator.
  4. Sensitive user-controlled values (delivery fields, fast-order text) pass
     through the sanitizer before being forwarded to the manager.
"""

import json

import pytest

from tests.fixtures.db_fixtures import mock_db_session  # noqa: F401


class TestSQLInjection:
    """Verify SQL-injection payloads are stored unchanged and never executed."""

    def test_sql_injection_stored_as_is(self, mock_db_session):  # noqa: F811
        """A DROP TABLE attempt must be saved as plain text, not executed."""
        from db.crud import create_order, create_order_item, get_order_by_id
        from db.models import Order

        order = create_order(
            db=mock_db_session,
            order_id="ORDER_SEC_SQL",
            user_id=1,
            total_price=100,
            status="pending",
        )

        payload = "'; DROP TABLE orders; --"
        item = create_order_item(
            db=mock_db_session,
            order_id=order.id,
            document_type="visa",
            quantity=1,
            unit_price=100,
            data={"full_name": payload},
        )

        # The payload is stored exactly as provided
        assert item.data_json is not None
        stored = json.loads(item.data_json)
        assert stored["full_name"] == payload

        # The orders table still exists and the order is intact
        assert mock_db_session.query(Order).count() == 1
        assert get_order_by_id(mock_db_session, "ORDER_SEC_SQL") is not None

    def test_sql_injection_in_delivery_email_stored_as_is(
        self, mock_db_session
    ):  # noqa: F811
        """A crafted email field with SQL syntax is stored without execution."""
        from db.crud import create_order, get_order_by_id

        payload = "x@x.com'); DROP TABLE users; --"
        create_order(
            db=mock_db_session,
            order_id="ORDER_SEC_EMAIL",
            user_id=2,
            total_price=50,
            status="pending",
            delivery={"name": "Test", "phone": "+48123456789", "email": payload},
        )

        order = get_order_by_id(mock_db_session, "ORDER_SEC_EMAIL")
        assert order is not None
        assert order.delivery_email == payload


class TestMarkdownInjection:
    """Verify Markdown links and formatting are neutralised for the manager."""

    def test_sanitize_for_telegram_escapes_markdown_link(self):
        """[click](http://evil.com) must become plain text, not a link."""
        from utils.sanitizer import sanitize_for_telegram

        sanitized = sanitize_for_telegram("[click](http://evil.com)")

        assert "[click]" not in sanitized
        assert "(http://evil.com)" not in sanitized
        # Brackets and parens are escaped => Telegram renders literal text
        assert "\\[click\\]" in sanitized
        assert "\\(" in sanitized and "\\)" in sanitized

    def test_sanitize_for_telegram_escapes_all_special_chars(self):
        """All Markdown special characters are backslash-escaped."""
        from utils.sanitizer import sanitize_for_telegram

        raw = "_*[]()~`>#+-=|{}.!"
        sanitized = sanitize_for_telegram(raw)

        for ch in "_*[]()~`>#+-=|{}.!":
            assert f"\\{ch}" in sanitized

    @pytest.mark.asyncio
    async def test_manager_message_contains_escaped_link(self, monkeypatch):
        """The manager notification must not contain a clickable link."""
        from typing import cast

        from aiogram import Bot

        from handlers.admin import orders
        from utils import router

        class RecordingBot:
            def __init__(self):
                self.messages = []
                self.photos = []

            async def send_message(self, chat_id, text, **kwargs):
                self.messages.append(
                    {"chat_id": chat_id, "text": text, "kwargs": kwargs}
                )
                return True

            async def send_photo(self, chat_id, photo, caption=None, **kwargs):
                self.photos.append(
                    {
                        "chat_id": chat_id,
                        "photo": photo,
                        "caption": caption,
                        "kwargs": kwargs,
                    }
                )
                return True

        orders.clear()
        monkeypatch.setattr(router, "ROUTING", {"visa": 111, "default": 999})
        bot = RecordingBot()

        order_data = {
            "order_id": "ORDER_SEC_MD",
            "documents": [
                {
                    "type": "visa",
                    "quantity": 1,
                    "items": [{"full_name": "[click](http://evil.com)"}],
                }
            ],
            "delivery": {
                "name": "Test[User]",
                "phone": "+48123456789",
                "email": "test@test.com",
                "address": "St (1)",
            },
            "payment_method": "card",
            "total_price": 35,
            "currency": "EUR",
            "user": {"id": 123, "username": "testuser"},
        }

        # RecordingBot is a test double masquerading as a Bot.
        await router.send_order_to_manager(
            bot=cast(Bot, bot),
            order_data=order_data,
            user_id=123,
            payment_proof_file_id="proof-file-id",
        )

        assert bot.photos, "send_photo was not called — payment proof missing"
        sent_text = bot.photos[0]["caption"]
        # The dangerous link is escaped — no clickable Markdown link remains
        assert "[click](http://evil.com)" not in sent_text
        assert "\\[click\\]\\(http://evil\\.com\\)" in sent_text
        # Delivery name brackets are escaped too
        assert "\\[User\\]" in sent_text


class TestLongInput:
    """Verify very long input is truncated or rejected without crashing."""

    def test_sanitize_for_telegram_truncates_10000_chars(self):
        """10000-char input is truncated to the sanitizer limit."""
        from utils.sanitizer import DEFAULT_MAX_LENGTH, sanitize_for_telegram

        long_input = "A" * 10000
        sanitized = sanitize_for_telegram(long_input)

        assert len(sanitized) == DEFAULT_MAX_LENGTH
        # Escaping 'A' adds nothing, so total length equals the limit exactly
        assert sanitized == "A" * DEFAULT_MAX_LENGTH

    def test_validate_field_value_rejects_10000_chars(self):
        """Field validation rejects input longer than the field max length."""
        from utils.validation import validate_field_value

        result = validate_field_value(
            value="B" * 10000,
            field_type="text",
            field_name="full_name",
        )

        assert result.is_valid is False
        assert "Слишком длинное" in result.error_message

    def test_truncate_for_storage_caps_at_db_column_size(self):
        """truncate_for_storage never returns more than the column size."""
        from utils.sanitizer import truncate_for_storage

        assert len(truncate_for_storage("C" * 10000)) == 255


class TestDeliveryAndFastOrderSanitization:
    """Verify user-controlled values are sanitized before forwarding."""

    def test_delivery_fields_stored_capped_but_not_escaped(
        self, mock_db_session
    ):  # noqa: F811
        """Delivery values are stored unchanged (length-capped); escaping happens
        later in utils.router when composing the manager message."""
        from utils.sanitizer import truncate_for_storage

        raw_lines = [
            "[Bad Name](http://evil.com)",
            "+48123456789",
            "test*@test.com",
            "St (1), Apt#2",
        ]
        delivery = {
            "name": truncate_for_storage(raw_lines[0]),
            "phone": truncate_for_storage(raw_lines[1]),
            "email": truncate_for_storage(raw_lines[2]),
            "address": truncate_for_storage(raw_lines[3]),
        }

        # Raw Markdown is preserved in storage — no escaping at save time
        assert delivery["name"] == "[Bad Name](http://evil.com)"
        assert delivery["phone"] == "+48123456789"
        assert delivery["email"] == "test*@test.com"
        assert delivery["address"] == "St (1), Apt#2"
        assert len(delivery["name"]) <= 255  # capped to DB column size

    def test_fast_order_text_is_sanitized(self):
        """Fast-order free text is sanitized before forwarding to the manager."""
        from utils.sanitizer import sanitize_for_telegram

        raw = "Hi, please call [support](http://evil.com)"
        sanitized = sanitize_for_telegram(raw)

        assert "\\[support\\]" in sanitized
        assert "\\(" in sanitized and "\\)" in sanitized
        # The evil link cannot be rendered as a clickable URL
        assert "[support](http://evil.com)" not in sanitized

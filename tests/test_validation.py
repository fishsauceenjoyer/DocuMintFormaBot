"""Tests for field validation logic (type, length, injection checks).

Run with:  pytest tests/test_validation.py -v

This file lives on the `feature/field-validation-tests` branch and tests
the validation layer to ensure we don't break it in future releases.
"""

import pytest

from templates.fields import Field
from utils.validation import (
    ValidationResult,
    _get_default_max_length,
    has_malicious_patterns,
    sanitize_text,
    validate_field_value,
)

# ── Field.type_hint() tests ──────────────────────────────────────────


class TestFieldTypeHint:
    """Verify that Field.type_hint() returns correct hints for each type."""

    def test_text_hint(self):
        f = Field("test", "Name", "text")
        hint = f.type_hint()
        assert "текст" in hint
        assert "255" in hint

    def test_text_hint_custom_max_length(self):
        f = Field("test", "Name", "text", max_length=100)
        hint = f.type_hint()
        assert "100" in hint

    def test_date_hint(self):
        f = Field("test", "Date", "date")
        hint = f.type_hint()
        assert "ДД.ММ.ГГГГ" in hint

    def test_email_hint(self):
        f = Field("test", "Email", "email")
        hint = f.type_hint()
        assert "email" in hint

    def test_phone_hint(self):
        f = Field("test", "Phone", "phone")
        hint = f.type_hint()
        assert "телефон" in hint

    def test_optional_text_hint(self):
        f = Field("test", "Note", "optional_text")
        hint = f.type_hint()
        assert "необязательно" in hint


# ── sanitize_text tests ──────────────────────────────────────────────


class TestSanitizeText:
    """Verify text sanitization removes extra whitespace."""

    def test_trims_whitespace(self):
        assert sanitize_text("  hello  ") == "hello"

    def test_normalizes_internal_spaces(self):
        assert sanitize_text("hello    world") == "hello world"

    def test_multiline_joins(self):
        assert sanitize_text("line1\nline2\nline3") == "line1 line2 line3"

    def test_empty_string(self):
        assert sanitize_text("") == ""

    def test_tabs_and_newlines(self):
        assert sanitize_text("\tfoo\tbar\nbaz") == "foo bar baz"


# ── has_malicious_patterns tests ─────────────────────────────────────


class TestMaliciousPatterns:
    """Verify detection of SQL injection, XSS, NoSQL and command injection."""

    def test_sql_select(self):
        assert has_malicious_patterns("SELECT * FROM users") is not None

    def test_sql_drop(self):
        assert has_malicious_patterns("DROP TABLE orders") is not None

    def test_sql_union(self):
        assert has_malicious_patterns("1 UNION SELECT * FROM passwords") is not None

    def test_sql_or_1_equals_1(self):
        assert has_malicious_patterns("' OR 1=1 --") is not None

    def test_sql_comment(self):
        assert has_malicious_patterns("admin'--") is not None

    def test_sql_insert(self):
        assert has_malicious_patterns("INSERT INTO users VALUES (...)") is not None

    def test_xss_script_tag(self):
        assert has_malicious_patterns("<script>alert('xss')</script>") is not None

    def test_xss_iframe(self):
        assert has_malicious_patterns("<iframe src='evil.com'></iframe>") is not None

    def test_xss_onclick(self):
        assert has_malicious_patterns("onclick=evil()") is not None

    def test_xss_javascript_protocol(self):
        assert has_malicious_patterns("javascript:alert(1)") is not None

    def test_xss_svg(self):
        assert has_malicious_patterns("<svg onload=alert(1)>") is not None

    def test_nosql_dollar_gt(self):
        assert has_malicious_patterns('{"$gt": ""}') is not None

    def test_nosql_dollar_where(self):
        assert has_malicious_patterns('{$where: "this.password"}') is not None

    def test_nosql_dollar_regex(self):
        assert has_malicious_patterns('{$regex: ".*"}') is not None

    def test_cmd_injection_pipe(self):
        assert has_malicious_patterns("| cat /etc/passwd") is not None

    def test_cmd_injection_semicolon(self):
        assert has_malicious_patterns("; rm -rf /") is not None

    def test_cmd_injection_backtick(self):
        assert has_malicious_patterns("`id`") is not None

    def test_safe_text_returns_none(self):
        assert has_malicious_patterns("John Doe") is None

    def test_safe_text_with_numbers(self):
        assert has_malicious_patterns("Fifth Avenue 123") is None

    def test_safe_cyrillic(self):
        assert has_malicious_patterns("Иван Петров") is None

    def test_safe_date_string(self):
        assert has_malicious_patterns("13.01.2022") is None

    def test_safe_address(self):
        assert has_malicious_patterns("ул. Пушкина, д. 10, кв. 5") is None


# ── validate_field_value tests ───────────────────────────────────────


class TestValidateFieldValue:
    """Core validation — type, length, injection, date validity."""

    def test_valid_text(self):
        result = validate_field_value("John Doe", "text", field_name="full_name")
        assert result.is_valid is True
        assert result.sanitized_value == "John Doe"

    def test_empty_value(self):
        result = validate_field_value("", "text", field_name="test")
        assert result.is_valid is False
        assert "пустым" in result.error_message

    def test_too_long_text(self):
        long_str = "A" * 300
        result = validate_field_value(long_str, "text", field_name="test")
        assert result.is_valid is False
        assert "Максимум 255" in result.error_message

    def test_too_long_with_custom_max(self):
        long_str = "A" * 50
        result = validate_field_value(
            long_str, "text", max_length=30, field_name="test"
        )
        assert result.is_valid is False
        assert "Максимум 30" in result.error_message

    def test_valid_date(self):
        result = validate_field_value("31.12.2024", "date", field_name="birth_date")
        assert result.is_valid is True

    def test_invalid_date_format(self):
        result = validate_field_value("2024-12-31", "date", field_name="birth_date")
        assert result.is_valid is False
        assert "формат" in result.error_message

    def test_date_wrong_format_dots(self):
        result = validate_field_value("31/12/2024", "date", field_name="birth_date")
        assert result.is_valid is False

    def test_date_year_out_of_range(self):
        from datetime import datetime

        current_year = datetime.utcnow().year
        result = validate_field_value(f"01.01.1899", "date", field_name="birth_date")
        assert result.is_valid is False
        assert "Год" in result.error_message
        assert "1900" in result.error_message
        assert str(current_year) in result.error_message

    def test_date_year_in_future(self):
        from datetime import datetime

        current_year = datetime.utcnow().year
        future_year = current_year + 1
        result = validate_field_value(
            f"01.01.{future_year}", "date", field_name="birth_date"
        )
        assert result.is_valid is False
        assert str(current_year) in result.error_message

    def test_date_month_out_of_range(self):
        result = validate_field_value("01.13.2000", "date", field_name="birth_date")
        assert result.is_valid is False
        # Calendar check catches impossible months with a unified message
        assert "не существует" in result.error_message

    def test_date_day_out_of_range(self):
        result = validate_field_value("32.01.2000", "date", field_name="birth_date")
        assert result.is_valid is False
        # Calendar check catches impossible days with a unified message
        assert "не существует" in result.error_message

    def test_valid_email(self):
        result = validate_field_value("user@example.com", "email", field_name="email")
        assert result.is_valid is True

    def test_invalid_email_no_at(self):
        result = validate_field_value("userexample.com", "email", field_name="email")
        assert result.is_valid is False

    def test_invalid_email_no_domain(self):
        result = validate_field_value("user@", "email", field_name="email")
        assert result.is_valid is False

    def test_valid_phone(self):
        result = validate_field_value("+48123456789", "phone", field_name="phone")
        assert result.is_valid is True

    def test_phone_with_spaces_and_dashes(self):
        result = validate_field_value("+48 123-456-789", "phone", field_name="phone")
        assert result.is_valid is True

    def test_invalid_phone_too_short(self):
        result = validate_field_value("123", "phone", field_name="phone")
        assert result.is_valid is False

    def test_text_with_sql_injection(self):
        result = validate_field_value(
            "Robert'); DROP TABLE users;--", "text", field_name="full_name"
        )
        assert result.is_valid is False
        assert "недопустимые символы" in result.error_message

    def test_text_with_xss(self):
        result = validate_field_value(
            "<script>alert(1)</script>", "text", field_name="full_name"
        )
        assert result.is_valid is False

    def test_date_with_injection_safe(self):
        # Dates are not checked for injection patterns, only format
        result = validate_field_value("12.12.2000", "date", field_name="date")
        assert result.is_valid is True

    def test_optional_text_empty_is_valid_if_optional(self):
        # Optional_text that is empty would be handled before validation
        # But validate_field_value still rejects empty
        result = validate_field_value("", "optional_text", field_name="note")
        assert result.is_valid is False

    def test_sanitize_removes_excess_spaces(self):
        result = validate_field_value("  John    Doe  ", "text", field_name="full_name")
        assert result.is_valid is True
        assert result.sanitized_value == "John Doe"

    def test_text_max_length_date_type(self):
        result = validate_field_value("01.01.2000 extra", "date", field_name="date")
        assert result.is_valid is False

    def test_text_sql_injection_concat(self):
        result = validate_field_value("CONCAT('a','b')", "text", field_name="test")
        assert result.is_valid is False

    def test_text_sql_information_schema(self):
        result = validate_field_value(
            "FROM INFORMATION_SCHEMA.TABLES", "text", field_name="test"
        )
        assert result.is_valid is False

    def test_text_cmd_injection_shell_exec(self):
        result = validate_field_value("system('ls')", "text", field_name="test")
        assert result.is_valid is False

    def test_text_cmd_injection_eval(self):
        result = validate_field_value("eval(malicious_code)", "text", field_name="test")
        assert result.is_valid is False

    def test_valid_long_text_within_limit(self):
        valid_text = "A" * 255
        result = validate_field_value(valid_text, "text", field_name="test")
        assert result.is_valid is True

    def test_nosql_dollar_in(self):
        result = validate_field_value("{$in: [1,2,3]}", "text", field_name="test")
        assert result.is_valid is False

    def test_valid_passport_number(self):
        result = validate_field_value(
            "FB363261", "passport_number", field_name="passport_number"
        )
        assert result.is_valid is True
        assert result.sanitized_value == "FB363261"

    def test_passport_number_with_allowed_chars(self):
        result = validate_field_value(
            "AB-123.45 / 678", "passport_number", field_name="passport_number"
        )
        assert result.is_valid is True
        assert result.sanitized_value == "AB-123.45 / 678"

    def test_passport_number_too_short(self):
        result = validate_field_value(
            "AB", "passport_number", field_name="passport_number"
        )
        assert result.is_valid is False
        assert "от 3" in result.error_message

    def test_passport_number_with_invalid_chars(self):
        result = validate_field_value(
            "AB@123", "passport_number", field_name="passport_number"
        )
        assert result.is_valid is False

    def test_passport_number_uppercased(self):
        result = validate_field_value(
            "fb363261", "passport_number", field_name="passport_number"
        )
        assert result.is_valid is True
        assert result.sanitized_value == "FB363261"

    def test_valid_country_code_pl(self):
        result = validate_field_value(
            "PL", "country_code", field_name="destination_country"
        )
        assert result.is_valid is True
        assert result.sanitized_value == "PL"

    def test_valid_country_code_ru(self):
        result = validate_field_value(
            "RU", "country_code", field_name="destination_country"
        )
        assert result.is_valid is True

    def test_valid_country_code_rs(self):
        result = validate_field_value(
            "RS", "country_code", field_name="destination_country"
        )
        assert result.is_valid is True

    def test_valid_country_code_am(self):
        result = validate_field_value(
            "AM", "country_code", field_name="destination_country"
        )
        assert result.is_valid is True

    def test_country_code_lowercase_normalized(self):
        result = validate_field_value(
            "pl", "country_code", field_name="destination_country"
        )
        assert result.is_valid is True
        assert result.sanitized_value == "PL"

    def test_country_code_invalid(self):
        result = validate_field_value(
            "XX", "country_code", field_name="destination_country"
        )
        assert result.is_valid is False
        assert "Допустимые страны" in result.error_message

    def test_country_code_wrong_length(self):
        result = validate_field_value(
            "POL", "country_code", field_name="destination_country"
        )
        assert result.is_valid is False


# ── _get_default_max_length tests ────────────────────────────────────


class TestDefaultMaxLength:
    """Verify default max lengths per field type."""

    def test_text_default(self):
        assert _get_default_max_length("text") == 255

    def test_date_default(self):
        assert _get_default_max_length("date") == 10

    def test_email_default(self):
        assert _get_default_max_length("email") == 255

    def test_phone_default(self):
        assert _get_default_max_length("phone") == 20

    def test_optional_text_default(self):
        assert _get_default_max_length("optional_text") == 255

    def test_unknown_type_default(self):
        assert _get_default_max_length("whatever") == 255


# ── Field constructor tests ──────────────────────────────────────────


class TestFieldConstructor:
    """Verify Field object creation with all params."""

    def test_minimal_creation(self):
        f = Field("id", "Prompt")
        assert f.id == "id"
        assert f.prompt == "Prompt"
        assert f.type == "text"
        assert f.optional is False
        assert f.max_length is None

    def test_full_creation(self):
        f = Field("email", "Email", "email", optional=True, max_length=100)
        assert f.id == "email"
        assert f.type == "email"
        assert f.optional is True
        assert f.max_length == 100

    def test_custom_type(self):
        f = Field("phone", "Phone", "phone")
        assert f.type == "phone"

    def test_passport_number_type_hint(self):
        f = Field("passport", "Number", "passport_number")
        hint = f.type_hint()
        assert "буквы" in hint
        assert "A-Z" in hint

    def test_country_code_type_hint(self):
        f = Field("country", "Country", "country_code")
        hint = f.type_hint()
        assert "код страны" in hint
        assert "PL" in hint or "RU" in hint


# ══════════════════════════════════════════════════════════════════════
# Equivalence-class & boundary-value parametrized tests
# ══════════════════════════════════════════════════════════════════════


class TestTextEquivalenceClasses:
    """Equivalence classes and boundary values for ``text`` fields."""

    @pytest.mark.parametrize(
        "value",
        [
            "John Doe",  # Latin name
            "Иван Петров",  # Cyrillic name
            "Olena Romenko",  # Two words
            "A",  # Single char (min boundary)
            "A" * 255,  # Max boundary
        ],
    )
    def test_valid_text_accepted(self, value):
        result = validate_field_value(value, "text", field_name="full_name")
        assert result.is_valid is True

    @pytest.mark.parametrize(
        "value,expected_error",
        [
            ("", "пустым"),  # Empty
            ("A" * 256, "Максимум"),  # Over max length
            ("   ", "пустым"),  # Whitespace only
            ("Robert'); DROP TABLE users;--", "недопустимые символы"),  # SQL injection
            ("<script>alert(1)</script>", "недопустимые символы"),  # XSS
        ],
    )
    def test_invalid_text_rejected(self, value, expected_error):
        result = validate_field_value(value, "text", field_name="full_name")
        assert result.is_valid is False
        assert expected_error in result.error_message


class TestDateEquivalenceClasses:
    """Equivalence classes and boundary values for ``date`` fields."""

    @pytest.mark.parametrize(
        "value",
        [
            "01.01.2000",  # Valid: start of year
            "31.12.2025",  # Valid: end of year
            "29.02.2000",  # Valid: leap year Feb 29
            "28.02.2001",  # Valid: non-leap year Feb 28
            "15.06.1990",  # Valid: mid-year
        ],
    )
    def test_valid_date_accepted(self, value):
        result = validate_field_value(value, "date", field_name="birth_date")
        assert result.is_valid is True

    @pytest.mark.parametrize(
        "value,expected_error",
        [
            ("", "пустым"),  # Empty
            ("32.01.2000", "не существует"),  # Day > 31
            ("00.01.2000", "не существует"),  # Day = 0
            ("01.13.2000", "не существует"),  # Month > 12 (calendar check)
            ("01.00.2000", "не существует"),  # Month = 0 (calendar check)
            ("01.01.1899", "Год"),  # Year < 1900
            ("2024-12-31", "формат"),  # Wrong format (ISO)
            ("31/12/2024", "формат"),  # Wrong separator
            ("31.02.2000", "не существует"),  # Feb 31 (impossible)
            ("30.02.2001", "не существует"),  # Feb 30 (impossible, non-leap)
            ("29.02.2001", "не существует"),  # Feb 29 non-leap year
        ],
    )
    def test_invalid_date_rejected(self, value, expected_error):
        result = validate_field_value(value, "date", field_name="birth_date")
        assert result.is_valid is False
        assert expected_error in result.error_message


class TestEmailEquivalenceClasses:
    """Equivalence classes and boundary values for ``email`` fields."""

    @pytest.mark.parametrize(
        "value",
        [
            "user@example.com",
            "test.user@domain.org",
            "a@b.co",  # Minimal valid
            "user+tag@mail.com",  # Plus addressing
        ],
    )
    def test_valid_email_accepted(self, value):
        result = validate_field_value(value, "email", field_name="email")
        assert result.is_valid is True

    @pytest.mark.parametrize(
        "value,expected_error",
        [
            ("", "пустым"),  # Empty
            ("userexample.com", "email"),  # No @
            ("user@", "email"),  # No domain
            ("@domain.com", "email"),  # No local part
            ("user@domain", "email"),  # No TLD
        ],
    )
    def test_invalid_email_rejected(self, value, expected_error):
        result = validate_field_value(value, "email", field_name="email")
        assert result.is_valid is False
        assert expected_error in result.error_message


class TestPhoneEquivalenceClasses:
    """Equivalence classes and boundary values for ``phone`` fields."""

    @pytest.mark.parametrize(
        "value",
        [
            "+48123456789",  # Minimal valid (11 chars)
            "+48 123-456-789",  # With spaces and dashes
            "+1 (555) 123-4567",  # International format
            "123456",  # 6 digits (min boundary)
        ],
    )
    def test_valid_phone_accepted(self, value):
        result = validate_field_value(value, "phone", field_name="phone")
        assert result.is_valid is True

    @pytest.mark.parametrize(
        "value,expected_error",
        [
            ("", "пустым"),  # Empty
            ("123", "телефон"),  # Too short (3 chars)
            ("12345", "телефон"),  # Too short (5 chars)
            ("abc", "телефон"),  # Non-numeric
        ],
    )
    def test_invalid_phone_rejected(self, value, expected_error):
        result = validate_field_value(value, "phone", field_name="phone")
        assert result.is_valid is False
        assert expected_error in result.error_message


class TestPassportNumberEquivalenceClasses:
    """Equivalence classes and boundary values for ``passport_number`` fields."""

    @pytest.mark.parametrize(
        "value",
        [
            "FB363261",  # Standard
            "AB-123.45 / 678",  # With allowed separators
            "ABC",  # Min boundary (3 chars)
            "A" * 30,  # Max boundary (30 chars)
            "fb363261",  # Lowercase (normalized to upper)
        ],
    )
    def test_valid_passport_accepted(self, value):
        result = validate_field_value(value, "passport_number", field_name="passport")
        assert result.is_valid is True

    @pytest.mark.parametrize(
        "value,expected_error",
        [
            ("", "пустым"),  # Empty
            ("AB", "от 3"),  # Too short (2 chars)
            ("A" * 31, "от 3"),  # Too long (31 chars)
            ("AB@123", "формат"),  # Invalid char
        ],
    )
    def test_invalid_passport_rejected(self, value, expected_error):
        result = validate_field_value(value, "passport_number", field_name="passport")
        assert result.is_valid is False
        assert expected_error in result.error_message


class TestCountryCodeEquivalenceClasses:
    """Equivalence classes and boundary values for ``country_code`` fields."""

    @pytest.mark.parametrize(
        "value",
        [
            "PL",  # Poland
            "RU",  # Russia
            "RS",  # Serbia
            "AM",  # Armenia
            "pl",  # Lowercase (normalized)
        ],
    )
    def test_valid_country_code_accepted(self, value):
        result = validate_field_value(value, "country_code", field_name="country")
        assert result.is_valid is True

    @pytest.mark.parametrize(
        "value,expected_error",
        [
            ("", "пустым"),  # Empty
            ("XX", "страны"),  # Not in allowed list
            ("POL", "страны"),  # Wrong length (3 chars)
            ("P", "страны"),  # Wrong length (1 char)
        ],
    )
    def test_invalid_country_code_rejected(self, value, expected_error):
        result = validate_field_value(value, "country_code", field_name="country")
        assert result.is_valid is False
        assert expected_error in result.error_message


class TestQuantityBoundaryValues:
    """Boundary values for document quantity (1–5) at the FSM level."""

    @pytest.mark.parametrize(
        "qty_data,should_accept",
        [
            ("qty_1", True),  # Min boundary
            ("qty_2", True),
            ("qty_3", True),
            ("qty_4", True),
            ("qty_5", True),  # Max boundary
            ("qty_0", False),  # Below min
            ("qty_6", False),  # Above max
            ("qty_99", False),  # Far above max
        ],
    )
    @pytest.mark.asyncio
    async def test_quantity_boundary(
        self, qty_data, should_accept, mock_fsm, clean_user_sessions
    ):
        from conftest import MockCallback  # type: ignore[import-not-found]

        from handlers.order import process_document_choice, process_quantity

        # Set up session by choosing a document first
        cb_doc = MockCallback(data="doc_visa")
        await process_document_choice(cb_doc, mock_fsm)

        cb_qty = MockCallback(data=qty_data, user_id=123)
        await process_quantity(cb_qty, mock_fsm)

        if should_accept:
            assert mock_fsm._data.get("state") is not None
            assert cb_qty._answered is True
        else:
            # Out-of-range quantities are rejected via callback.answer()
            assert cb_qty._answered is True
            assert cb_qty._show_alert is True
            assert "1 до 5" in (cb_qty._answered_text or "")

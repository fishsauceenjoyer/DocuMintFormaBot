"""Tests for data/business_config.py.

Verifies:
    - Constants are correct (countries, currencies, prices, patterns, etc.)
    - Helper functions return expected values
    - YAML template loading works
    - Edge cases (unknown document codes, missing fields)
"""

import re

import pytest


class TestConstants:
    """Tests for module-level constants."""

    def test_country_codes_has_expected_keys(self):
        """Verify COUNTRY_CODES contains PL, RU, RS, AM."""
        from data.business_config import COUNTRY_CODES

        assert "PL" in COUNTRY_CODES
        assert "RU" in COUNTRY_CODES
        assert "RS" in COUNTRY_CODES
        assert "AM" in COUNTRY_CODES
        assert len(COUNTRY_CODES) == 4

    def test_country_codes_values_have_required_languages(self):
        """Verify each country has en, ru, uk translations."""
        from data.business_config import COUNTRY_CODES

        for code, names in COUNTRY_CODES.items():
            assert "en" in names, f"{code} missing 'en'"
            assert "ru" in names, f"{code} missing 'ru'"
            assert "uk" in names, f"{code} missing 'uk'"

    def test_allowed_countries_hint_format(self):
        """Verify ALLOWED_COUNTRIES_HINT contains all country names."""
        from data.business_config import (
            ALLOWED_COUNTRIES_HINT,
            COUNTRY_CODES,
        )

        for code, names in COUNTRY_CODES.items():
            assert names["en"] in ALLOWED_COUNTRIES_HINT

    def test_destination_countries_matches_country_codes(self):
        """Verify DESTINATION_COUNTRIES is derived from COUNTRY_CODES keys."""
        from data.business_config import (
            COUNTRY_CODES,
            DESTINATION_COUNTRIES,
        )

        assert set(DESTINATION_COUNTRIES) == set(COUNTRY_CODES.keys())

    def test_passport_number_pattern_is_string(self):
        """Verify PASSPORT_NUMBER_PATTERN is a non-empty regex string."""
        from data.business_config import PASSPORT_NUMBER_PATTERN

        assert isinstance(PASSPORT_NUMBER_PATTERN, str)
        assert len(PASSPORT_NUMBER_PATTERN) > 0
        # Compile to verify it's a valid regex
        re.compile(PASSPORT_NUMBER_PATTERN)

    def test_supported_currencies(self):
        """Verify SUPPORTED_CURRENCIES contains EUR and PLN only."""
        from data.business_config import SUPPORTED_CURRENCIES

        assert "EUR" in SUPPORTED_CURRENCIES
        assert "PLN" in SUPPORTED_CURRENCIES
        assert len(SUPPORTED_CURRENCIES) == 2

    def test_delivery_prices_positive(self):
        """Verify delivery prices are positive integers."""
        from data.business_config import DELIVERY_PRICE_EUR, DELIVERY_PRICE_PLN

        assert isinstance(DELIVERY_PRICE_PLN, int)
        assert isinstance(DELIVERY_PRICE_EUR, int)
        assert DELIVERY_PRICE_PLN > 0
        assert DELIVERY_PRICE_EUR > 0

    def test_payment_details_keys(self):
        """Verify PAYMENT_DETAILS has blik, uah, usdt methods."""
        from data.business_config import PAYMENT_DETAILS

        assert "blik" in PAYMENT_DETAILS
        assert "uah" in PAYMENT_DETAILS
        assert "usdt" in PAYMENT_DETAILS
        for key, value in PAYMENT_DETAILS.items():
            assert isinstance(value, str)
            assert len(value) > 0

    def test_routing_keys(self):
        """Verify ROUTING_KEYS has expected document types."""
        from data.business_config import ROUTING_KEYS

        assert "visa" in ROUTING_KEYS
        assert "passport" in ROUTING_KEYS
        assert "apostille" in ROUTING_KEYS
        for key, value in ROUTING_KEYS.items():
            assert isinstance(value, str)
            assert value.startswith("ROUTING_")


class TestGetTemplate:
    """Tests for get_template function."""

    def test_returns_dict_for_known_code(self):
        """Verify get_template returns a dict for a known document code."""
        from data.business_config import get_template

        result = get_template("visa")
        assert result is not None
        assert isinstance(result, dict)

    def test_returns_none_for_unknown_code(self):
        """Verify get_template returns None for an unknown code."""
        from data.business_config import get_template

        result = get_template("nonexistent_document_xyz")
        assert result is None

    def test_returned_template_has_required_keys(self):
        """Verify template dict has name_ru, price_pln, fields, etc."""
        from data.business_config import get_template

        template = get_template("visa")
        assert "name_ru" in template
        assert "name_uk" in template
        assert "name_en" in template
        assert "price_pln" in template
        assert "price_eur" in template
        assert "fields" in template

    def test_template_fields_are_list(self):
        """Verify template fields is a list."""
        from data.business_config import get_template

        template = get_template("visa")
        assert isinstance(template["fields"], list)


class TestGetAllTemplates:
    """Tests for get_all_templates function."""

    def test_returns_list_of_tuples(self):
        """Verify get_all_templates returns list of (code, name) tuples."""
        from data.business_config import get_all_templates

        result = get_all_templates()
        assert isinstance(result, list)
        assert len(result) > 0
        for item in result:
            assert isinstance(item, tuple)
            assert len(item) == 2

    def test_contains_known_documents(self):
        """Verify known documents appear in get_all_templates."""
        from data.business_config import get_all_templates

        result = get_all_templates()
        codes = [code for code, _ in result]
        assert "visa" in codes
        assert "passport" in codes


class TestGetPricePln:
    """Tests for get_price_pln function."""

    def test_returns_positive_int_for_known_code(self):
        """Verify get_price_pln returns a positive integer for known codes."""
        from data.business_config import get_price_pln

        price = get_price_pln("visa")
        assert isinstance(price, int)
        assert price > 0

    def test_returns_zero_for_unknown_code(self):
        """Verify get_price_pln returns 0 for unknown code."""
        from data.business_config import get_price_pln

        price = get_price_pln("nonexistent_document_xyz")
        assert price == 0

    def test_specific_known_prices(self):
        """Verify specific document prices match expected values."""
        from data.business_config import get_price_pln

        # These values come from config/templates.yaml
        assert get_price_pln("visa") == 150
        assert get_price_pln("passport") == 200
        assert get_price_pln("apostille") == 120


class TestGetPriceEur:
    """Tests for get_price_eur function."""

    def test_returns_positive_int_for_known_code(self):
        """Verify get_price_eur returns a positive integer for known codes."""
        from data.business_config import get_price_eur

        price = get_price_eur("visa")
        assert isinstance(price, int)
        assert price > 0

    def test_returns_zero_for_unknown_code(self):
        """Verify get_price_eur returns 0 for unknown code."""
        from data.business_config import get_price_eur

        price = get_price_eur("nonexistent_document_xyz")
        assert price == 0

    def test_specific_known_prices(self):
        """Verify specific document prices match expected values."""
        from data.business_config import get_price_eur

        # These values come from config/templates.yaml
        assert get_price_eur("visa") == 35
        assert get_price_eur("passport") == 45
        assert get_price_eur("apostille") == 30


class TestPassportPattern:
    """Tests for PASSPORT_NUMBER_PATTERN validation."""

    def test_valid_passport_numbers(self):
        """Verify valid passport numbers match the pattern."""
        from data.business_config import PASSPORT_NUMBER_PATTERN

        pattern = re.compile(PASSPORT_NUMBER_PATTERN)
        valid_numbers = [
            "AB1234567",
            "123456789",
            "ABC-123/45",
        ]
        for number in valid_numbers:
            assert pattern.match(number), f"{number} should be valid"

    def test_invalid_passport_numbers(self):
        """Verify invalid passport numbers don't match the pattern."""
        from data.business_config import PASSPORT_NUMBER_PATTERN

        pattern = re.compile(PASSPORT_NUMBER_PATTERN)
        invalid_numbers = [
            "short",  # too short
            "a" * 31,  # too long
            "lowercase",  # lowercase not allowed
            "invalid@char",  # special chars not allowed
        ]
        for number in invalid_numbers:
            assert not pattern.match(number), f"{number} should be invalid"

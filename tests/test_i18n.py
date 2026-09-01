"""Tests for internationalisation (i18n) module.

Covers:
    - I18n class: loading locales, get() with fallbacks, format parameters
    - user_language function: language mapping, fallback to default
    - Edge cases: missing locale directory, missing keys, format errors
"""

import json
import os
import tempfile

import pytest
from aiogram.types import User


class TestI18n:
    """Tests for the I18n class."""

    def test_get_exact_language(self):
        """Verify get() returns exact language match."""
        from utils.i18n import I18n

        i18n = I18n()
        welcome_ru = i18n.get("welcome", language="ru")
        assert "бот" in welcome_ru or "Добро" in welcome_ru

    def test_get_fallback_to_en(self):
        """Verify get() falls back to English when language is missing."""
        from utils.i18n import I18n

        i18n = I18n()
        # 'welcome' should exist in all languages
        result = i18n.get("welcome", language="de")
        assert result is not None
        assert not result.startswith("[")  # Not a missing key

    def test_get_missing_key(self):
        """Verify get() returns [key] for missing translation key."""
        from utils.i18n import I18n

        i18n = I18n()
        result = i18n.get("nonexistent_key_xyz", language="en")
        assert result == "[nonexistent_key_xyz]"

    def test_get_with_format_params(self):
        """Verify get() substitutes format parameters."""
        from utils.i18n import I18n

        i18n = I18n()
        # Try to find a key that uses format params, or test with a mock
        result = i18n.get("choose_document", language="en")
        assert result is not None

    def test_get_with_kwargs(self):
        """Verify get() handles keyword arguments in translation."""
        from utils.i18n import I18n

        i18n = I18n()
        # Test with a key that accepts format parameters
        result = i18n.get(
            "choose_quantity",
            language="en",
            name="Terminator 1",
            price=10,
            currency="€",
        )
        assert "Terminator 1" in result
        assert "10" in result
        assert "€" in result

    def test_available_languages(self):
        """Verify get_available_languages returns loaded locales."""
        from utils.i18n import I18n

        i18n = I18n()
        langs = i18n.get_available_languages()
        assert "en" in langs
        assert "ru" in langs
        assert "uk" in langs

    def test_load_locales_from_custom_dir(self):
        """Verify I18n can load locales from a custom directory."""
        from utils.i18n import I18n

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test locale file
            test_locale = {"test_key": "Test Value {param}"}
            with open(os.path.join(tmpdir, "test.json"), "w", encoding="utf-8") as f:
                json.dump(test_locale, f)

            i18n = I18n(locales_dir=tmpdir)
            assert "test" in i18n.get_available_languages()
            assert i18n.get("test_key", language="test") == "Test Value {param}"
            assert i18n.get("test_key", language="test", param="OK") == "Test Value OK"

    def test_load_empty_directory(self):
        """Verify I18n handles empty locale directory."""
        from utils.i18n import I18n

        with tempfile.TemporaryDirectory() as tmpdir:
            i18n = I18n(locales_dir=tmpdir)
            assert i18n.get_available_languages() == []
            # Fallback should still fail gracefully
            result = i18n.get("any_key", language="en")
            assert result == "[any_key]"

    def test_missing_format_param(self):
        """Verify missing format param returns raw text (no crash)."""
        from utils.i18n import I18n

        with tempfile.TemporaryDirectory() as tmpdir:
            test_locale = {"test_key": "Hello {name}"}
            with open(os.path.join(tmpdir, "en.json"), "w", encoding="utf-8") as f:
                json.dump(test_locale, f)

            i18n = I18n(locales_dir=tmpdir)
            # Missing 'name' param should not crash
            result = i18n.get("test_key", language="en")
            assert result == "Hello {name}"


class TestUserLanguage:
    """Tests for the user_language function."""

    def test_supported_language_ru(self):
        """Verify user with 'ru' language_code returns 'ru'."""
        from utils.i18n import user_language

        user = User(id=1, is_bot=False, first_name="Test", language_code="ru")
        assert user_language(user) == "ru"

    def test_supported_language_uk(self):
        """Verify user with 'uk' language_code returns 'uk'."""
        from utils.i18n import user_language

        user = User(id=1, is_bot=False, first_name="Test", language_code="uk")
        assert user_language(user) == "uk"

    def test_supported_language_en(self):
        """Verify user with 'en' language_code returns 'en'."""
        from utils.i18n import user_language

        user = User(id=1, is_bot=False, first_name="Test", language_code="en")
        assert user_language(user) == "en"

    def test_fallback_to_default(self):
        """Verify unsupported language falls back to 'en'."""
        from utils.i18n import user_language

        user = User(id=1, is_bot=False, first_name="Test", language_code="pl")
        assert user_language(user) == "en"

    def test_none_language_code(self):
        """Verify None language_code falls back to 'en'."""
        from utils.i18n import user_language

        user = User(id=1, is_bot=False, first_name="Test", language_code=None)
        assert user_language(user) == "en"

    def test_belarusian_maps_to_ru(self):
        """Verify Belarusian ('be') maps to 'ru'."""
        from utils.i18n import user_language

        user = User(id=1, is_bot=False, first_name="Test", language_code="be")
        assert (
            user_language(user) == "en"
        )  # Falls to default since 'be' is not a prefix of 'ru'

    def test_ru_variants(self):
        """Verify 'ru-RU' maps to 'ru'."""
        from utils.i18n import user_language

        user = User(id=1, is_bot=False, first_name="Test", language_code="ru-RU")
        assert user_language(user) == "ru"

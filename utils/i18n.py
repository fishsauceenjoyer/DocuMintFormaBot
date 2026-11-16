"""
Internationalisation (i18n) for the Telegram bot.

Loads translations from JSON files in the locales/ folder.
Provides a simple API to retrieve strings by key and language,
and a helper to determine a user's language from their Telegram settings.
"""

import json
import logging
import os
from typing import Any, Dict, Optional

from aiogram.types import User

logger = logging.getLogger(__name__)

# Default locale directory
LOCALES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "locales")

# Supported language codes — used to map Telegram language_code → our keys
SUPPORTED_LANGUAGES = {"ru", "uk", "en"}
DEFAULT_LANGUAGE = "en"


def user_language(user: User) -> str:
    """Determine the bot interface language from a Telegram user object.

    Inspects ``user.language_code`` (e.g. "ru", "uk", "en", "be", "pl") and maps
    it to one of the supported languages. Falls back to *en* for unsupported codes.
    """
    if user.language_code and user.language_code in SUPPORTED_LANGUAGES:
        return user.language_code
    # Map Belarusian → Russian, Polish → English, etc.
    # Only handle direct matches; everything else → default
    if user.language_code and user.language_code.startswith("ru"):
        return "ru"
    if user.language_code and user.language_code.startswith("uk"):
        return "uk"
    return DEFAULT_LANGUAGE


class I18n:
    """Translation manager for the bot's multilingual interface.

    Loads JSON locale files from the *locales/* directory and provides
    :meth:`get` to retrieve a translated string by key and language.

    Attributes:
        locales: Dictionary ``{language_code: {key: translated_text}}``.
    """

    def __init__(self, locales_dir: str = LOCALES_DIR) -> None:
        """Initialise I18n, loading all available translations.

        Args:
            locales_dir: Path to the folder containing JSON locale files.
        """
        self.locales_dir = locales_dir
        self.locales: Dict[str, Dict[str, str]] = {}
        self._load_locales()

    def _load_locales(self) -> None:
        """Load all JSON locale files from the locales directory."""
        if not os.path.exists(self.locales_dir):
            logger.warning(f"Locales directory not found: {self.locales_dir}")
            return

        for filename in os.listdir(self.locales_dir):
            if filename.endswith(".json"):
                lang_code = filename[:-5]  # Remove .json suffix
                filepath = os.path.join(self.locales_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        self.locales[lang_code] = json.load(f)
                    keys_count = len(self.locales[lang_code])
                    logger.info(f"Loaded locale: {lang_code} ({keys_count} keys)")
                except Exception as e:
                    logger.error(f"Error loading locale {filename}: {e}")

    def get(self, key: str, language: str = DEFAULT_LANGUAGE, **kwargs: Any) -> str:
        """Return a translated string by key and language.

        Resolution order:
            1. Exact language.
            2. Fallback to ``DEFAULT_LANGUAGE`` (English).
            3. Return ``[key]`` if nothing matches.

        If *kwargs* are supplied, they are substituted via ``.format()``.

        Args:
            key: Translation key (e.g. ``"welcome"``, ``"order_accepted"``).
            language: Language code (``"ru"``, ``"uk"``, ``"en"``).
            **kwargs: Parameters to substitute into the text.

        Returns:
            Translated string, or ``[key]`` if not found.
        """
        # Try exact language first
        translations = self.locales.get(language, {})
        text = translations.get(key)

        if text is None:
            # Fallback to English
            fallback = self.locales.get(DEFAULT_LANGUAGE, {})
            text = fallback.get(key)

        if text is None:
            logger.warning(
                f"Translation key not found: '{key}' for language '{language}'"
            )
            return f"[{key}]"

        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError as e:
                logger.error(f"Missing format parameter {e} in translation key '{key}'")
                return text

        return text

    def get_available_languages(self) -> list:
        """Return the list of available language codes.

        Returns:
            List of language code strings (e.g. ``["en", "ru", "uk"]``).
        """
        return list(self.locales.keys())


# Singleton instance for easy import
_i18n: Optional[I18n] = None


def get_i18n() -> I18n:
    """Return the global I18n singleton (created on first call).

    Returns:
        I18n instance with loaded translations.
    """
    global _i18n
    if _i18n is None:
        _i18n = I18n()
    return _i18n

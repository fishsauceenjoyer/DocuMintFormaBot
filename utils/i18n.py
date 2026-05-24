"""
Интернационализация (i18n) для Telegram-бота.

Загружает переводы из JSON-файлов в папке locales/.
Предоставляет простой API для получения текста на нужном языке.

Использование:
    i18n = I18n()
    welcome_text = i18n.get("welcome", language="uk")
    # или с подстановками:
    text = i18n.get("order_created", language="uk", order_id="ORDER_123")
"""

import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Default locale directory
LOCALES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "locales")


class I18n:
    """
    Менеджер переводов для многоязычного интерфейса бота.

    Загружает JSON-файлы локализации из папки locales/ и предоставляет
    метод get() для получения текста по ключу и языку.

    Атрибуты:
        locales: Словарь {language_code: {key: text}}
    """

    def __init__(self, locales_dir: str = LOCALES_DIR) -> None:
        """
        Инициализирует I18n, загружая все доступные переводы.

        Args:
            locales_dir: Путь к папке с JSON-файлами локализации.
        """
        self.locales_dir = locales_dir
        self.locales: Dict[str, Dict[str, str]] = {}
        self._load_locales()

    def _load_locales(self) -> None:
        """Загружает все JSON-файлы локализации из папки locales/."""
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
                    logger.info(f"Loaded locale: {lang_code} ({len(self.locales[lang_code])} keys)")
                except Exception as e:
                    logger.error(f"Error loading locale {filename}: {e}")

    def get(self, key: str, language: str = "ru", **kwargs: Any) -> str:
        """
        Возвращает переведённую строку по ключу и языку.

        Если перевод не найден, возвращает ключ в квадратных скобках.
        Если указаны kwargs — делает подстановку через .format().

        Args:
            key: Ключ перевода (например, "welcome", "order_created").
            language: Код языка ("ru", "uk").
            **kwargs: Параметры для подстановки в текст.

        Returns:
            Переведённая строка или ключ в скобках, если перевод не найден.
        """
        # Try exact language first, fall back to "ru", then return key
        translations = self.locales.get(language, {})
        text = translations.get(key)

        if text is None:
            # Fallback to Russian
            fallback = self.locales.get("ru", {})
            text = fallback.get(key)

        if text is None:
            logger.warning(f"Translation key not found: '{key}' for language '{language}'")
            return f"[{key}]"

        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError as e:
                logger.error(f"Missing format parameter {e} in translation key '{key}'")
                return text

        return text

    def get_available_languages(self) -> list:
        """
        Возвращает список доступных кодов языков.

        Returns:
            Список строк с кодами языков (например, ["ru", "uk"]).
        """
        return list(self.locales.keys())


# Singleton instance for easy import
_i18n: Optional[I18n] = None


def get_i18n() -> I18n:
    """
    Возвращает глобальный экземпляр I18n (создаёт при первом вызове).

    Returns:
        Экземпляр I18n с загруженными переводами.
    """
    global _i18n
    if _i18n is None:
        _i18n = I18n()
    return _i18n
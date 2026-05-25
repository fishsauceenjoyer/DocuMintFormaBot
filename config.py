"""Runtime configuration loaded from environment variables.

This is the single place for bot secrets, manager routing chat IDs, payment
details, delivery price, and database URL. Import constants from here instead
of reading environment variables in handlers directly.
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ID чатов для разных типов документов (из .env)
ROUTING = {
    "sanepid": int(os.getenv("ROUTING_SANEPID", "-100123456789")),
    "bhp": int(os.getenv("ROUTING_BHP", "-100987654321")),
    "psychotests": int(os.getenv("ROUTING_PSYCHOTESTS", "123456789")),
    "pesel": int(os.getenv("ROUTING_PESEL", "-100123456788")),
    "default": int(os.getenv("ROUTING_DEFAULT", "555555555")),
}

# Реквизиты для оплаты (из .env)
PAYMENT_DETAILS = {
    "blik": os.getenv("PAYMENT_BLIK", "Номер телефона: +48 123 456 789"),
    "uah": os.getenv(
        "PAYMENT_UAH", "ПриватБанк: 5168 7456 1234 5678\nПолучатель: Ivanov Ivan"
    ),
    "usdt": os.getenv("PAYMENT_USDT", "TRC20: TXYZ... (кошелек)"),
}

# Стоимость доставки
DELIVERY_PRICE = 20  # zł

# Админ username
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")

# База данных
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot.db")


def validate_config() -> None:
    """
    Проверяет обязательные настройки конфигурации при запуске бота.

    Выполняет проверки:
        - BOT_TOKEN должен быть задан и не быть значением-заглушкой
        - ADMIN_USERNAME должен быть задан
        - Все chat_id в ROUTING должны быть валидными целыми числами
        - DATABASE_URL должен быть задан

    Raises:
        SystemExit: Если какая-либо проверка не пройдена,
                    с выводом описания ошибки в stderr.
    """
    errors: list[str] = []

    # Check BOT_TOKEN
    if not BOT_TOKEN:
        errors.append("BOT_TOKEN is not set in .env file")
    elif BOT_TOKEN == "your_bot_token_here":
        errors.append(
            "BOT_TOKEN is still the placeholder value 'your_bot_token_here'. "
            "Replace it with a real token from @BotFather"
        )

    # Check ADMIN_USERNAME
    if not ADMIN_USERNAME:
        errors.append("ADMIN_USERNAME is not set in .env file")

    # Check ROUTING chat_ids
    for key, chat_id_value in [
        ("ROUTING_SANEPID", ROUTING.get("sanepid")),
        ("ROUTING_BHP", ROUTING.get("bhp")),
        ("ROUTING_PSYCHOTESTS", ROUTING.get("psychotests")),
        ("ROUTING_PESEL", ROUTING.get("pesel")),
        ("ROUTING_DEFAULT", ROUTING.get("default")),
    ]:
        if chat_id_value is None:
            errors.append(f"{key} is not set in .env file")

    # Check DATABASE_URL
    if not DATABASE_URL:
        errors.append("DATABASE_URL is not set in .env file")

    if errors:
        error_text = "\n  - ".join(["Configuration errors found:"] + errors)
        print(error_text, file=sys.stderr)
        sys.exit(1)

    print("Configuration validation passed.", file=sys.stderr)

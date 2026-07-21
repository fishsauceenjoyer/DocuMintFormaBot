"""Runtime configuration loaded from environment variables.

This is the single place for bot secrets, manager routing chat IDs, payment
details, delivery price, and database URL. Import constants from here instead
of reading environment variables in handlers directly.
"""

import os
import sys

from dotenv import load_dotenv

from data.business_config import (
    DELIVERY_PRICE_EUR,
    DELIVERY_PRICE_PLN,
    PAYMENT_DETAILS as BIZ_PAYMENT_DETAILS,
    ROUTING_KEYS,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Chat IDs for different document types (from .env)
# Keys are automatically built from the business config's ROUTING_KEYS mapping
# e.g. ROUTING_VISA, ROUTING_PASSPORT, etc.
ROUTING: dict[str, int] = {
    doc_code: int(os.getenv(env_key, "-100123456789"))
    for doc_code, env_key in ROUTING_KEYS.items()
}
ROUTING["default"] = int(os.getenv("ROUTING_DEFAULT", "555555555"))

# Payment details (from business_config — override via .env if needed)
PAYMENT_DETAILS = {
    "blik": os.getenv("PAYMENT_BLIK", BIZ_PAYMENT_DETAILS["blik"]),
    "uah": os.getenv("PAYMENT_UAH", BIZ_PAYMENT_DETAILS["uah"]),
    "usdt": os.getenv("PAYMENT_USDT", BIZ_PAYMENT_DETAILS["usdt"]),
}

# Delivery prices
DELIVERY_PRICE_PLN = DELIVERY_PRICE_PLN
DELIVERY_PRICE_EUR = DELIVERY_PRICE_EUR
# Convenience alias for backwards-compatibility (uses PLN)
DELIVERY_PRICE = DELIVERY_PRICE_PLN

# Admin username
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot.db")


def validate_config() -> None:
    """
    Validate required configuration at bot startup.

    Checks:
        - BOT_TOKEN is set and not a placeholder
        - ADMIN_USERNAME is set
        - All ROUTING chat IDs are valid integers
        - DATABASE_URL is set

    Raises:
        SystemExit: If any check fails, with details written to stderr.
    """
    errors: list[str] = []

    if not BOT_TOKEN:
        errors.append("BOT_TOKEN is not set in .env file")
    elif BOT_TOKEN == "your_bot_token_here":
        errors.append(
            "BOT_TOKEN is still the placeholder value 'your_bot_token_here'. "
            "Replace it with a real token from @BotFather"
        )

    if not ADMIN_USERNAME:
        errors.append("ADMIN_USERNAME is not set in .env file")

    for doc_code, env_key in ROUTING_KEYS.items():
        chat_id_value = ROUTING.get(doc_code)
        if chat_id_value is None:
            errors.append(f"{env_key} is not set in .env file")

    if not DATABASE_URL:
        errors.append("DATABASE_URL is not set in .env file")

    if errors:
        error_text = "\n  - ".join(["Configuration errors found:"] + errors)
        print(error_text, file=sys.stderr)
        sys.exit(1)

    print("Configuration validation passed.", file=sys.stderr)

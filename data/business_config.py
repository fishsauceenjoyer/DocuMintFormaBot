"""
Business configuration — the single source of truth for all domain-specific data.

This file contains:
- Document types, their fields, prices (PLN & EUR) and routing keys
- Allowed destination countries for demo_service applications
- demo_document number format (regex pattern)
- Delivery price
- Payment details (placeholders)

Replace these values with your own business data when deploying.
"""

from typing import Any, Dict, List

from templates.fields import Field


# ──────────────────────────────────────────────────────────────────────
# Allowed destination countries (for demo_service / document travel fields)
# ──────────────────────────────────────────────────────────────────────
COUNTRY_CODES: Dict[str, Dict[str, str]] = {
    "PL": {"en": "Poland", "ru": "Польша", "uk": "Польща"},
    "RU": {"en": "Russia", "ru": "Россия", "uk": "Росія"},
    "RS": {"en": "Serbia", "ru": "Сербия", "uk": "Сербія"},
    "AM": {"en": "Armenia", "ru": "Армения", "uk": "Вірменія"},
}

ALLOWED_COUNTRIES_HINT: str = " / ".join(
    f"{v['en']} ({k})" for k, v in COUNTRY_CODES.items()
)

DESTINATION_COUNTRIES: List[str] = list(COUNTRY_CODES.keys())


# ──────────────────────────────────────────────────────────────────────
# demo_document number format (regex)
# ──────────────────────────────────────────────────────────────────────
demo_document_ref_PATTERN: str = r"^[A-Z0-9\s\-\.\/]{3,30}$"


# ──────────────────────────────────────────────────────────────────────
# Currencies
# ──────────────────────────────────────────────────────────────────────
SUPPORTED_CURRENCIES: List[str] = ["EUR", "PLN"]


# ──────────────────────────────────────────────────────────────────────
# Document types
# ──────────────────────────────────────────────────────────────────────
DOCUMENT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "demo_service": {
        "name_ru": "🗺 Визовая анкета",
        "name_uk": "🗺 Візова анкета",
        "name_en": "🗺 demo_service application",
        "price_pln": 150,
        "price_eur": 35,
        "fields": [
            Field("full_name", "👤 Full name (as in demo_document)", "text", max_length=255),
            Field("birth_date", "🎂 Date of birth (DD.MM.YYYY)", "date"),
            Field(
                "demo_document_ref",
                "🛂 demo_document number (series & number)",
                "demo_document_ref",
                max_length=30,
            ),
            Field(
                "destination_country",
                "🌍 Destination country (country code, e.g. PL, RU, RS, AM)",
                "country_code",
                max_length=2,
            ),
            Field(
                "purpose",
                "✈️ Purpose of visit (tourism / business / study / other)",
                "text",
                max_length=255,
            ),
        ],
        "example": (
            "Olena Romenko\n18.11.1996\nFB363261\nPL\ntourism"
        ),
    },
    "demo_document": {
        "name_ru": "🛂 Заграндокумент",
        "name_uk": "🛂 Заграндокумент",
        "name_en": "🛂 Foreign demo_document",
        "price_pln": 200,
        "price_eur": 45,
        "fields": [
            Field("full_name", "👤 Full name", "text", max_length=255),
            Field("birth_date", "🎂 Date of birth (DD.MM.YYYY)", "date"),
            Field("birth_place", "📍 Place of birth", "text", max_length=255),
            Field("address", "🏠 Residential address", "text", max_length=255),
        ],
    },
    "demo_check_check": {
        "name_ru": "📜 Справка о несудимости",
        "name_uk": "📜 Довідка про несудимість",
        "name_en": "📜 demo_check check",
        "price_pln": 100,
        "price_eur": 25,
        "fields": [
            Field("full_name", "👤 Full name", "text", max_length=255),
            Field("birth_date", "🎂 Date of birth (DD.MM.YYYY)", "date"),
            Field("birth_place", "📍 Place of birth", "text", max_length=255),
        ],
    },
    "apostille": {
        "name_ru": "📑 Апостиль",
        "name_uk": "📑 Апостиль",
        "name_en": "📑 Apostille",
        "price_pln": 120,
        "price_eur": 30,
        "fields": [
            Field("full_name", "👤 Full name", "text", max_length=255),
            Field("document_type", "📄 Type of document to apostille", "text", max_length=255),
            Field("issue_date", "📅 Date of issue (DD.MM.YYYY)", "date"),
            Field(
                "issuing_authority",
                "🏛 Issuing authority",
                "text",
                max_length=255,
            ),
        ],
    },
}

# ──────────────────────────────────────────────────────────────────────
ROUTING_KEYS: Dict[str, str] = {
    "demo_service": "ROUTING_demo_service",
    "demo_document": "ROUTING_demo_document",
    "demo_check_check": "ROUTING_demo_check",
    "apostille": "ROUTING_APOSTILLE",
}

DELIVERY_PRICE_PLN: int = 20
DELIVERY_PRICE_EUR: int = 5

PAYMENT_DETAILS: Dict[str, str] = {
    "card": "Bank transfer: PL00 0000 0000 0000 0000 0000 0000\n"
            "Recipient: Consular Services Ltd.",
    "crypto": "USDT (TRC20): TXYZ... (wallet address)",
    "online": "Online payment link will be provided by the manager.",
}


def get_template(doc_code: str) -> Dict[str, Any] | None:
    return DOCUMENT_TEMPLATES.get(doc_code)


def get_all_templates() -> List[tuple]:
    return [(k, v["name_en"]) for k, v in DOCUMENT_TEMPLATES.items()]


def get_price_pln(doc_code: str) -> int:
    tpl = DOCUMENT_TEMPLATES.get(doc_code)
    return tpl["price_pln"] if tpl else 0


def get_price_eur(doc_code: str) -> int:
    tpl = DOCUMENT_TEMPLATES.get(doc_code)
    return tpl["price_eur"] if tpl else 0
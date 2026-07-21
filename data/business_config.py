"""
Business configuration — the single source of truth for all domain-specific data.

This file contains:
- Document types, their fields, prices (PLN & EUR) and routing keys
- Allowed destination countries for visa applications
- Passport number format (regex pattern)
- Delivery price
- Payment details (placeholders)

Replace these values with your own business data when deploying.
"""

from typing import Any, Dict, List

from templates.fields import Field


# ──────────────────────────────────────────────────────────────────────
# Allowed destination countries (for visa / document travel fields)
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
# Passport number format (regex)
# ──────────────────────────────────────────────────────────────────────
PASSPORT_NUMBER_PATTERN: str = r"^[A-Z0-9\s\-\.\/]{3,30}$"


# ──────────────────────────────────────────────────────────────────────
# Currencies
# ──────────────────────────────────────────────────────────────────────
SUPPORTED_CURRENCIES: List[str] = ["EUR", "PLN"]


# ──────────────────────────────────────────────────────────────────────
# Document types
# ──────────────────────────────────────────────────────────────────────
DOCUMENT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "visa": {
        "name_ru": "🗺 Визовая анкета",
        "name_uk": "🗺 Візова анкета",
        "name_en": "🗺 Visa application",
        "price_pln": 150,
        "price_eur": 35,
        "fields": [
            Field("full_name", "👤 Full name (as in passport)", "text", max_length=255),
            Field("birth_date", "🎂 Date of birth (DD.MM.YYYY)", "date"),
            Field(
                "passport_number",
                "🛂 Passport number (series & number)",
                "passport_number",
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
    "passport": {
        "name_ru": "🛂 Загранпаспорт",
        "name_uk": "🛂 Загранпаспорт",
        "name_en": "🛂 Foreign passport",
        "price_pln": 200,
        "price_eur": 45,
        "fields": [
            Field("full_name", "👤 Full name", "text", max_length=255),
            Field("birth_date", "🎂 Date of birth (DD.MM.YYYY)", "date"),
            Field("birth_place", "📍 Place of birth", "text", max_length=255),
            Field("address", "🏠 Residential address", "text", max_length=255),
        ],
    },
    "criminal_record_check": {
        "name_ru": "📜 Справка о несудимости",
        "name_uk": "📜 Довідка про несудимість",
        "name_en": "📜 Criminal record check",
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
    "visa": "ROUTING_VISA",
    "passport": "ROUTING_PASSPORT",
    "criminal_record_check": "ROUTING_CRIMINAL_RECORD",
    "apostille": "ROUTING_APOSTILLE",
}

DELIVERY_PRICE_PLN: int = 20
DELIVERY_PRICE_EUR: int = 5

PAYMENT_DETAILS: Dict[str, str] = {
    "blik": "💳 Blik przelew na numer telefonu:\n"
            "Nr tel: +48 123 456 789\n"
            "Odbiorca: Consular Services Ltd.",
    "uah": "🇺🇦 Перевод на гривневую карту ПриватБанк:\n"
           "Карта: 5168 7456 3456 7890\n"
           "Получатель: Иванова А.",
    "usdt": "₿ USDT (TRC20): TXYZ... (wallet address)",
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
"""
Business configuration — the single source of truth for all domain-specific data.

This file contains:
- Document types, their fields, prices (PLN & EUR) and routing keys
- Delivery price
- Payment details (placeholders)

Replace these values with your own business data when deploying.
"""

from typing import Any, Dict, List

from templates.fields import Field


# ──────────────────────────────────────────────────────────────────────
# Document types
# ──────────────────────────────────────────────────────────────────────
# Each entry defines:
#   - code:         unique routing key (used in ROUTING dict, .env, callbacks)
#   - name_ru:      Russian display name
#   - name_uk:      Ukrainian display name
#   - name_en:      English display name
#   - fields:       list of input fields the customer must fill in
#   - example:      example filled-in data (shown as hint)
#   - price_pln:    unit price in Polish złoty
#   - price_eur:    unit price in Euros

DOCUMENT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "visa": {
        "name_ru": "🗺 Визовая анкета",
        "name_uk": "🗺 Візова анкета",
        "name_en": "🗺 Visa application",
        "price_pln": 150,
        "price_eur": 35,
        "fields": [
            Field("full_name", "👤 Full name (as in passport)", "text"),
            Field("birth_date", "🎂 Date of birth (DD.MM.YYYY)", "date"),
            Field(
                "passport_number",
                "🛂 Passport number (series & number)",
                "text",
            ),
            Field(
                "destination_country",
                "🌍 Destination country",
                "text",
            ),
            Field(
                "purpose",
                "✈️ Purpose of visit (tourism / business / study / other)",
                "text",
            ),
        ],
        "example": (
            "Olena Romenko\n18.11.1996\nFB363261\nPoland\ntourism"
        ),
    },
    "passport": {
        "name_ru": "🛂 Загранпаспорт",
        "name_uk": "🛂 Загранпаспорт",
        "name_en": "🛂 Foreign passport",
        "price_pln": 200,
        "price_eur": 45,
        "fields": [
            Field("full_name", "👤 Full name", "text"),
            Field("birth_date", "🎂 Date of birth (DD.MM.YYYY)", "date"),
            Field("birth_place", "📍 Place of birth", "text"),
            Field("address", "🏠 Residential address", "text"),
        ],
    },
    "criminal_record_check": {
        "name_ru": "📜 Справка о несудимости",
        "name_uk": "📜 Довідка про несудимість",
        "name_en": "📜 Criminal record check",
        "price_pln": 100,
        "price_eur": 25,
        "fields": [
            Field("full_name", "👤 Full name", "text"),
            Field("birth_date", "🎂 Date of birth (DD.MM.YYYY)", "date"),
            Field("birth_place", "📍 Place of birth", "text"),
        ],
    },
    "apostille": {
        "name_ru": "📑 Апостиль",
        "name_uk": "📑 Апостиль",
        "name_en": "📑 Apostille",
        "price_pln": 120,
        "price_eur": 30,
        "fields": [
            Field("full_name", "👤 Full name", "text"),
            Field("document_type", "📄 Type of document to apostille", "text"),
            Field("issue_date", "📅 Date of issue (DD.MM.YYYY)", "date"),
            Field(
                "issuing_authority",
                "🏛 Issuing authority",
                "text",
            ),
        ],
    },
}

# ──────────────────────────────────────────────────────────────────────
# Routing keys (maps document code → ROUTING key for .env)
# ──────────────────────────────────────────────────────────────────────
ROUTING_KEYS: Dict[str, str] = {
    "visa": "ROUTING_VISA",
    "passport": "ROUTING_PASSPORT",
    "criminal_record_check": "ROUTING_CRIMINAL_RECORD",
    "apostille": "ROUTING_APOSTILLE",
}

# ──────────────────────────────────────────────────────────────────────
# Delivery
# ──────────────────────────────────────────────────────────────────────
DELIVERY_PRICE_PLN: int = 20
DELIVERY_PRICE_EUR: int = 5

# ──────────────────────────────────────────────────────────────────────
# Payment details (placeholder — replace with real ones)
# ──────────────────────────────────────────────────────────────────────
PAYMENT_DETAILS: Dict[str, str] = {
    "card": "Bank transfer: PL00 0000 0000 0000 0000 0000 0000\n"
            "Recipient: Consular Services Ltd.",
    "crypto": "USDT (TRC20): TXYZ... (wallet address)",
    "online": "Online payment link will be provided by the manager.",
}


def get_template(doc_code: str) -> Dict[str, Any] | None:
    """Return the document template by its code, or *None* if not found."""
    return DOCUMENT_TEMPLATES.get(doc_code)


def get_all_templates() -> List[tuple]:
    """Return a list of (code, name_en) tuples for all active templates."""
    return [(k, v["name_en"]) for k, v in DOCUMENT_TEMPLATES.items()]


def get_price_pln(doc_code: str) -> int:
    """Return the PLN price for a document, or 0 if not found."""
    tpl = DOCUMENT_TEMPLATES.get(doc_code)
    return tpl["price_pln"] if tpl else 0


def get_price_eur(doc_code: str) -> int:
    """Return the EUR price for a document, or 0 if not found."""
    tpl = DOCUMENT_TEMPLATES.get(doc_code)
    return tpl["price_eur"] if tpl else 0
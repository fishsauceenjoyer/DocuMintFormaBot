"""
Business configuration — the single source of truth for all domain-specific data.

This file contains:
- Document types, their fields, prices (PLN & EUR) and routing keys
- Allowed destination countries for visa applications
- Passport number format (regex pattern)
- Delivery price
- Payment details (placeholders)

Document templates are loaded from ``config/templates.yaml`` so that business
users can edit them without touching Python code.
"""

import os
from typing import Any, Dict, List, Optional

import yaml

from templates.fields import Field

# ──────────────────────────────────────────────────────────────────────────
# YAML template loader
# ──────────────────────────────────────────────────────────────────────────
_TEMPLATES_PATH = os.path.join(
    os.path.dirname(__file__), "..", "config", "templates.yaml"
)


def _yaml_to_fields(field_list: List[dict]) -> List[Field]:
    """Convert a list of YAML field dicts into Field objects."""
    return [
        Field(
            id=f["id"],
            prompt=f["prompt"],
            field_type=f.get("type", "text"),
            optional=f.get("optional", False),
            max_length=f.get("max_length"),
        )
        for f in field_list
    ]


def _load_templates() -> Dict[str, Dict[str, Any]]:
    """Load and parse document templates from the YAML file.

    Returns:
        The same structure as the old hardcoded DOCUMENT_TEMPLATES dict
        (with ``Field`` objects in the ``"fields"`` key).
    """
    path = _TEMPLATES_PATH
    if not os.path.isfile(path):
        # Fallback to empty dict so the bot can start without the file
        return {}

    with open(path, encoding="utf-8") as fh:
        raw: dict = yaml.safe_load(fh) or {}

    templates: Dict[str, Dict[str, Any]] = {}
    for code, data in raw.items():
        templates[code] = {
            "name_ru": data.get("name_ru", ""),
            "name_uk": data.get("name_uk", ""),
            "name_en": data.get("name_en", ""),
            "price_pln": data.get("price_pln", 0),
            "price_eur": data.get("price_eur", 0),
            "fields": _yaml_to_fields(data.get("fields", [])),
            "example": data.get("example", ""),
        }
    return templates


# ──────────────────────────────────────────────────────────────────────────
# Allowed destination countries (for visa / document travel fields)
# ──────────────────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────────────────
# Passport number format (regex)
# ──────────────────────────────────────────────────────────────────────────
PASSPORT_NUMBER_PATTERN: str = r"^[A-Z0-9\s\-\.\/]{3,30}$"


# ──────────────────────────────────────────────────────────────────────────
# Currencies
# ──────────────────────────────────────────────────────────────────────────
SUPPORTED_CURRENCIES: List[str] = ["EUR", "PLN"]


# ──────────────────────────────────────────────────────────────────────────
# Document templates — loaded from YAML
# ──────────────────────────────────────────────────────────────────────────
DOCUMENT_TEMPLATES: Dict[str, Dict[str, Any]] = _load_templates()

# ──────────────────────────────────────────────────────────────────────────
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


def get_template(doc_code: str) -> Optional[Dict[str, Any]]:
    return DOCUMENT_TEMPLATES.get(doc_code)


def get_all_templates() -> List[tuple]:
    return [(k, v["name_en"]) for k, v in DOCUMENT_TEMPLATES.items()]


def get_price_pln(doc_code: str) -> int:
    tpl = DOCUMENT_TEMPLATES.get(doc_code)
    return tpl["price_pln"] if tpl else 0


def get_price_eur(doc_code: str) -> int:
    tpl = DOCUMENT_TEMPLATES.get(doc_code)
    return tpl["price_eur"] if tpl else 0
"""
Original business configuration — reference file (PD-clean).

⚠️  PD NOTE (Epic 1): this file previously contained the **original**
business data (sanepid, BHP, PESEL, psychotests) that collected personal
data — passport/PESEL numbers, birth dates, residential addresses.
All such documents were removed; only the demo poster configuration
(which collects no personal data) is kept as a frozen reference.

To switch to this configuration:
1. Rename this file to ``business_config.py`` (or update the import in
   ``templates/documents.py`` to point here instead).
2. Update ``.env`` variable names and chat IDs accordingly.
3. Reset ``locales/`` if needed.

This file is **not imported** by default — it exists as a reference.
"""

from typing import Any, Dict, List

from templates.fields import Field


# ──────────────────────────────────────────────────────────────────────
# Document types (demo posters only — no personal data)
# ──────────────────────────────────────────────────────────────────────

DOCUMENT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "poster_terminator1": {
        "name_ru": "🎬 Терминатор 1",
        "name_uk": "🎬 Термінатор 1",
        "name_en": "🎬 Terminator 1",
        "price_pln": 40,
        "price_eur": 10,
        "fields": [
            Field("size", "📐 Выберите размер постера", "choice"),
            Field("color", "🎨 Выберите цветность", "choice"),
            Field("quantity", "🔢 Количество экземпляров (1–5)", "integer"),
        ],
    },
    "poster_terminator2": {
        "name_ru": "🎬 Терминатор 2",
        "name_uk": "🎬 Термінатор 2",
        "name_en": "🎬 Terminator 2",
        "price_pln": 60,
        "price_eur": 15,
        "fields": [
            Field("size", "📐 Выберите размер постера", "choice"),
            Field("color", "🎨 Выберите цветность", "choice"),
            Field("quantity", "🔢 Количество экземпляров (1–5)", "integer"),
        ],
    },
    "poster_predator": {
        "name_ru": "🎬 Хищник",
        "name_uk": "🎬 Хижак",
        "name_en": "🎬 Predator",
        "price_pln": 80,
        "price_eur": 20,
        "fields": [
            Field("size", "📐 Выберите размер постера", "choice"),
            Field("color", "🎨 Выберите цветность", "choice"),
            Field("quantity", "🔢 Количество экземпляров (1–5)", "integer"),
        ],
    },
}

# ──────────────────────────────────────────────────────────────────────
# Routing keys (demo)
# ──────────────────────────────────────────────────────────────────────
ROUTING_KEYS: Dict[str, str] = {
    "poster_terminator1": "ROUTING_POSTER_TERMINATOR1",
    "poster_terminator2": "ROUTING_POSTER_TERMINATOR2",
    "poster_predator": "ROUTING_POSTER_PREDATOR",
}

# ──────────────────────────────────────────────────────────────────────
# Delivery (original — PLN only)
# ──────────────────────────────────────────────────────────────────────
DELIVERY_PRICE_PLN: int = 20
DELIVERY_PRICE_EUR: int = 5

# ──────────────────────────────────────────────────────────────────────
# Payment details (original)
# ──────────────────────────────────────────────────────────────────────
PAYMENT_DETAILS: Dict[str, str] = {
    "blik": "Номер телефона: +48 123 456 789",
    "uah": "ПриватБанк: 5168 7456 1234 5678\nПолучатель: Ivanov Ivan",
    "usdt": "TRC20: TXYZ... (кошелек)",
}


def get_template(doc_code: str) -> Dict[str, Any] | None:
    """Return the document template by its code, or *None* if not found."""
    return DOCUMENT_TEMPLATES.get(doc_code)


def get_all_templates() -> List[tuple]:
    """Return a list of (code, name) tuples for all active templates.

    Uses the Russian name as default display name.
    """
    return [(k, v["name_ru"]) for k, v in DOCUMENT_TEMPLATES.items()]


def get_price_pln(doc_code: str) -> int:
    """Return the PLN price for a document, or 0 if not found."""
    tpl = DOCUMENT_TEMPLATES.get(doc_code)
    return tpl["price_pln"] if tpl else 0


def get_price_eur(doc_code: str) -> int:
    """Return the EUR price for a document, or 0 if not found."""
    tpl = DOCUMENT_TEMPLATES.get(doc_code)
    return tpl["price_eur"] if tpl else 0
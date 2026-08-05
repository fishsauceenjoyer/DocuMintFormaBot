"""
Demo business configuration — poster printing services.

This is a **demo** config for presentations. It defines three poster-printing
services ("Терминатор 1", "Терминатор 2", "Хищник") with configurable fields:

- ``size``     — choice: A4 / A3 / A2
- ``color``    — choice: color / bw
- ``quantity`` — integer: 1–5

Pricing is computed as: base price (per film) + size surcharge + color surcharge.

To activate this config, rename it to ``business_config.py`` (or point the
import in ``templates/documents.py`` to this module). The original configs
(``business_config.py`` / ``business_config_original.py``) remain untouched.
"""

from typing import Any, Dict, List, Optional

from templates.fields import Field

# ──────────────────────────────────────────────────────────────────────
# Poster pricing — base price per film + surcharges per size/color
# ──────────────────────────────────────────────────────────────────────
POSTER_BASE_PRICE_EUR: Dict[str, int] = {
    "poster_terminator1": 10,
    "poster_terminator2": 15,
    "poster_predator": 20,
}

POSTER_BASE_PRICE_PLN: Dict[str, int] = {
    "poster_terminator1": 40,
    "poster_terminator2": 60,
    "poster_predator": 80,
}

# Surcharge per size (EUR / PLN)
POSTER_SIZE_SURCHARGE_EUR: Dict[str, int] = {"A4": 0, "A3": 5, "A2": 10}
POSTER_SIZE_SURCHARGE_PLN: Dict[str, int] = {"A4": 0, "A3": 20, "A2": 40}

# Surcharge per color mode (EUR / PLN)
POSTER_COLOR_SURCHARGE_EUR: Dict[str, int] = {"bw": 0, "color": 3}
POSTER_COLOR_SURCHARGE_PLN: Dict[str, int] = {"bw": 0, "color": 12}


def _poster_price(
    doc_code: str,
    base: Dict[str, int],
    size_surcharge: Dict[str, int],
    color_surcharge: Dict[str, int],
    size: Optional[str] = None,
    color: Optional[str] = None,
) -> int:
    """Compute a poster price from base + optional size/color surcharges."""
    price = base.get(doc_code, 0)
    if size:
        price += size_surcharge.get(size, 0)
    if color:
        price += color_surcharge.get(color, 0)
    return price


# ──────────────────────────────────────────────────────────────────────
# Document templates — poster printing services
# ──────────────────────────────────────────────────────────────────────
DOCUMENT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "poster_terminator1": {
        "name_ru": "🎬 Терминатор 1",
        "name_uk": "🎬 Термінатор 1",
        "name_en": "🎬 Terminator 1",
        "price_pln": POSTER_BASE_PRICE_PLN["poster_terminator1"],
        "price_eur": POSTER_BASE_PRICE_EUR["poster_terminator1"],
        "fields": [
            Field(
                "size",
                "📐 Выберите размер постера",
                "choice",
                choices=["A4", "A3", "A2"],
            ),
            Field(
                "color",
                "🎨 Выберите цветность",
                "choice",
                choices=["color", "bw"],
            ),
            Field(
                "quantity",
                "🔢 Количество экземпляров (1–5)",
                "integer",
                min_value=1,
                max_value=5,
            ),
        ],
        "example": "A4\ncolor\n2",
    },
    "poster_terminator2": {
        "name_ru": "🎬 Терминатор 2",
        "name_uk": "🎬 Термінатор 2",
        "name_en": "🎬 Terminator 2",
        "price_pln": POSTER_BASE_PRICE_PLN["poster_terminator2"],
        "price_eur": POSTER_BASE_PRICE_EUR["poster_terminator2"],
        "fields": [
            Field(
                "size",
                "📐 Выберите размер постера",
                "choice",
                choices=["A4", "A3", "A2"],
            ),
            Field(
                "color",
                "🎨 Выберите цветность",
                "choice",
                choices=["color", "bw"],
            ),
            Field(
                "quantity",
                "🔢 Количество экземпляров (1–5)",
                "integer",
                min_value=1,
                max_value=5,
            ),
        ],
        "example": "A3\ncolor\n1",
    },
    "poster_predator": {
        "name_ru": "🎬 Хищник",
        "name_uk": "🎬 Хижак",
        "name_en": "🎬 Predator",
        "price_pln": POSTER_BASE_PRICE_PLN["poster_predator"],
        "price_eur": POSTER_BASE_PRICE_EUR["poster_predator"],
        "fields": [
            Field(
                "size",
                "📐 Выберите размер постера",
                "choice",
                choices=["A4", "A3", "A2"],
            ),
            Field(
                "color",
                "🎨 Выберите цветность",
                "choice",
                choices=["color", "bw"],
            ),
            Field(
                "quantity",
                "🔢 Количество экземпляров (1–5)",
                "integer",
                min_value=1,
                max_value=5,
            ),
        ],
        "example": "A2\nbw\n3",
    },
}

# ──────────────────────────────────────────────────────────────────────
# Routing keys (demo — all posters go to the default manager chat)
# ──────────────────────────────────────────────────────────────────────
ROUTING_KEYS: Dict[str, str] = {
    "poster_terminator1": "ROUTING_POSTER_TERMINATOR1",
    "poster_terminator2": "ROUTING_POSTER_TERMINATOR2",
    "poster_predator": "ROUTING_POSTER_PREDATOR",
}

# ──────────────────────────────────────────────────────────────────────
# Delivery (same as active config)
# ──────────────────────────────────────────────────────────────────────
DELIVERY_PRICE_PLN: int = 20
DELIVERY_PRICE_EUR: int = 5

# ──────────────────────────────────────────────────────────────────────
# Payment details (same as active config)
# ──────────────────────────────────────────────────────────────────────
PAYMENT_DETAILS: Dict[str, str] = {
    "blik": "💳 Blik перевод на номер телефона:\n"
            "Номер: +48 123 456 789\n"
            "Получатель: Consular Services Ltd.",
    "uah": "🇺🇦 Перевод на гривневую карту ПриватБанк:\n"
           "Карта: 5168 7456 3456 7890\n"
           "Получатель: Иванова А.",
    "usdt": "₿ USDT (TRC20): TXYZ... (адрес кошелька)",
}


def get_template(doc_code: str) -> Optional[Dict[str, Any]]:
    """Return the document template by its code, or *None* if not found."""
    return DOCUMENT_TEMPLATES.get(doc_code)


def get_all_templates() -> List[tuple]:
    """Return a list of (code, name) tuples for all active templates."""
    return [(k, v["name_ru"]) for k, v in DOCUMENT_TEMPLATES.items()]


def get_price_pln(
    doc_code: str,
    size: Optional[str] = None,
    color: Optional[str] = None,
) -> int:
    """Return the PLN price for a poster, optionally adjusted by size/color."""
    return _poster_price(
        doc_code,
        POSTER_BASE_PRICE_PLN,
        POSTER_SIZE_SURCHARGE_PLN,
        POSTER_COLOR_SURCHARGE_PLN,
        size=size,
        color=color,
    )


def get_price_eur(
    doc_code: str,
    size: Optional[str] = None,
    color: Optional[str] = None,
) -> int:
    """Return the EUR price for a poster, optionally adjusted by size/color."""
    return _poster_price(
        doc_code,
        POSTER_BASE_PRICE_EUR,
        POSTER_SIZE_SURCHARGE_EUR,
        POSTER_COLOR_SURCHARGE_EUR,
        size=size,
        color=color,
    )
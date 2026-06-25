"""
Original business configuration — reference file.

This file contains the **original** business data (sanepid, BHP, PESEL, psychotests,
etc.) that was replaced by the demo "consular services" config.

To switch back to the original configuration:
1. Rename this file to ``business_config.py`` (or update the import in
   ``templates/documents.py`` to point here instead).
2. Update ``.env`` variable names (ROUTING_VISA → ROUTING_SANEPID etc.)
   and chat IDs accordingly.
3. Reset ``locales/`` if needed.

⚠️  This file is **not imported** by default — it exists as a reference
   so you can restore the original data at any time.
"""

from typing import Any, Dict, List

from templates.fields import Field


# ──────────────────────────────────────────────────────────────────────
# Document types  (original — sanepid, BHP, psychotests, PESEL)
# ──────────────────────────────────────────────────────────────────────

DOCUMENT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "sanepid": {
        "name_ru": "📑 Санэпид / СК",
        "name_uk": "📑 Санэпід / СК",
        "name_en": "📑 Sanepid / Health certificate",
        "price_pln": 150,
        "price_eur": 35,
        "fields": [
            Field("date", "📅 Дата изготовления (не выходной/праздник)", "date"),
            Field("full_name", "👤 Фамилия и имя как в загранпаспорте", "text"),
            Field("birth_date", "🎂 Дата рождения (ДД.ММ.ГГГГ)", "date"),
            Field("pesel", "🆔 PESEL или серия/номер паспорта", "text"),
            Field(
                "address",
                "🏠 Полный адрес проживания (индекс, город, улица, квартира)",
                "text",
            ),
            Field(
                "workplace",
                "🏢 Место работы (если нет - поставьте '-')",
                "optional_text",
                optional=True,
            ),
            Field(
                "position",
                "💼 Должность (если нет - поставьте '-')",
                "optional_text",
                optional=True,
            ),
        ],
        "example": (
            "02.01.2025\nOlena Romenko\n18.11.1996\nFB363261\n"
            "Kraków, 89-510, ul. Senkiewicza 1/12\nROXI SP.Z O.O.\nSprzedawca"
        ),
    },
    "bhp": {
        "name_ru": "⛑ BHP",
        "name_uk": "⛑ BHP",
        "name_en": "⛑ BHP / Occupational safety",
        "price_pln": 100,
        "price_eur": 25,
        "fields": [
            Field("full_name", "👤 ФИО", "text"),
            Field("pesel", "🆔 PESEL", "text"),
            Field("position", "💼 Должность", "text"),
        ],
    },
    "psychotests": {
        "name_ru": "🚕 Психотесты для водителей",
        "name_uk": "🚕 Психотести для водіїв",
        "name_en": "🚕 Psychotests for drivers",
        "price_pln": 120,
        "price_eur": 30,
        "fields": [
            Field("full_name", "👤 ФИО водителя", "text"),
            Field("license_number", "📘 Номер удостоверения", "text"),
        ],
    },
    "pesel": {
        "name_ru": "🧧 PESEL без присутствия",
        "name_uk": "🧧 PESEL без присутності",
        "name_en": "🧧 PESEL without presence",
        "price_pln": 200,
        "price_eur": 45,
        "fields": [
            Field("full_name", "👤 ФИО", "text"),
            Field("birth_date", "🎂 Дата рождения", "date"),
            Field("parents_names", "👪 Имена родителей", "text"),
        ],
    },
}

# ──────────────────────────────────────────────────────────────────────
# Routing keys (original)
# ──────────────────────────────────────────────────────────────────────
ROUTING_KEYS: Dict[str, str] = {
    "sanepid": "ROUTING_SANEPID",
    "bhp": "ROUTING_BHP",
    "psychotests": "ROUTING_PSYCHOTESTS",
    "pesel": "ROUTING_PESEL",
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
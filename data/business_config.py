"""
Business configuration — the single source of truth for all domain-specific data.

This module loads business configuration from YAML files (``configs/base.yaml``
and ``configs/services.yaml``) via :class:`config.loader.BusinessConfigLoader`
and exposes the same module-level constants and helper functions as before,
so existing imports in handlers and tests keep working without changes.

Document templates are loaded from YAML so that business users can edit them
without touching Python code.
"""

from typing import Any, Dict, List, Optional

from config.loader import BusinessConfigLoader, get_loader
from templates.fields import Field

# ──────────────────────────────────────────────────────────────────────────
# Loader
# ──────────────────────────────────────────────────────────────────────────
_loader: BusinessConfigLoader = get_loader()


def reload_config() -> None:
    """Reload the business configuration from YAML files.

    Useful for hot-reloading after editing ``configs/*.yaml`` without
    restarting the bot.
    """
    global _loader
    _loader = BusinessConfigLoader()
    _loader.load_defaults()


# ──────────────────────────────────────────────────────────────────────────
# Allowed destination countries (for visa / document travel fields)
# ──────────────────────────────────────────────────────────────────────────
COUNTRY_CODES: Dict[str, Dict[str, str]] = (
    _loader.base.countries if _loader.base else {}
)

ALLOWED_COUNTRIES_HINT: str = " / ".join(
    f"{v['en']} ({k})" for k, v in COUNTRY_CODES.items()
)

DESTINATION_COUNTRIES: List[str] = list(COUNTRY_CODES.keys())


# ──────────────────────────────────────────────────────────────────────────
# Currencies
# ──────────────────────────────────────────────────────────────────────────
SUPPORTED_CURRENCIES: List[str] = (
    list(_loader.base.currencies.get("supported", ["EUR", "PLN"]))
    if _loader.base
    else ["EUR", "PLN"]
)


# ──────────────────────────────────────────────────────────────────────────
# Document templates — loaded from YAML via the loader
# ──────────────────────────────────────────────────────────────────────────
def _service_to_template(service: Any) -> Dict[str, Any]:
    """Convert a ServiceConfig dataclass into the legacy template dict."""
    fields = []
    for f in service.fields:
        fields.append(
            Field(
                id=f.id,
                prompt=f.prompt,
                field_type=f.type,
                optional=f.optional,
                max_length=f.max_length,
                choices=f.choices,
                min_value=f.min,
                max_value=f.max,
            )
        )
    return {
        "name_ru": service.name.get("ru", ""),
        "name_uk": service.name.get("uk", ""),
        "name_en": service.name.get("en", ""),
        "price_pln": _loader.get_price(service.id, "PLN"),
        "price_eur": _loader.get_price(service.id, "EUR"),
        "fields": fields,
        "example": "",
    }


DOCUMENT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    service.id: _service_to_template(service)
    for service in _loader.get_all_services()
}

# ──────────────────────────────────────────────────────────────────────────
ROUTING_KEYS: Dict[str, str] = (
    dict(_loader.base.routing_keys) if _loader.base else {}
)

DELIVERY_PRICE_PLN: int = (
    int(_loader.base.delivery["price"]["PLN"]) if _loader.base else 20
)
DELIVERY_PRICE_EUR: int = (
    int(_loader.base.delivery["price"]["EUR"]) if _loader.base else 5
)

PAYMENT_DETAILS: Dict[str, str] = (
    dict(_loader.base.payment_methods) if _loader.base else {}
)


def get_template(doc_code: str) -> Optional[Dict[str, Any]]:
    return DOCUMENT_TEMPLATES.get(doc_code)


def get_all_templates() -> List[tuple]:
    return [(k, v["name_ru"]) for k, v in DOCUMENT_TEMPLATES.items()]


def get_price_pln(doc_code: str) -> int:
    tpl = DOCUMENT_TEMPLATES.get(doc_code)
    return tpl["price_pln"] if tpl else 0


def get_price_eur(doc_code: str) -> int:
    tpl = DOCUMENT_TEMPLATES.get(doc_code)
    return tpl["price_eur"] if tpl else 0
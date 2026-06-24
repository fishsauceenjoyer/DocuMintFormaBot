"""Document catalog — thin wrapper around :mod:`data.business_config`.

This module re-exports the helpers from the business configuration so that
existing imports in handlers keep working without changes.
"""

from data.business_config import (
    DOCUMENT_TEMPLATES,
    ROUTING_KEYS,
    get_all_templates,
    get_price_eur,
    get_price_pln,
    get_template as _get_template,
)
from templates.fields import Field

__all__ = [
    "DOCUMENT_TEMPLATES",
    "Field",
    "ROUTING_KEYS",
    "get_all_templates",
    "get_price_eur",
    "get_price_pln",
    "get_template",
]


# Re-export for external usage
get_template = _get_template


def get_template_price(doc_type: str) -> int:
    """Return the PLN price for a document (backwards-compatible name)."""
    return get_price_pln(doc_type)

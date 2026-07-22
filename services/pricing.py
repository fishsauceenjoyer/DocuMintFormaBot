"""Order pricing helpers.

Everything related to price calculation lives here: document unit prices,
delivery surcharge, cart totals. Handlers should not duplicate this math.
"""

from typing import List

from config import DELIVERY_PRICE_EUR, DELIVERY_PRICE_PLN

DEFAULT_CURRENCY = "EUR"


def currency_symbol(currency: str) -> str:
    return "€" if currency == "EUR" else "zł"


def document_price(currency: str, doc_code: str) -> int:
    """Return the price for one document unit in the requested currency."""
    from data.business_config import get_price_eur, get_price_pln

    if currency == "EUR":
        return get_price_eur(doc_code)
    return get_price_pln(doc_code)


def delivery_price(currency: str) -> int:
    return DELIVERY_PRICE_EUR if currency == "EUR" else DELIVERY_PRICE_PLN


def calculate_total(
    items: List[dict], delivery: dict | None, currency: str = DEFAULT_CURRENCY
) -> int:
    """Calculate order total including optional delivery surcharge.

    Args:
        items: Cart items, each with keys: type, quantity.
        delivery: Delivery details dict or None for pickup.
        currency: Currency code ('EUR' or 'PLN').

    Returns:
        Total price in minor units (zł/€).
    """
    total = 0
    for item in items:
        price = document_price(currency, item["type"])
        total += price * item.get("quantity", 1)

    if delivery:
        total += delivery_price(currency)

    return total
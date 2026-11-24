"""Tests for order currency persistence (EUR/PLN)."""

import pytest
from sqlalchemy import select

from db.models import Order
from db.crud import create_order, get_order_by_id


@pytest.mark.asyncio
async def test_create_order_with_eur_currency(mock_order_db):
    """Test creating an order with EUR currency."""
    order_data = {
        "order_id": "ORDER_20261124_0001",
        "user_id": 1,
        "total_price": 1500,
        "currency": "EUR",
        "status": "paid",
    }
    order = await create_order(
        db=mock_order_db,
        order_id=order_data["order_id"],
        user_id=order_data["user_id"],
        total_price=order_data["total_price"],
        currency=order_data["currency"],
        status=order_data["status"],
    )
    assert order.currency == "EUR"


@pytest.mark.asyncio
async def test_create_order_with_pln_currency(mock_order_db):
    """Test creating an order with PLN currency."""
    order_data = {
        "order_id": "ORDER_20261124_0002",
        "user_id": 1,
        "total_price": 500,
        "currency": "PLN",
        "status": "paid",
    }
    order = await create_order(
        db=mock_order_db,
        order_id=order_data["order_id"],
        user_id=order_data["user_id"],
        total_price=order_data["total_price"],
        currency=order_data["currency"],
        status=order_data["status"],
    )
    assert order.currency == "PLN"


@pytest.mark.asyncio
async def test_get_order_by_id_currency(mock_order_db):
    """Test retrieving order by ID preserves currency."""
    order_data = {
        "order_id": "ORDER_20261124_0003",
        "user_id": 1,
        "total_price": 2000,
        "currency": "PLN",
        "status": "pending",
    }
    await create_order(
        db=mock_order_db,
        order_id=order_data["order_id"],
        user_id=order_data["user_id"],
        total_price=order_data["total_price"],
        currency=order_data["currency"],
        status=order_data["status"],
    )
    retrieved = await get_order_by_id(db=mock_order_db, order_id=order_data["order_id"])
    assert retrieved is not None
    assert retrieved.currency == "PLN"


@pytest.mark.asyncio
async def test_default_currency_is_eur(mock_order_db):
    """Test that default currency is EUR when not specified."""
    order_data = {
        "order_id": "ORDER_20261124_0004",
        "user_id": 1,
        "total_price": 1000,
        "status": "pending",
        # currency not specified - should default to EUR
    }
    order = await create_order(
        db=mock_order_db,
        order_id=order_data["order_id"],
        user_id=order_data["user_id"],
        total_price=order_data["total_price"],
        status=order_data["status"],
    )
    assert order.currency == "EUR"

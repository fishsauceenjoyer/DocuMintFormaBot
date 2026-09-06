"""Tests for services/ module: pricing, order_builder, order_manager."""

import pytest

from services import order_builder, order_manager, pricing


@pytest.fixture
async def clean_order_manager_db(monkeypatch):
    """Patch AsyncSessionLocal in order_manager to use a clean in-memory DB."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from db.models import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    TestSession = async_sessionmaker(engine, expire_on_commit=False)

    import services.order_manager as om

    monkeypatch.setattr(om, "AsyncSessionLocal", TestSession)
    return TestSession


class TestPricing:
    def test_currency_symbol_eur(self):
        assert pricing.currency_symbol("EUR") == "€"

    def test_currency_symbol_pln(self):
        assert pricing.currency_symbol("PLN") == "zł"

    def test_document_price_eur(self):
        # poster_terminator1 is one of the demo templates
        price = pricing.document_price("EUR", "poster_terminator1")
        assert isinstance(price, int)
        assert price > 0

    def test_document_price_pln(self):
        price = pricing.document_price("PLN", "poster_terminator1")
        assert isinstance(price, int)
        assert price > 0

    def test_delivery_price_eur(self):
        assert pricing.delivery_price("EUR") > 0

    def test_delivery_price_pln(self):
        assert pricing.delivery_price("PLN") > 0

    def test_calculate_total_without_delivery(self):
        items = [{"type": "poster_terminator1", "quantity": 2}]
        total = pricing.calculate_total(items, delivery=None, currency="EUR")
        assert total == pricing.document_price("EUR", "poster_terminator1") * 2

    def test_calculate_total_with_delivery(self):
        items = [{"type": "poster_terminator1", "quantity": 1}]
        total = pricing.calculate_total(
            items, delivery={"name": "Test"}, currency="EUR"
        )
        expected = pricing.document_price(
            "EUR", "poster_terminator1"
        ) + pricing.delivery_price("EUR")
        assert total == expected

    def test_calculate_total_empty_cart(self):
        assert pricing.calculate_total([], delivery=None, currency="EUR") == 0
        assert pricing.calculate_total(
            [], delivery={"name": "Test"}, currency="PLN"
        ) == pricing.delivery_price("PLN")


class TestOrderBuilder:
    def test_build_manager_message_required_keys(self):
        order_data = {
            "order_id": "ORDER_123456",
            "user": {"id": 123, "username": "testuser"},
            "documents": [
                {
                    "type": "poster_terminator1",
                    "quantity": 1,
                    "items": [{"full_name": "John Doe"}],
                }
            ],
            "delivery": None,
            "total_price": 150,
            "currency": "EUR",
            "payment_method": "blik",
        }
        text = order_builder.build_manager_message(order_data)
        assert "NEW ORDER #ORDER_123456" in text
        assert "John Doe" in text
        assert "150" in text
        assert "Pickup (no delivery)" in text

    def test_build_manager_message_with_delivery(self):
        order_data = {
            "order_id": "ORDER_999999",
            "user": {"id": 321, "username": None},
            "documents": [
                {
                    "type": "poster_terminator2",
                    "quantity": 2,
                    "items": [{"first": "A", "second": "B"}],
                }
            ],
            "delivery": {
                "name": "Alice",
                "phone": "123",
                "email": "a@b.com",
                "address": "Street 1",
            },
            "total_price": 400,
            "currency": "PLN",
            "payment_method": "uah",
        }
        text = order_builder.build_manager_message(order_data)
        assert "NEW ORDER #ORDER_999999" in text
        assert "Delivery:" in text
        assert "Alice" in text
        assert "Pickup (no delivery)" not in text


class TestOrderManager:
    @pytest.mark.asyncio
    async def test_create_and_get_order(self, clean_order_manager_db):
        manager = order_manager.OrderManager()
        order_data = {
            "order_id": "ORDER_UNIT_1",
            "user_id": 1,
            "total_price": 120,
            "status": "pending",
            "payment_method": "usdt",
            "payment_proof_file_id": None,
            "delivery": {
                "name": "Bob",
                "phone": "999",
                "email": "bob@example.com",
                "address": "Main 1",
            },
            "documents": [
                {
                    "type": "poster_terminator1",
                    "quantity": 1,
                    "items": [{"full_name": "Bob"}],
                }
            ],
            "items": [
                {
                    "type": "poster_terminator1",
                    "quantity": 1,
                    "unit_price": 120,
                    "data": {"full_name": "Bob"},
                }
            ],
        }
        order = await manager.create_order(order_data)
        assert order.id is not None
        assert order.status == "pending"

        fetched = await manager.get_order("ORDER_UNIT_1")
        assert fetched is not None
        assert fetched.id == order.id

    @pytest.mark.asyncio
    async def test_update_status_changes_status(self, clean_order_manager_db):
        manager = order_manager.OrderManager()
        order_data = {
            "order_id": "ORDER_UNIT_2",
            "user_id": 2,
            "total_price": 50,
            "status": "pending",
            "payment_method": None,
            "payment_proof_file_id": None,
            "delivery": None,
            "documents": [],
            "items": [],
        }
        order = await manager.create_order(order_data)
        assert order.status == "pending"

        updated = await manager.update_status("ORDER_UNIT_2", "paid")
        assert updated is not None
        assert updated.status == "paid"

    @pytest.mark.asyncio
    async def test_get_order_missing_returns_none(self, clean_order_manager_db):
        manager = order_manager.OrderManager()
        assert await manager.get_order("ORDER_MISSING") is None

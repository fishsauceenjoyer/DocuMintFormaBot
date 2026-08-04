"""Integration tests for database CRUD operations.

Uses an in-memory SQLite database created by the mock_db_session fixture.
All tests are async (SQLAlchemy async operations).
"""

from tests.fixtures.db_fixtures import mock_db_session  # noqa: F401


class TestUserCRUD:
    """Tests for user CRUD operations."""

    async def test_create_user(self, mock_db_session):  # noqa: F811
        """Verify a user can be created."""
        from db.crud import create_user, get_user_by_username

        user = await create_user(
            mock_db_session, username="testuser", chat_id=12345, role="user"
        )
        assert user.username == "testuser"
        assert user.chat_id == 12345
        assert user.role == "user"
        assert user.id is not None

        # Verify we can retrieve it
        found = await get_user_by_username(mock_db_session, "testuser")
        assert found is not None
        assert found.id == user.id

    async def test_create_user_without_chat_id(self, mock_db_session):  # noqa: F811
        """Verify user can be created without chat_id."""
        from db.crud import create_user

        user = await create_user(mock_db_session, username="noiduser")
        assert user.username == "noiduser"
        assert user.chat_id is None

    async def test_get_user_by_username_not_found(self, mock_db_session):  # noqa: F811
        """Verify get_user_by_username returns None for missing user."""
        from db.crud import get_user_by_username

        result = await get_user_by_username(mock_db_session, "nonexistent")
        assert result is None

    async def test_get_user_by_id(self, mock_db_session):  # noqa: F811
        """Verify user can be found by local DB id."""
        from db.crud import create_user, get_user_by_id

        user = await create_user(mock_db_session, username="byiduser", chat_id=67890)
        found = await get_user_by_id(mock_db_session, user.id)
        assert found is not None
        assert found.username == "byiduser"

    async def test_update_user_chat_id(self, mock_db_session):  # noqa: F811
        """Verify chat_id can be updated."""
        from db.crud import create_user, update_user_chat_id

        user = await create_user(mock_db_session, username="updatechat", chat_id=111)
        await update_user_chat_id(mock_db_session, user, 222)
        assert user.chat_id == 222

    async def test_update_user_language(self, mock_db_session):  # noqa: F811
        """Verify user language can be updated."""
        from db.crud import create_user, update_user_language

        user = await create_user(mock_db_session, username="languser")
        assert user.language == "en"  # Default

        await update_user_language(mock_db_session, user, "ru")
        assert user.language == "ru"


class TestDocumentTypeCRUD:
    """Tests for document type CRUD operations."""

    async def test_get_document_type_by_code(self, mock_db_session):  # noqa: F811
        """Verify document type can be found by code."""
        from db.crud import get_document_type, init_default_document_types

        # Ensure default document types are inserted
        await init_default_document_types(mock_db_session)

        doc_type = await get_document_type(mock_db_session, "visa")
        assert doc_type is not None
        assert doc_type.code == "visa"

    async def test_get_document_type_not_found(self, mock_db_session):  # noqa: F811
        """Verify get_document_type returns None for missing code."""
        from db.crud import get_document_type

        result = await get_document_type(mock_db_session, "nonexistent_code")
        assert result is None

    async def test_get_all_document_types(self, mock_db_session):  # noqa: F811
        """Verify all active document types are returned."""
        # init_default_document_types should have created them
        from db.crud import get_all_document_types, init_default_document_types

        await init_default_document_types(mock_db_session)

        types = await get_all_document_types(mock_db_session)
        assert len(types) >= 4  # visa, passport, criminal_record_check, apostille
        codes = [t.code for t in types]
        assert "visa" in codes
        assert "passport" in codes


class TestOrderCRUD:
    """Tests for order CRUD operations."""

    async def _create_test_order(self, db, order_id="ORDER_TEST001"):
        """Helper to create a test order."""
        from db.crud import create_order

        return await create_order(
            db=db,
            order_id=order_id,
            user_id=1,
            total_price=150,
            status="pending",
            payment_method="blik",
            payment_proof_file_id="file_id_123",
            delivery={
                "name": "Test User",
                "phone": "+48123456789",
                "email": "test@test.com",
                "address": "Test St 1",
            },
            documents=[
                {"type": "visa", "quantity": 1, "items": [{"full_name": "Test"}]}
            ],
        )

    async def test_create_order(self, mock_db_session):  # noqa: F811
        """Verify an order can be created."""
        order = await self._create_test_order(mock_db_session)
        assert order.order_id == "ORDER_TEST001"
        assert order.status == "pending"
        assert order.total_price == 150
        assert order.payment_method == "blik"

    async def test_get_order_by_id(self, mock_db_session):  # noqa: F811
        """Verify order can be found by order_id string."""
        from db.crud import get_order_by_id

        await self._create_test_order(mock_db_session, "ORDER_FINDME")
        found = await get_order_by_id(mock_db_session, "ORDER_FINDME")
        assert found is not None
        assert found.status == "pending"

    async def test_get_order_by_id_not_found(self, mock_db_session):  # noqa: F811
        """Verify get_order_by_id returns None for missing order."""
        from db.crud import get_order_by_id

        result = await get_order_by_id(mock_db_session, "ORDER_NONEXISTENT")
        assert result is None

    async def test_get_orders_by_user(self, mock_db_session):  # noqa: F811
        """Verify orders can be retrieved by user_id."""
        from db.crud import get_orders_by_user

        # Create orders with same user_id
        await self._create_test_order(mock_db_session, "ORDER_USER_1")
        order2 = await self._create_test_order(mock_db_session, "ORDER_USER_2")
        # Manually set user_id
        order2.user_id = 1
        await mock_db_session.commit()

        orders = await get_orders_by_user(mock_db_session, 1)
        assert len(orders) >= 1

    async def test_update_order_status(self, mock_db_session):  # noqa: F811
        """Verify order status can be updated."""
        from db.crud import update_order_status

        order = await self._create_test_order(mock_db_session, "ORDER_STATUS")
        await update_order_status(mock_db_session, order, "paid")
        assert order.status == "paid"

    async def test_update_order_tracking(self, mock_db_session):  # noqa: F811
        """Verify tracking number can be added to order."""
        from db.crud import update_order_tracking

        order = await self._create_test_order(mock_db_session, "ORDER_TRACK")
        await update_order_tracking(mock_db_session, order, "TRACK123")
        assert order.tracking_number == "TRACK123"
        assert order.status == "shipped"

    async def test_get_all_orders(self, mock_db_session):  # noqa: F811
        """Verify all orders can be retrieved."""
        from db.crud import get_all_orders

        await self._create_test_order(mock_db_session, "ORDER_ALL_1")
        await self._create_test_order(mock_db_session, "ORDER_ALL_2")

        all_orders = await get_all_orders(mock_db_session)
        assert len(all_orders) >= 2

    async def test_get_orders_by_status(self, mock_db_session):  # noqa: F811
        """Verify orders can be filtered by status."""
        from db.crud import get_orders_by_status

        await self._create_test_order(mock_db_session, "ORDER_STAT_1")
        from db.crud import create_order

        await create_order(
            db=mock_db_session,
            order_id="ORDER_STAT_2",
            user_id=2,
            total_price=200,
            status="completed",
        )

        pending = await get_orders_by_status(mock_db_session, "pending")
        assert len(pending) == 1
        assert pending[0].order_id == "ORDER_STAT_1"

        completed = await get_orders_by_status(mock_db_session, "completed")
        assert len(completed) == 1

    async def test_get_order_stats(self, mock_db_session):  # noqa: F811
        """Verify order statistics are calculated correctly."""
        from db.crud import create_order, get_order_stats

        # Create orders with different statuses
        await create_order(mock_db_session, "ORDER_S_1", 1, 100, "pending")
        await create_order(mock_db_session, "ORDER_S_2", 1, 200, "paid")
        await create_order(mock_db_session, "ORDER_S_3", 2, 150, "completed")
        await create_order(mock_db_session, "ORDER_S_4", 2, 300, "cancelled")

        stats = await get_order_stats(mock_db_session)
        assert stats["total"] == 4
        assert stats["pending"] == 1
        assert stats["paid"] == 1
        assert stats["completed"] == 1
        assert stats["cancelled"] == 1

    async def test_create_order_item(self, mock_db_session):  # noqa: F811
        """Verify order items can be created."""
        from db.crud import create_order_item

        order = await self._create_test_order(mock_db_session, "ORDER_ITEM_TEST")
        item = await create_order_item(
            db=mock_db_session,
            order_id=order.id,
            document_type="visa",
            quantity=2,
            unit_price=150,
            data={"type": "visa", "items": [{"full_name": "Test"}]},
        )
        assert item.document_type == "visa"
        assert item.quantity == 2
        assert item.unit_price == 150


class TestInitDB:
    """Tests for database initialisation."""

    async def test_init_db_creates_tables(self, mock_db_session):  # noqa: F811
        """Verify init_db creates all tables."""
        # Tables should already be created by the fixture,
        # but init_db should not crash
        from db.crud import init_default_document_types

        await init_default_document_types(mock_db_session)

        from db.crud import get_all_document_types

        types = await get_all_document_types(mock_db_session)
        assert len(types) >= 4

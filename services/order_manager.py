"""Order persistence and status transitions.

Wraps db.crud operations so handlers/domain code never import SQLAlchemy
directly. This keeps business logic testable and decoupled from ORM details.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from db.crud import (
    AsyncSessionLocal,
    create_order,
    create_order_item,
    get_order_by_id,
)
from db.models import Order


class OrderManager:
    """High-level order API used by handlers and future services."""

    async def create_order(self, order_data: dict) -> Order:
        """Create order header plus line items in one transaction.

        Args:
            order_data: Payload with keys matching db.crud.create_order().

        Returns:
            Created Order ORM instance.
        """
        async with AsyncSessionLocal() as db:
            order = await create_order(
                db=db,
                order_id=order_data["order_id"],
                user_id=order_data["user_id"],
                total_price=order_data.get("total_price", 0),
                status=order_data.get("status", "pending"),
                payment_method=order_data.get("payment_method"),
                payment_proof_file_id=order_data.get("payment_proof_file_id"),
                delivery=order_data.get("delivery"),
                documents=order_data.get("documents"),
            )

            for item in order_data.get("items", []):
                await create_order_item(
                    db=db,
                    order_id=order.id,
                    document_type=item["type"],
                    quantity=item.get("quantity", 1),
                    unit_price=item.get("unit_price", 0),
                    data=item.get("data"),
                )

            await db.commit()
            await db.refresh(order)
            return order

    async def update_status(self, order_number: str, status: str) -> Optional[Order]:
        """Update order status by order_id string.

        Args:
            order_number: External order ID like ORDER_XXXXXX.
            status: New status string.

        Returns:
            Updated Order or None if not found.
        """
        async with AsyncSessionLocal() as db:
            order = await get_order_by_id(db, order_number)
            if not order:
                return None
            order.status = status
            order.updated_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(order)
            return order

    async def get_order(self, order_number: str) -> Optional[Order]:
        """Fetch order by external order_id.

        Args:
            order_number: External order ID like ORDER_XXXXXX.

        Returns:
            Order instance or None.
        """
        async with AsyncSessionLocal() as db:
            return await get_order_by_id(db, order_number)

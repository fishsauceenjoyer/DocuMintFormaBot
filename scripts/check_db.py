"""Database inspection helper for local development.

Usage:
    uv run python scripts/check_db.py

This script prints the total number of orders and the last 5 orders
from the local SQLite database (bot.db). It is intended for quick
sanity checks after manual Telegram testing.
"""

import sys
from pathlib import Path

# Ensure project root is on path when running script directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.crud import SessionLocal, get_all_orders  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        orders = get_all_orders(db)
        print(f"Total orders: {len(orders)}\n")
        print("Last 5 orders:")
        print("-" * 80)
        for order in orders[-5:]:
            print(
                f"  {order.order_id} | status={order.status} | "
                f"total={order.total_price} | created={order.created_at}"
            )
        print("-" * 80)
    finally:
        db.close()


if __name__ == "__main__":
    main()
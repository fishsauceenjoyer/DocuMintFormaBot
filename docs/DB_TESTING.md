# Database Testing Guide

This guide shows how to verify that orders are saved correctly to the database after manual or automated testing.

## Prerequisites

- Bot is configured with `.env`
- Dependencies are installed: `uv sync`
- At least one order has been created through the bot

## Quick check with Python script

We provide a ready-to-run helper script that prints the latest orders from the SQLite database.

```bash
uv run python scripts/check_db.py
```

Expected output:

```
Total orders: 7
Last 5 orders:
  ORDER_20260803_EC90 | paid | 25 EUR | 2026-08-03 18:37
  ORDER_20260728_C24B | paid | 35 EUR | 2026-07-28 17:03
  ...
```

## Manual SQL check

If you want to inspect the database directly, you can use the `sqlite3` CLI or any SQLite browser.

```bash
# Open the database file
sqlite3 bot.db
```

Example queries:

```sql
-- Count all orders
SELECT COUNT(*) FROM orders;

-- Show the last 10 orders with basic info
SELECT order_id, status, total_price, payment_method, created_at
FROM orders
ORDER BY created_at DESC
LIMIT 10;

-- See the raw JSON stored for an order
SELECT order_id, documents_json
FROM orders
WHERE order_id = 'ORDER_20260803_EC90';

-- Count orders by status
SELECT status, COUNT(*) as cnt
FROM orders
GROUP BY status;
```

## Verify order details

For a given `order_id`, you should see:

- `status` — one of: `pending`, `paid`, `processing`, `ready`, `shipped`, `completed`, `cancelled`
- `total_price` — integer, price in PLN
- `payment_method` — `blik`, `uah`, `usdt`, or `None`
- `payment_proof_file_id` — Telegram file ID of the receipt photo (if uploaded)
- `documents_json` — JSON array with document types, quantities, and filled fields

If you need to check order items separately:

```sql
SELECT o.order_id, oi.document_type, oi.quantity, oi.unit_price
FROM orders o
JOIN order_items oi ON o.id = oi.order_id
WHERE o.order_id = 'ORDER_20260803_EC90';
```

## Troubleshooting

- **No orders found**: Make sure the bot has been started and at least one order flow was completed.
- **Database locked**: Stop the bot before running `sqlite3` commands.
- **Wrong path**: By default the bot uses `sqlite:///bot.db` (file `bot.db` in project root). If you changed `DATABASE_URL`, adjust the path accordingly.
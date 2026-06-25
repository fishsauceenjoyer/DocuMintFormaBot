# Tests — DocuMint Telegram Bot

Unit tests for the Telegram bot's order FSM, fast-order flow, database
configuration, and order-routing logic. All tests use mocked Telegram objects
so they run offline without a real bot token.

---

## Test files

| File | What it covers |
|------|----------------|
| `test_order.py` | Main order flow: document selection, quantity, delivery choice, cart validation |
| `test_fast_order.py` | Fast-order callback (accessible/inaccessible message), message forwarding |
| `test_router.py` | Order routing to manager chats, metadata storage on failure |
| `test_database_config.py` | SQLAlchemy engine initialisation with SQLite and PostgreSQL URLs |

---

## How to run

```bash
# From project root — run all tests
pytest -v

# Run a single file
pytest tests/test_order.py -v

# Run with coverage
pytest --cov=. -v
```

---

## Test doubles (mocks)

All mocks live in `tests/conftest.py` (shared) or inline in each test file:

| Mock | Purpose |
|------|---------|
| `MockBot` | Stores sent messages / photos locally for assertion |
| `MockMessage` | Stores `_edited_text` and `_answered_text` without Telegram API |
| `MockCallback` | Simulates inline-button press with configurable message accessibility |
| `MockFSMContext` | In-memory FSM state storage |

A `clean_user_sessions` fixture clears the global in-memory session store
between test runs.

---

## Adding a new test

1. Add your test function to the appropriate file (or create a new one).
2. Use the fixtures from `conftest.py`:
   ```python
   @pytest.mark.asyncio
   async def test_something(mock_fsm, clean_user_sessions):
       callback = MockCallback(data="doc_visa")
       await my_handler(callback, mock_fsm)
       assert callback._answered is True
   ```
3. Run `pytest -v` and check it passes.
4. Run `flake8 .` to ensure style compliance.

---

## Known issues

- `test_database_engine_works_with_postgresql_url` requires `psycopg2`
  installed. It will be skipped or fail if the package is missing — this is
  expected in a development environment that uses SQLite only.
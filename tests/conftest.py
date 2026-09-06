"""Shared pytest fixtures and Telegram test doubles.

The mocks mimic the aiogram objects used by handlers and record sent/edited
messages locally, so unit tests can exercise FSM logic without Telegram API
network calls.

Failover behaviour
------------------
By default, all tests use mocked Telegram objects and never call the real API.
This ensures tests run offline, fast, and without a bot token.

If you pass ``--with-real-api`` on the command line AND the bot token is set
AND ``api.telegram.org`` is reachable, the **telegram_available** fixture
returns ``True``. Test modules that support a real-API code path can check
this fixture and conditionally switch to live calls.  When the API is
unreachable (or the flag is not given), the entire suite silently falls back
to mocks without any test failure.
"""

import asyncio
import datetime
import logging
import os
import socket
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pytest
from aiogram.types import CallbackQuery, Chat, InaccessibleMessage, Message, User

logger = logging.getLogger(__name__)

# ── mutmut compatibility ───────────────────────────────────────────────
# When mutmut runs tests, it copies only data/ and tests/ to a mutants/
# subdirectory.  Other source packages (fsm, handlers, services, etc.) are
# not copied.  We detect the mutants/ environment and add the real project
# root to sys.path so those imports still resolve.
# The data/ package resolves from mutants/data/ first (since '' / cwd is
# ahead of the appended path), so mutated copies are always tested.
_this_dir = Path(__file__).resolve().parent
_parent_dir = _this_dir.parent
if _parent_dir.name == "mutants":
    _real_root = str(_parent_dir.parent)
    if _real_root not in sys.path:
        sys.path.append(_real_root)
# ── end mutmut compatibility ────────────────────────────────────────────


# ── CLI option ──────────────────────────────────────────────────────────


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register a ``--with-real-api`` flag for live Telegram API tests."""
    parser.addoption(
        "--with-real-api",
        action="store_true",
        default=False,
        help="Attempt real Telegram API calls (requires BOT_TOKEN + connectivity)",
    )


# ── Connectivity detection ──────────────────────────────────────────────


def _telegram_api_reachable() -> bool:
    """Check whether ``api.telegram.org`` is reachable via DNS + TCP.

    Returns ``True`` only if the hostname resolves **and** a TCP connection
    to port 443 succeeds within a short timeout.
    """
    try:
        # DNS lookup
        addresses = socket.getaddrinfo("api.telegram.org", 443)
        if not addresses:
            logger.info("telegram API unreachable: DNS returned no addresses")
            return False

        # Try connecting to the first resolved address
        addr = addresses[0]
        sock = socket.socket(addr[0], socket.SOCK_STREAM)
        sock.settimeout(3.0)
        try:
            sock.connect(addr[4])
            logger.info("telegram API reachable via %s", addr[4])
            return True
        except (OSError, socket.timeout) as exc:
            logger.info("telegram API unreachable: %s", exc)
            return False
        finally:
            sock.close()
    except socket.gaierror as exc:
        logger.info("telegram API unreachable (DNS): %s", exc)
        return False


def _bot_token_available() -> bool:
    """Check whether a real ``BOT_TOKEN`` is set (not a placeholder)."""
    token = os.getenv("BOT_TOKEN", "")
    if not token:
        return False
    # Common placeholders found in .env.example files
    placeholders = {"your_bot_token_here", "1234567890:YOUR_TOKEN"}
    return token not in placeholders


# ── Session-scoped availability flag ────────────────────────────────────


@pytest.fixture(scope="session")
def telegram_available(request: pytest.FixtureRequest) -> bool:
    """Session-scoped flag indicating real Telegram API availability.

    The check is performed once per test run.  It requires all three
    conditions:

    * ``--with-real-api`` is passed on the CLI **and**
    * ``BOT_TOKEN`` env var is set to a non-placeholder value **and**
    * ``api.telegram.org`` is reachable (DNS + TCP).

    When any condition is missing the fixture returns ``False``, which causes
    the entire suite to use mocks.
    """
    if not request.config.getoption("--with-real-api"):
        logger.info("telegram API disabled: --with-real-api not passed")
        return False

    if not _bot_token_available():
        logger.info("telegram API disabled: BOT_TOKEN missing or placeholder")
        return False

    return _telegram_api_reachable()


@pytest.fixture(scope="session")
def use_mocks(telegram_available: bool) -> bool:
    """Fixture – should the test suite use mocks?

    Returns ``True`` when the real Telegram API is **not** available,
    so all tests automatically fall back to the mocked Telegram objects
    defined below.
    """
    return not telegram_available


# ── Mock Telegram objects ───────────────────────────────────────────────


class MockBot:
    """Mock bot object that records sent messages locally."""

    def __init__(self):
        self._mock_message_sent: Optional[dict] = None
        self._mock_photo_sent: Optional[dict] = None
        self._mock_document_sent: Optional[dict] = None
        self.id = 12345  # Bot ID

    async def send_message(self, chat_id, text, **kwargs):
        self._mock_message_sent = {"chat_id": chat_id, "text": text, "kwargs": kwargs}
        return Message(
            message_id=123,
            date=datetime.datetime.now(),
            chat=Chat(id=chat_id, type="private"),
            from_user=User(id=chat_id, is_bot=False, first_name="Test"),
        )

    async def send_photo(self, chat_id, photo, caption=None, **kwargs):
        self._mock_photo_sent = {
            "chat_id": chat_id,
            "photo": photo,
            "caption": caption,
            "kwargs": kwargs,
        }
        return True

    async def send_document(self, chat_id, document, caption=None, **kwargs):
        self._mock_document_sent = {
            "chat_id": chat_id,
            "document": document,
            "caption": caption,
            "kwargs": kwargs,
        }
        return True


class MockMessage(Message):
    """Mock Message subclass that captures edited / answered text."""

    bot: Any  # type: ignore[assignment]  # injected at runtime by aiogram

    def __init__(self, text=None, message_id=1, chat_id=123, user_id=123):
        chat = Chat(id=chat_id, type="private")
        from_user = User(
            id=user_id, is_bot=False, first_name="Test", username="testuser"
        )
        date = datetime.datetime.now()
        super().__init__(
            message_id=message_id,
            date=date,
            chat=chat,
            from_user=from_user,
            text=text,
        )
        self._edited_text: Optional[str] = None
        self._answered_text: Optional[str] = None

    async def edit_text(self, text, **kwargs):
        self._edited_text = text
        return True

    async def answer(self, text, **kwargs):
        self._answered_text = text
        return True


class MockCallback(CallbackQuery):
    """CallbackQuery test double that stores callback answers locally."""

    message: Any  # type: ignore[assignment]  # may be None/duck-typed in tests
    bot: Any  # type: ignore[assignment]  # injected at runtime by aiogram

    def __init__(self, data=None, message_accessible=True, user_id=123):
        user = User(id=user_id, is_bot=False, first_name="Test", username="testuser")
        if message_accessible:
            msg = MockMessage(chat_id=user_id)
        else:
            msg = InaccessibleMessage(
                message_id=1, date=0, chat=Chat(id=user_id, type="private")
            )

        super().__init__(
            id=f"callback_{user_id}_{datetime.datetime.now().timestamp()}",
            from_user=user,
            chat_instance=f"instance_{user_id}",
            message=msg,
            data=data,
        )
        self._answered: bool = False
        self._answered_text: Optional[str] = None
        self._show_alert: Optional[bool] = None

    async def answer(self, text=None, show_alert=None):
        self._answered = True
        self._answered_text = text
        self._show_alert = show_alert
        return True


class MockFSMContext:
    """In-memory FSM context storage for testing."""

    def __init__(self):
        self._data: Dict[str, Any] = {}

    async def set_state(self, state):
        self._data["state"] = state

    async def update_data(self, **kwargs):
        self._data.update(kwargs)

    async def clear(self):
        self._data.clear()

    async def get_state(self):
        return self._data.get("state")

    async def get_data(self):
        return self._data.copy()


# ── Standard fixtures ───────────────────────────────────────────────────


@pytest.fixture
def mock_bot():
    """Return a ``MockBot`` instance."""
    return MockBot()


@pytest.fixture
def mock_fsm():
    """Return a ``MockFSMContext`` instance."""
    return MockFSMContext()


@pytest.fixture
def mock_callback():
    """Return a ``MockCallback`` with an accessible message (doc_poster_terminator1)."""
    return MockCallback(data="doc_poster_terminator1", message_accessible=True)


@pytest.fixture
def clean_user_sessions():
    """Clear the global user session store before and after each test."""
    from handlers.order import user_sessions

    user_sessions.clear()
    yield
    user_sessions.clear()


# ── Order-handler database fixture ───────────────────────────────────────


@pytest.fixture
async def mock_order_db(monkeypatch):
    """Patch ``handlers.order.AsyncSessionLocal`` to use an in-memory SQLite DB.

    Creates all tables from ``db.models.Base.metadata`` so handlers that
    touch the database (e.g. ``_generate_order_id``, ``process_payment_proof``)
    run against a clean in-memory schema instead of the real ``bot.db``.
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from db.models import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    TestSession = async_sessionmaker(engine, expire_on_commit=False)

    import handlers.order as order_module

    monkeypatch.setattr(order_module, "AsyncSessionLocal", TestSession)
    return TestSession


# ── Integration-test database fixture ────────────────────────────────────


@pytest.fixture
async def test_db(tmp_path, monkeypatch):
    """Spin up a temporary SQLite database and apply all Alembic migrations.

    Creates a file-based SQLite DB in the pytest ``tmp_path``, runs
    ``alembic upgrade head`` so the schema matches production, then patches
    ``handlers.order.AsyncSessionLocal`` (and ``db.crud.AsyncSessionLocal``)
    to use an async session factory bound to the test database.

    Yields an ``async_sessionmaker`` so tests can open their own sessions to
    assert on the persisted data.
    """
    import importlib

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    db_file = tmp_path / "integration_test.db"
    db_url = f"sqlite:///{db_file}"

    # Patch DATABASE_URL *before* reloading db.crud so the module-level
    # engine/session factory point at the test database.
    import config

    monkeypatch.setattr(config, "DATABASE_URL", db_url)

    # Reload db.crud so its module-level engine picks up the new URL.
    import db.crud as crud_module

    importlib.reload(crud_module)

    # Run Alembic migrations against the test database.
    # migrations/env.py reads config.DATABASE_URL at execution time, so the
    # monkeypatched value is used.
    from alembic import command
    from alembic.config import Config as AlembicConfig

    alembic_cfg = AlembicConfig("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(alembic_cfg, "head")

    # Build an async session factory bound to the freshly-migrated test database.
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")
    TestSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    # Patch the AsyncSessionLocal used by the order handler (imported at module
    # load time) so DB writes go to the test database.
    import handlers.order as order_module

    monkeypatch.setattr(order_module, "AsyncSessionLocal", TestSessionLocal)

    # Also patch db.crud.AsyncSessionLocal for any code that imports it lazily.
    monkeypatch.setattr(crud_module, "AsyncSessionLocal", TestSessionLocal)

    try:
        yield TestSessionLocal
    finally:
        await engine.dispose()


@pytest.fixture
def clean_admin_orders():
    """Clear the in-memory admin orders dict before and after each test."""
    from handlers.admin import orders

    orders.clear()
    yield
    orders.clear()

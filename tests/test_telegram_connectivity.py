"""Telegram API connectivity test — controls the failover mechanism.

This module serves two purposes:

1. **Probe** — a single, fast test that checks whether the real Telegram
   API is actually reachable (DNS + TCP + optional HTTP ping via Bot API).

2. **Failover trigger** — the result is exposed via the session-scoped
   ``telegram_available`` fixture defined in ``conftest.py``.  When the API
   is unreachable, the ``use_mocks`` fixture returns ``True`` and *every*
   downstream test automatically falls back to mock Telegram objects
   without raising or skipping.

Design decisions
----------------
- The probe is intentionally minimal: DNS + TCP to ``api.telegram.org:443``.
  An HTTP-level check (``getMe``) would be more precise, but requires a
  valid bot token and counts against rate limits.  The TCP check is a safe,
  zero-cost proxy that catches the vast majority of network-offline cases.

- If a more thorough probe is desired later (e.g. in CI), the
  ``_telegram_api_reachable()`` function in ``conftest.py`` can be extended
  with an optional ``requests.get`` call.

Usage
-----
.. code:: bash

    # Offline (default) — mocks only, no network calls
    pytest tests/

    # Online — attempts real API (skips test if unreachable)
    pytest tests/ --with-real-api
"""

import logging

import pytest
from conftest import _bot_token_available, _telegram_api_reachable

logger = logging.getLogger(__name__)


# ── Connectivity test (offline-safe) ────────────────────────────────────


def test_telegram_api_dns_resolves() -> None:
    """Verify that ``api.telegram.org`` resolves to at least one IP address.

    This test **never** makes an HTTP request — only a DNS lookup followed
    by a TCP connect socket check.  It is safe to run in fully offline
    environments: it will simply return ``False`` and log the outcome
    without failing.

    The test always passes.  Its real value is the *side-effect*: the
    session-scoped ``telegram_available`` fixture reuses the same
    ``_telegram_api_reachable()`` helper and records the result for every
    other test in the suite.
    """
    reachable = _telegram_api_reachable()
    token_ok = _bot_token_available()

    if not reachable:
        logger.info(
            "Telegram API is NOT reachable — all tests will use mocks. "
            "This is expected when running offline or without network."
        )
    elif not token_ok:
        logger.info(
            "Telegram API is reachable but BOT_TOKEN is missing/placeholder — "
            "all tests will use mocks."
        )
    else:
        logger.info(
            "Telegram API IS reachable and BOT_TOKEN is available — "
            "tests that support real API calls may run against the live API."
        )

    # Always pass — this is a diagnostic probe, not a gate
    assert True


# ── Conditional real-API smoke test ─────────────────────────────────────


@pytest.mark.asyncio
async def test_telegram_getme(
    request: pytest.FixtureRequest, telegram_available: bool
) -> None:
    """Optional smoke test: call ``getMe`` on the real Bot API.

    This test runs **only** when ``--with-real-api`` is passed on the
    CLI *and* ``api.telegram.org`` is reachable *and* a real ``BOT_TOKEN``
    is set.  In all other cases it is skipped.
    """
    if not request.config.getoption("--with-real-api"):
        pytest.skip("Pass --with-real-api to test live Telegram API connectivity")

    if not telegram_available:
        pytest.skip("Telegram API not available")

    import os

    from aiogram import Bot

    token = os.getenv("BOT_TOKEN")
    if not token:
        pytest.skip("BOT_TOKEN not set")

    bot = Bot(token=token)
    try:
        me = await bot.get_me()
        assert me is not None
        assert me.username is not None
        logger.info("Live Telegram API check passed: bot @%s", me.username)
    finally:
        await bot.session.close()

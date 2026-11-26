"""Tests for routing configuration validation and error propagation.

Verifies that invalid routing chat IDs are rejected at initialization
and that TelegramForbiddenError is not silently swallowed by the router.
Both tests are expected to fail until the routing validation and error
propagation fix is merged (TDD crash tests).
"""

import importlib
import os

import pytest

from aiogram.exceptions import TelegramForbiddenError

from utils import router


class _DummyTelegramMethod:
    """Minimal TelegramMethod stub for constructing TelegramForbiddenError."""

    __returning__ = bool
    api_method: str = "sendMessage"


class _FailingBot:
    """Bot whose send_message raises TelegramForbiddenError."""

    async def send_message(self, *args, **kwargs):
        raise TelegramForbiddenError(
            method=_DummyTelegramMethod(),
            message="Forbidden: bot was blocked by the user",
        )

    async def send_photo(self, *args, **kwargs):
        raise TelegramForbiddenError(
            method=_DummyTelegramMethod(),
            message="Forbidden: bot was blocked by the user",
        )


@pytest.mark.xfail(reason="TDD: awaiting routing validation and error propagation fix")
def test_missing_default_routing_id_raises_value_error(monkeypatch):
    """Invalid ROUTING_DEFAULT chat id must raise ValueError at initialization."""
    monkeypatch.setitem(os.environ, "ROUTING_DEFAULT", "-100")

    import config_runtime

    raised = False
    try:
        importlib.reload(config_runtime)
    except ValueError:
        raised = True

    if not raised:
        pytest.fail(
            "ROUTING_DEFAULT='-100' did not raise ValueError: invalid chat_id "
            "is silently swallowed (hidden fallback). Expected: ValueError."
        )


@pytest.mark.xfail(reason="TDD: awaiting routing validation and error propagation fix")
@pytest.mark.asyncio
async def test_send_order_to_manager_propagates_forbidden_error():
    """router._safe_send must propagate TelegramForbiddenError instead of swallowing it."""
    bot = _FailingBot()
    swallowed = False
    try:
        await router._safe_send(
            bot=bot,
            chat_id=-100123456789,
            text="test message",
        )
    except TelegramForbiddenError:
        pass  # error propagated upwards — desired behavior
    except Exception:
        swallowed = True  # error was caught and wrapped/swallowed
    else:
        # returned normally (False) — error fully swallowed
        swallowed = True

    if swallowed:
        pytest.fail(
            "router._safe_send swallowed TelegramForbiddenError silently: "
            "exception was not propagated and no critical alert was raised. "
            "Expected: propagation upwards or critical alert."
        )

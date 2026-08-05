"""Resilient polling wrapper with retry logic for Telegram API network errors.

The wrapper wraps ``Dispatcher.start_polling`` in an infinite loop and
classifies exceptions into three buckets:

* **Retryable** (``aiogram.exceptions.TelegramNetworkError`` and
  ``aiohttp.ClientConnectorError``) — log a warning and retry after a random
  10–30 second delay.
* **Interrupts** (``KeyboardInterrupt`` / ``SystemExit``) — re-raise so the
  process can shut down gracefully (e.g. on ``SIGINT`` / ``SIGTERM``).
* **Anything else** — log critical and exit immediately with ``exit_code`` so
  an orchestrator (Docker ``restart: unless-stopped``, systemd) can restart
  the process in a clean state instead of looping forever on a non-network bug.

After ``max_consecutive_failures`` retryable errors *in a row* the wrapper
exits with ``exit_code``, so a permanent network block does not leave the
process spinning forever.  "In a row" is measured by wall-clock survival: if
the previous attempt ran healthily for at least ``reset_after_seconds`` before
failing, the failure counter resets to one.  This prevents long-lived bots
from dying because of five intermittent blips spread over days.

The function returns an exit code (``0`` on clean stop) instead of calling
``sys.exit`` itself, which keeps it unit-testable.
"""

import asyncio
import logging
import os
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Tuning parameters for the polling retry loop.

    ``min_delay`` / ``max_delay`` bound the random sleep between attempts;
    the actual delay is sampled uniformly from this interval to avoid
    stampeding a recovering API endpoint with synchronized reconnects.
    ``reset_after_seconds`` is the healthy-survival threshold described in
    the module docstring.
    """

    max_consecutive_failures: int = field(
        default_factory=lambda: int(os.getenv("MAX_RETRY_ATTEMPTS", "5"))
    )
    min_delay: float = field(
        default_factory=lambda: float(os.getenv("RETRY_DELAY_MIN_SECONDS", "10"))
    )
    max_delay: float = field(
        default_factory=lambda: float(os.getenv("RETRY_DELAY_MAX_SECONDS", "30"))
    )
    reset_after_seconds: float = field(
        default_factory=lambda: float(os.getenv("RETRY_RESET_AFTER_SECONDS", "60"))
    )
    exit_code: int = 1


# Imported lazily so the module can be imported even if the aiogram version
# changes the location of these exception classes.
def _retryable_exceptions() -> tuple[type[BaseException], ...]:
    try:
        from aiogram.exceptions import TelegramNetworkError
    except ImportError:  # pragma: no cover - aiogram always ships this
        TelegramNetworkError = Exception  # type: ignore[assignment,misc]
    try:
        from aiohttp import ClientConnectorError
    except ImportError:  # pragma: no cover - aiohttp is an aiogram dependency
        ClientConnectorError = Exception  # type: ignore[assignment,misc]
    return (TelegramNetworkError, ClientConnectorError)


def _from_config() -> RetryConfig:
    """Build a :class:`RetryConfig` from environment variables.

    Entries that fail to parse fall back to the built-in default, so a bad
    value in ``.env`` can never crash the bot at startup.
    """

    def _env_float(name: str, default: float) -> float:
        raw = os.getenv(name)
        if raw is None:
            return default
        try:
            return float(raw)
        except ValueError:
            logger.warning("Invalid %s=%r, using default %s", name, raw, default)
            return default

    def _env_int(name: str, default: int) -> int:
        raw = os.getenv(name)
        if raw is None:
            return default
        try:
            return int(raw)
        except ValueError:
            logger.warning("Invalid %s=%r, using default %s", name, raw, default)
            return default

    return RetryConfig(
        max_consecutive_failures=_env_int("MAX_RETRY_ATTEMPTS", 5),
        min_delay=_env_float("RETRY_DELAY_MIN_SECONDS", 10.0),
        max_delay=_env_float("RETRY_DELAY_MAX_SECONDS", 30.0),
        reset_after_seconds=_env_float("RETRY_RESET_AFTER_SECONDS", 60.0),
        exit_code=1,
    )


async def run_polling_with_retry(
    dp: Any,
    bot: Any,
    config: RetryConfig | None = None,
    *,
    _now: Callable[[], float] | None = None,
) -> int:
    """Run ``dp.start_polling(bot)`` forever, retrying on network errors.

    Args:
        dp: Configured aiogram Dispatcher (duck-typed — only ``start_polling``
            is required, which keeps the wrapper unit-testable without a real
            bot token).
        bot: Configured aiogram Bot (duck-typed).
        config: Retry tuning. Defaults to env-configurable
            :class:`RetryConfig`.
        _now: Test-only monotonic clock, defaults to the running loop's
            ``time()``.

    Returns:
        Exit code: ``0`` on a clean stop (e.g. ``stop_polling``),
        ``config.exit_code`` after ``max_consecutive_failures`` consecutive
        network errors or on an unhandled non-network exception.
    """
    if config is None:
        config = _from_config()
    if _now is None:
        _now = asyncio.get_running_loop().time

    retryable = _retryable_exceptions()
    consecutive_failures = 0
    attempt = 0

    while True:
        attempt += 1
        attempt_started = _now()
        try:
            await dp.start_polling(bot)
        except (KeyboardInterrupt, SystemExit):
            # Preserve graceful shutdown behaviour (SIGINT / SIGTERM).
            logger.info("Polling interrupted, shutting down gracefully.")
            raise
        except retryable as exc:
            elapsed = _now() - attempt_started
            if elapsed >= config.reset_after_seconds:
                # The previous attempt survived a healthy period — the streak
                # of consecutive failures is broken.
                consecutive_failures = 1
            else:
                consecutive_failures += 1

            if consecutive_failures >= config.max_consecutive_failures:
                logger.critical(
                    "Telegram API unreachable for %d consecutive attempts "
                    "(attempt %d): %s — exiting with code %d",
                    consecutive_failures,
                    attempt,
                    exc,
                    config.exit_code,
                )
                return config.exit_code

            # Backoff jitter — not used for security/crypto, so B311 is a
            # false positive here.
            delay = random.uniform(config.min_delay, config.max_delay)  # nosec: B311
            logger.warning(
                "Telegram network error (attempt %d, %d consecutive): %s — "
                "retrying in %.1fs",
                attempt,
                consecutive_failures,
                exc,
                delay,
            )
            await asyncio.sleep(delay)
        except Exception as exc:  # noqa: BLE001 - top-level safety net
            logger.critical(
                "Unhandled polling error (attempt %d): %s — exiting with code %d",
                attempt,
                exc,
                config.exit_code,
            )
            return config.exit_code
        else:
            # start_polling returned normally (e.g. stop_polling was called).
            logger.info("Polling stopped cleanly.")
            return 0

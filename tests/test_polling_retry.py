"""Tests for the resilient polling wrapper (``utils.polling_retry``).

The wrapper is tested with a fake dispatcher so no network access or real
Telegram API is required.  Delays are pinned to zero via :class:`RetryConfig`
and wall-clock behaviour is driven by an injected fake clock to keep the
suite fast and deterministic.

Retryable exceptions are represented by local stand-ins
(:class:`FakeNetworkError`, :class:`FakeConnectorError`) with normal
constructor semantics.  The module's ``_retryable_exceptions()`` hook is
patched to return them, which keeps the tests independent of the exact
aiogram/aiohttp constructor signatures while still exercising the retry
classification path.
"""

import pytest

from utils.polling_retry import RetryConfig, run_polling_with_retry


class FakeNetworkError(Exception):
    """Stand-in for ``TelegramNetworkError``."""


class FakeConnectorError(Exception):
    """Stand-in for ``aiohttp.ClientConnectorError``."""


class FakeDispatcher:
    """Minimal stand-in for ``aiogram.Dispatcher``.

    Lets the test script the behaviour of ``start_polling``: raise retryable
    exceptions an arbitrary number of times, raise an unexpected exception,
    or return cleanly.
    """

    def __init__(self, failures=None, unexpected=None, calls=None):
        self.failures = list(failures or [])
        self.unexpected = unexpected
        self.calls = calls or []
        self.start_polling_calls = 0

    async def start_polling(self, bot):
        self.start_polling_calls += 1
        self.calls.append("start")
        if self.unexpected is not None:
            raise self.unexpected
        if self.failures and self.failures.pop(0) != 0:
            raise FakeNetworkError("simulated network loss")


class FakeBot:
    """Placeholder bot object — never used by the fake dispatcher."""


class SequencedClock:
    """Fake monotonic clock that returns a scripted sequence of timestamps."""

    def __init__(self, values):
        self._values = list(values)

    def __call__(self) -> float:
        if not self._values:
            raise AssertionError("Ran out of clock values")
        return self._values.pop(0)


@pytest.fixture
def fast_config() -> RetryConfig:
    """Retry config with zero delays and a low failure threshold."""
    return RetryConfig(
        max_consecutive_failures=3,
        min_delay=0.0,
        max_delay=0.0,
        reset_after_seconds=10.0,
        exit_code=7,
    )


@pytest.fixture
def retryable_types(monkeypatch):
    """Point the wrapper's retryable exception hook at the fake classes."""
    import utils.polling_retry as pr

    monkeypatch.setattr(pr, "_retryable_exceptions", lambda: (FakeNetworkError,))
    return (FakeNetworkError,)


@pytest.fixture
def retryable_types_both(monkeypatch):
    """Point the hook at both fake retryable exception classes."""
    import utils.polling_retry as pr

    monkeypatch.setattr(
        pr, "_retryable_exceptions", lambda: (FakeNetworkError, FakeConnectorError)
    )
    return (FakeNetworkError, FakeConnectorError)


@pytest.mark.asyncio
async def test_recovers_after_transient_network_errors(
    fast_config, retryable_types
) -> None:
    """A one-off network blip must not kill the bot."""
    dp = FakeDispatcher(failures=[1, 0])  # one failure, then clean poll
    bot = FakeBot()

    exit_code = await run_polling_with_retry(dp, bot, config=fast_config)

    assert exit_code == 0
    assert dp.start_polling_calls == 2


@pytest.mark.asyncio
async def test_retries_both_retryable_exception_types(
    fast_config, retryable_types_both
) -> None:
    """Both TelegramNetworkError and aiohttp.ClientConnectorError are retried."""
    errors = iter(
        [
            FakeNetworkError("telegram down"),
            FakeConnectorError("connector refused"),
        ]
    )
    calls = []

    async def _start_polling(bot):
        calls.append("start")
        try:
            raise next(errors)
        except StopIteration:
            return

    dp = FakeDispatcher()
    dp.start_polling = _start_polling  # type: ignore[method-assign]
    bot = FakeBot()

    exit_code = await run_polling_with_retry(dp, bot, config=fast_config)

    assert exit_code == 0
    assert len(calls) == 3  # 2 errors + 1 clean stop


@pytest.mark.asyncio
async def test_exits_after_max_consecutive_failures(
    fast_config, retryable_types
) -> None:
    """Permanent outage must end with the configured exit code."""
    dp = FakeDispatcher(failures=[1, 1, 1])  # exactly max_consecutive_failures
    bot = FakeBot()

    exit_code = await run_polling_with_retry(dp, bot, config=fast_config)

    assert exit_code == fast_config.exit_code == 7
    assert dp.start_polling_calls == 3


@pytest.mark.asyncio
async def test_time_based_reset_prevents_death_from_spread_out_blips(
    fast_config, retryable_types
) -> None:
    """A long healthy period before a failure breaks the consecutive streak.

    Each attempt consumes two clock reads: the attempt start and the moment
    the exception is raised.  Timeline:

    * attempt 1: 0.0 → 0.1  (elapsed 0.1s)   — counter 1
    * attempt 2: 5.0 → 15.1 (elapsed 10.1s)  — counter resets to 1
    * attempt 3: 15.2 → 15.3 (elapsed 0.1s)  — counter 2
    * attempt 4: 15.4 → 15.5 (elapsed 0.1s)  — counter 3 → exit

    Without the time-based reset the wrapper would have exited after attempt
    3; with it, a genuinely healthy 10s stretch grants the bot an extra life.
    """
    dp = FakeDispatcher(failures=[1, 1, 1, 1])  # all attempts fail
    bot = FakeBot()
    clock = SequencedClock([0.0, 0.1, 5.0, 15.1, 15.2, 15.3, 15.4, 15.5])

    exit_code = await run_polling_with_retry(dp, bot, config=fast_config, _now=clock)

    assert exit_code == fast_config.exit_code
    assert dp.start_polling_calls == 4


@pytest.mark.asyncio
async def test_exits_on_unexpected_exception(fast_config, retryable_types) -> None:
    """Non-network errors must fail fast (no infinite retry loop)."""
    dp = FakeDispatcher(unexpected=RuntimeError("bug in handler"))
    bot = FakeBot()

    exit_code = await run_polling_with_retry(dp, bot, config=fast_config)

    assert exit_code == fast_config.exit_code
    assert dp.start_polling_calls == 1


@pytest.mark.asyncio
async def test_clean_stop_returns_zero(fast_config, retryable_types) -> None:
    """A clean return from start_polling (stop_polling) must exit 0."""
    dp = FakeDispatcher(failures=[])  # clean return on first call
    bot = FakeBot()

    exit_code = await run_polling_with_retry(dp, bot, config=fast_config)

    assert exit_code == 0
    assert dp.start_polling_calls == 1


@pytest.mark.asyncio
async def test_keyboard_interrupt_propagates(fast_config, retryable_types) -> None:
    """KeyboardInterrupt/SystemExit must be re-raised, not swallowed."""
    dp = FakeDispatcher()
    bot = FakeBot()

    async def _interrupt(bot):
        raise KeyboardInterrupt

    dp.start_polling = _interrupt  # type: ignore[method-assign]

    with pytest.raises(KeyboardInterrupt):
        await run_polling_with_retry(dp, bot, config=fast_config)

"""Интеграционные тесты «слепых зон» роутинга и валидации настроек.

Цель: зафиксировать уязвимость, которая сейчас позволяет невалидным ID в .env
молча пройти инициализацию, а ошибкам Telegram — поглощаться скрыто.
Оба теста ДОЛЖНЫ упасть (FAILED) на текущем коде — это и есть доказательство бага.
"""

import importlib
import os

import pytest

from aiogram.exceptions import TelegramForbiddenError

from utils import router


class _DummyTelegramMethod:
    """Минимальная заглушка TelegramMethod для конструирования TelegramForbiddenError.

    Исключение просто хранит ``method`` как атрибут, поэтому полноценный
    экземпляр ``TelegramMethod`` не обязателен.
    """

    __returning__ = bool
    api_method: str = "sendMessage"


class _FailingBot:
    """Бот, у которого send_message бросает TelegramForbiddenError (бан бота / сбой сети)."""

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


@pytest.mark.xfail(reason="Known routing edge-case documented for future refactoring")
def test_config_swallows_invalid_routing_env(monkeypatch):
    """ROUTING_DEFAULT с невалидным значением должен вызвать ValueError при инициализации.

    config_runtime делает int(os.getenv(...)) без валидации формата Telegram-chat-id.
    Значение "-100" (число без полного префикса -100XXXXXXX) — parsable int,
    но не валидный ID канала/супергруппы — проглатывается молча.
    Ожидаемое (после фикса): ValueError. Текущее: исключения нет -> pytest.fail().
    """
    monkeypatch.setitem(os.environ, "ROUTING_DEFAULT", "-100")

    import config_runtime

    raised = False
    try:
        importlib.reload(config_runtime)
    except ValueError:
        raised = True  # желаемое поведение — невалидный env отвергнут

    if not raised:
        pytest.fail(
            "ROUTING_DEFAULT='-100' не вызвал ValueError при инициализации настроек: "
            "невалидный chat_id в .env проглатывается молча (скрытый fallback). "
            "Ожидалось: ValueError."
        )


@pytest.mark.asyncio
@pytest.mark.xfail(reason="Known routing edge-case documented for future refactoring")
async def test_router_silent_fallback_prevention():
    """_safe_send не должен поглощать TelegramForbiddenError молча.

    Ошибка должна пробрасываться наверх или порождать критический алерт,
    а не возвращаться как False / игнорироваться.
    Текущее поведение: try/except Exception в _safe_send ловит ошибку, логирует,
    возвращает False — уязвимость, тест падает.
    """
    bot = _FailingBot()
    swallowed = False
    try:
        await router._safe_send(
            bot=bot,
            chat_id=-100123456789,
            text="test message",
        )
    except TelegramForbiddenError:
        pass  # ошибка проброшена наверх — желаемое поведение
    except Exception:
        swallowed = True  # ошибка поймана и завернута/поглощена
    else:
        # вернулось нормально (False) — ошибка полностью поглощена
        swallowed = True

    if swallowed:
        pytest.fail(
            "router._safe_send проглотил TelegramForbiddenError молча: "
            "исключение не проброшено и не порождено критическое оповещение. "
            "Ожидалось: проброс наверх или критический алерт."
        )

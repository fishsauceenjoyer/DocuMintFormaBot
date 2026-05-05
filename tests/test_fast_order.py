"""
Тесты для обработчиков быстрого заказа (fast_order) с замоканным Telegram API.

Использует мок-объекты вместо реального Telegram API для тестирования
логики обработки callback-запросов и сообщений без необходимости
подключения к боту.
"""

import datetime
import os
import sys
from unittest.mock import patch

import pytest
from aiogram.types import (Chat, InaccessibleMessage, Message,
                           User)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fsm.states import OrderState  # noqa: E402


class MockBot:
    """
    Мок-объект бота для тестирования.

    Вместо реальной отправки сообщений через Telegram API сохраняет
    параметры вызова send_message для последующей проверки в тестах.

    Атрибуты:
        _mock_message_sent: Словарь с параметрами последнего вызова send_message.
    """

    _mock_message_sent: dict | None = None

    def __init__(self):
        pass

    async def send_message(self, chat_id, text, **kwargs):
        """
        Имитация отправки сообщения.

        Сохраняет параметры вызова и возвращает мок-объект Message.

        Args:
            chat_id: ID чата получателя.
            text: Текст сообщения.
            kwargs: Дополнительные параметры (parse_mode и т.д.).
        """
        self._mock_message_sent = {"chat_id": chat_id, "text": text, "kwargs": kwargs}
        return Message(
            message_id=123,
            date=datetime.datetime.now(),
            chat=Chat(id=chat_id, type="private"),
            from_user=User(id=chat_id, is_bot=False, first_name="Test"),
        )


class MockMessage:
    """
    Мок-объект сообщения для тестирования.

    Имитирует объект Message из aiogram, сохраняя отредактированный
    и отправленный текст для проверки.

    Атрибуты:
        text: Текст сообщения.
        _edited_text: Текст после вызова edit_text.
        _answered_text: Текст после вызова answer.
    """

    text: str | None
    message_id: int
    _edited_text: str | None = None
    _answered_text: str | None = None

    def __init__(self, text=None, message_id=1, chat_id=123):
        self.text = text
        self.message_id = message_id
        self.chat = Chat(id=chat_id, type="private")
        self.from_user = User(
            id=chat_id, is_bot=False, first_name="Test", username="testuser"
        )
        self.bot = MockBot()

    async def edit_text(self, text, **kwargs):
        """Имитация редактирования текста сообщения."""
        self._edited_text = text
        return True

    async def answer(self, text, **kwargs):
        """Имитация ответа на сообщение."""
        self._answered_text = text
        return True


class MockCallback:
    """
    Мок-объект callback-запроса для тестирования.

    Позволяет имитировать как доступные (Message), так и недоступные
    (InaccessibleMessage) сообщения для проверки разных сценариев.

    Args:
        message_accessible: Если True — message будет доступным Message,
                           иначе — InaccessibleMessage.
    """

    def __init__(self, message_accessible=True):
        self.from_user = User(
            id=123, is_bot=False, first_name="Test", username="testuser"
        )

        if message_accessible:
            self.message = MockMessage()
        else:
            # Simulate InaccessibleMessage
            self.message = InaccessibleMessage(
                message_id=1, date=0, chat=Chat(id=123, type="private")
            )

        self.bot = MockBot()

    async def answer(self, text=None, show_alert=None):
        """Имитация ответа на callback-запрос."""
        self._answered = True
        return True


class MockFSMContext:
    """
    Мок-объект контекста FSM для тестирования.

    Хранит состояние и данные в оперативной памяти вместо реального
    хранилища aiogram FSM.

    Атрибуты:
        _data: Словарь с данными состояния.
    """

    def __init__(self):
        self._data = {}

    async def set_state(self, state):
        """Устанавливает текущее состояние."""
        self._data["state"] = state

    async def update_data(self, **kwargs):
        """Обновляет данные состояния."""
        self._data.update(kwargs)

    async def clear(self):
        """Очищает все данные состояния."""
        self._data.clear()

    async def get_state(self):
        """Возвращает текущее состояние."""
        return self._data.get("state")

    async def get_data(self):
        """Возвращает копию данных состояния."""
        return self._data.copy()


@pytest.mark.asyncio
async def test_callback_fast_order_accessible_message():
    """
    Тест: обработка callback быстрого заказа с доступным сообщением.

    Проверяет, что при нажатии кнопки "Я постоянный клиент" с доступным
    для редактирования сообщением:
        - Текст сообщения изменяется (edit_text вызывается).
        - В отредактированном тексте есть приветствие "Я постоянный клиент".
        - Состояние FSM устанавливается в OrderState.fast_order_waiting.
    """
    callback = MockCallback(message_accessible=True)
    state = MockFSMContext()

    # Import and run the handler
    from handlers.fast_order import callback_fast_order

    await callback_fast_order(callback, state)

    # Verify message was edited
    # Type check to satisfy Pylance - we know it's MockMessage since message_accessible=True
    assert isinstance(callback.message, MockMessage)
    assert hasattr(callback.message, "_edited_text")
    assert callback.message._edited_text is not None
    assert "Я постоянный клиент" in callback.message._edited_text
    # Verify state was set
    assert state._data.get("state") == OrderState.fast_order_waiting


@pytest.mark.asyncio
async def test_callback_fast_order_inaccessible_message():
    """
    Тест: обработка callback быстрого заказа с недоступным сообщением.

    Проверяет, что при нажатии кнопки "Я постоянный клиент" с недоступным
    для редактирования сообщением (InaccessibleMessage):
        - Сообщение отправляется заново через bot.send_message.
        - В отправленном тексте есть приветствие "Я постоянный клиент".
        - Состояние FSM устанавливается в OrderState.fast_order_waiting.
    """
    callback = MockCallback(message_accessible=False)
    state = MockFSMContext()

    # Import and run the handler
    from handlers.fast_order import callback_fast_order

    await callback_fast_order(callback, state)

    # Verify message was sent via bot
    assert callback.bot._mock_message_sent is not None
    assert "Я постоянный клиент" in callback.bot._mock_message_sent["text"]
    # Verify state was set
    assert state._data.get("state") == OrderState.fast_order_waiting


@pytest.mark.asyncio
async def test_process_fast_order():
    """
    Тест: обработка сообщения быстрого заказа.

    Проверяет, что при отправке пользователем данных для быстрого заказа:
        - Сообщение пересылается менеджеру с пометкой "БЫСТРЫЙ ЗАКАЗ".
        - Текст сообщения пользователя включён в пересылаемое сообщение.
    """
    message = MockMessage(text="Test order: passport", chat_id=123)
    state = MockFSMContext()
    state._data["state"] = OrderState.fast_order_waiting

    # Import and run the handler
    from handlers.fast_order import process_fast_order

    with patch("handlers.fast_order.ROUTING", {"default": 555555555}):
        await process_fast_order(message, state)

    # Verify message was forwarded to manager
    assert message.bot._mock_message_sent is not None
    assert "БЫСТРЫЙ ЗАКАЗ" in message.bot._mock_message_sent["text"]
    assert "Test order: passport" in message.bot._mock_message_sent["text"]


if __name__ == "__main__":
    import asyncio

    async def run_tests():
        print("Running tests...")

        # Test 1: Accessible message
        print("\n=== Test 1: Accessible message ===")
        callback = MockCallback(message_accessible=True)
        state = MockFSMContext()
        from handlers.fast_order import callback_fast_order

        await callback_fast_order(callback, state)
        print(f"✓ Message edited: {'_edited_text' in dir(callback.message)}")
        print(
            f"✓ State set: {state._data.get('state') == OrderState.fast_order_waiting}"
        )

        # Test 2: Inaccessible message
        print("\n=== Test 2: Inaccessible message ===")
        callback2 = MockCallback(message_accessible=False)
        state2 = MockFSMContext()
        await callback_fast_order(callback2, state2)
        print(f"✓ Message sent via bot: {callback2.bot._mock_message_sent is not None}")
        print(
            f"✓ State set: {state2._data.get('state') == OrderState.fast_order_waiting}"
        )

        # Test 3: Process fast order
        print("\n=== Test 3: Process fast order ===")
        message = MockMessage(text="Test order", chat_id=123)
        state3 = MockFSMContext()
        state3._data["state"] = OrderState.fast_order_waiting
        from handlers.fast_order import process_fast_order

        with patch("handlers.fast_order.ROUTING", {"default": 555555555}):
            await process_fast_order(message, state3)
        mock_msg = message.bot._mock_message_sent
        assert mock_msg is not None
        print(f"✓ Message forwarded: {'БЫСТРЫЙ ЗАКАЗ' in mock_msg['text']}")

        print("\n=== All tests passed! ===")

    asyncio.run(run_tests())
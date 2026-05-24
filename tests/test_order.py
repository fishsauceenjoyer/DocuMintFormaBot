"""
Тесты для основного флоу заказа (order handlers).

Проверяет:
    - Выбор типа документа
    - Выбор количества
    - Заполнение полей документа
    - Выбор доставки
    - Выбор способа оплаты
    - Ожидание подтверждения оплаты
"""

import datetime

import pytest
from aiogram.types import Chat, Message, User

from fsm.states import OrderState

# Import handlers early to avoid async fixture issues
from handlers.order import process_document_choice
from handlers.order import process_quantity
from handlers.order import process_delivery_choice


@pytest.mark.asyncio
async def test_callback_document_choice_sanepid(mock_callback, mock_fsm, clean_user_sessions):
    """
    Тест: выбор документа "Санэпид" из списка доступных.

    Проверяет:
        - Текст сообщения содержит название шаблона
        - Текст сообщения содержит цену
        - Состояние FSM устанавливается в entering_quantity
    """
    mock_callback.data = "doc_sanepid"

    await process_document_choice(mock_callback, mock_fsm)

    # Verify message was edited with template info
    assert mock_callback.message._edited_text is not None
    assert "Санэпид" in mock_callback.message._edited_text
    assert "150" in mock_callback.message._edited_text  # price
    # Verify state
    assert mock_fsm._data.get("state") == OrderState.entering_quantity


@pytest.mark.asyncio
async def test_callback_document_choice_bhp(mock_callback, mock_fsm, clean_user_sessions):
    """
    Тест: выбор документа "BHP" из списка доступных.

    Проверяет корректную загрузку другого типа документа.
    """
    mock_callback.data = "doc_bhp"

    await process_document_choice(mock_callback, mock_fsm)

    assert mock_callback.message._edited_text is not None
    assert "BHP" in mock_callback.message._edited_text
    assert "100" in mock_callback.message._edited_text  # BHP price
    assert mock_fsm._data.get("state") == OrderState.entering_quantity


@pytest.mark.asyncio
async def test_callback_document_choice_invalid(mock_callback, mock_fsm, clean_user_sessions):
    """
    Тест: выбор несуществующего документа.

    Проверяет, что при неверном типе документа вызывается answer с ошибкой.
    """
    mock_callback.data = "doc_nonexistent"

    await process_document_choice(mock_callback, mock_fsm)

    # Template not found - should answer with error
    assert mock_callback._answered is True


@pytest.mark.asyncio
async def test_callback_quantity_selection(mock_callback, mock_fsm, clean_user_sessions):
    """
    Тест: выбор количества документов (3 экземпляра).

    Проверяет:
        - Состояние FSM устанавливается в filling_document
        - Сессия пользователя обновляется
    """
    # First make a document choice to set up the session
    mock_callback.data = "doc_sanepid"
    await process_document_choice(mock_callback, mock_fsm)

    # Now select quantity
    mock_callback.data = "qty_3"
    await process_quantity(mock_callback, mock_fsm)

    # Verify state
    assert mock_fsm._data.get("state") == OrderState.filling_document


@pytest.mark.asyncio
async def test_callback_delivery_yes(mock_callback, mock_fsm, clean_user_sessions):
    """
    Тест: выбор доставки "Нужна доставка".

    Проверяет, что состояние FSM устанавливается в filling_delivery.
    """
    mock_callback.data = "delivery_yes"
    mock_callback.message = Message(
        message_id=1,
        date=datetime.datetime.now(),
        chat=Chat(id=123, type="private"),
        from_user=User(id=123, is_bot=False, first_name="Test"),
        text="test",
    )

    await process_delivery_choice(mock_callback, mock_fsm)

    # Check that state is filling_delivery
    assert mock_fsm._data.get("state") == OrderState.filling_delivery


@pytest.mark.asyncio
async def test_callback_delivery_no(mock_callback, mock_fsm, clean_user_sessions):
    """
    Тест: выбор "Самовывоз (без доставки)".

    Проверяет, что состояние FSM устанавливается в choosing_payment.
    """
    mock_callback.data = "delivery_no"
    mock_callback.message = Message(
        message_id=1,
        date=datetime.datetime.now(),
        chat=Chat(id=123, type="private"),
        from_user=User(id=123, is_bot=False, first_name="Test"),
        text="test",
    )

    await process_delivery_choice(mock_callback, mock_fsm)

    # Check that state is choosing_payment (skip to payment)
    assert mock_fsm._data.get("state") == OrderState.choosing_payment
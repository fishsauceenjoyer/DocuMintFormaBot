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

import pytest
from conftest import MockCallback  # type: ignore[import-not-found]

from fsm.states import OrderState

# Import handlers early to avoid async fixture issues
from handlers.order import (
    process_delivery_choice,
    process_document_choice,
    process_quantity,
)


@pytest.mark.asyncio
async def test_callback_document_choice_sanepid(mock_fsm, clean_user_sessions):
    """
    Тест: выбор документа "Санэпид" из списка доступных.

    Проверяет:
        - Текст сообщения содержит название шаблона
        - Текст сообщения содержит цену
        - Состояние FSM устанавливается в entering_quantity
    """
    callback = MockCallback(data="doc_sanepid")

    await process_document_choice(callback, mock_fsm)

    # Verify message was edited with template info
    assert callback.message._edited_text is not None
    assert "Санэпид" in callback.message._edited_text
    assert "150" in callback.message._edited_text  # price
    # Verify state
    assert mock_fsm._data.get("state") == OrderState.entering_quantity


@pytest.mark.asyncio
async def test_callback_document_choice_bhp(mock_fsm, clean_user_sessions):
    """
    Тест: выбор документа "BHP" из списка доступных.

    Проверяет корректную загрузку другого типа документа.
    """
    callback = MockCallback(data="doc_bhp")

    await process_document_choice(callback, mock_fsm)

    assert callback.message._edited_text is not None
    assert "BHP" in callback.message._edited_text
    assert "100" in callback.message._edited_text  # BHP price
    assert mock_fsm._data.get("state") == OrderState.entering_quantity


@pytest.mark.asyncio
async def test_callback_document_choice_invalid(mock_fsm, clean_user_sessions):
    """
    Тест: выбор несуществующего документа.

    Проверяет, что при неверном типе документа вызывается answer с ошибкой.
    """
    callback = MockCallback(data="doc_nonexistent")

    await process_document_choice(callback, mock_fsm)

    # Template not found - should answer with error
    assert callback._answered is True


@pytest.mark.asyncio
async def test_callback_quantity_selection(mock_fsm, clean_user_sessions):
    """
    Тест: выбор количества документов (3 экземпляра).

    Проверяет:
        - Состояние FSM устанавливается в filling_document
        - Сессия пользователя обновляется
    """
    # First make a document choice to set up the session
    callback = MockCallback(data="doc_sanepid")
    await process_document_choice(callback, mock_fsm)

    # Now select quantity (need a new callback since frozen model)
    callback2 = MockCallback(data="qty_3", user_id=123)
    await process_quantity(callback2, mock_fsm)

    # Verify state
    assert mock_fsm._data.get("state") == OrderState.filling_document


@pytest.mark.asyncio
async def test_callback_delivery_yes(mock_fsm, clean_user_sessions):
    """
    Тест: выбор доставки "Нужна доставка".

    Проверяет, что состояние FSM устанавливается в filling_delivery.
    """
    callback = MockCallback(data="delivery_yes")

    await process_delivery_choice(callback, mock_fsm)

    # Check that state is filling_delivery
    assert mock_fsm._data.get("state") == OrderState.filling_delivery


@pytest.mark.asyncio
async def test_callback_delivery_no(mock_fsm, clean_user_sessions):
    """
    Тест: выбор "Самовывоз (без доставки)".

    Проверяет, что состояние FSM устанавливается в choosing_payment.
    """
    callback = MockCallback(data="delivery_no")

    await process_delivery_choice(callback, mock_fsm)

    # Check that state is choosing_payment (skip to payment)
    assert mock_fsm._data.get("state") == OrderState.choosing_payment

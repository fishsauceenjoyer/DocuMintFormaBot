"""
FSM состояния (Finite State Machine) для управления диалогами бота.

Каждый класс StatesGroup представляет собой группу состояний,
через которые проходит пользователь при выполнении определённого
сценария (оформление заказа, администрирование).
"""

from aiogram.fsm.state import State, StatesGroup


class OrderState(StatesGroup):
    """
    Состояния для основного сценария оформления заказа.

    Последовательность:
        1. choosing_document — выбор типа документа из списка
        2. entering_quantity — выбор количества экземпляров (1-5)
        3. filling_document — заполнение полей выбранного документа
        4. asking_delivery — запрос: нужна ли доставка?
        5. filling_delivery — ввод данных для доставки (ФИО, телефон, адрес)
        6. choosing_payment — выбор способа оплаты (Blik, гривна, USDT)
        7. waiting_for_payment_proof — ожидание фото/скриншота чека оплаты
        8. fast_order_waiting — ожидание данных для быстрого заказа (без обработки)
    """

    choosing_document = State()
    entering_quantity = State()
    filling_document = State()
    asking_delivery = State()
    filling_delivery = State()
    choosing_payment = State()
    waiting_for_payment_proof = State()
    fast_order_waiting = State()


class AdminState(StatesGroup):
    """
    Состояния для сценариев работы менеджера/администратора.

    Состояния:
        - waiting_for_tracking: менеджер вводит трек-номер для отправки клиенту
        - waiting_for_file: менеджер отправляет готовый файл документа
        - waiting_for_order_id: менеджер вводит номер заказа для поиска
    """

    waiting_for_tracking = State()
    waiting_for_file = State()
    waiting_for_order_id = State()

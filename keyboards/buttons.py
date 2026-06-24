"""
Inline keyboard definitions for the Telegram bot.

Each function returns an :class:`InlineKeyboardMarkup` used in different
contexts: document type selection, quantity, delivery, payment, cart
actions, and manager actions.
"""

from typing import List, Tuple

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def document_keyboard(
    docs: List[Tuple[str, str]],
) -> InlineKeyboardMarkup:
    """
    Клавиатура для выбора типа документа.

    Создаёт кнопки для каждого доступного типа документа.
    Внизу добавляет кнопку "Связь с менеджером".

    Args:
        docs: Список кортежей (код_документа, название).

    Returns:
        InlineKeyboardMarkup с кнопками выбора документа.
    """
    buttons = []
    for doc_type, doc_name in docs:
        buttons.append(
            [InlineKeyboardButton(text=doc_name, callback_data=f"doc_{doc_type}")]
        )
    buttons.append(
        [
            InlineKeyboardButton(
                text="🆘 Связь с менеджером", callback_data="help_manager"
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def quantity_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для выбора количества документов (от 1 до 5).

    Кнопки расположены в один ряд с цифрами 1, 2, 3, 4, 5.
    Внизу добавляет кнопку "Связь с менеджером".

    Returns:
        InlineKeyboardMarkup с кнопками выбора количества.
    """
    buttons = []
    row = [
        InlineKeyboardButton(text=str(i), callback_data=f"qty_{i}") for i in range(1, 6)
    ]
    buttons.append(row)
    buttons.append(
        [
            InlineKeyboardButton(
                text="🆘 Связь с менеджером", callback_data="help_manager"
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def delivery_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для выбора способа получения: доставка или самовывоз.

    Предлагает два варианта:
        - "Нужна доставка" (доставка InPost)
        - "Самовывоз (без доставки)"

    Returns:
        InlineKeyboardMarkup с кнопками выбора доставки.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Нужна доставка", callback_data="delivery_yes"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Самовывоз (без доставки)", callback_data="delivery_no"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🆘 Связь с менеджером", callback_data="help_manager"
                )
            ],
        ]
    )


def payment_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для выбора способа оплаты.

    Предлагает три метода оплаты:
        - Blik за номером телефона
        - Перевод на гривневую карту ПриватБанк
        - Криптовалюта USDt (TRC20)

    Returns:
        InlineKeyboardMarkup с кнопками выбора оплаты.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Blik за номером", callback_data="pay_blik")],
            [InlineKeyboardButton(text="🇺🇦 Оплата гривнею", callback_data="pay_uah")],
            [
                InlineKeyboardButton(
                    text="₿ Криптовалюта USDt", callback_data="pay_usdt"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🆘 Связь с менеджером", callback_data="help_manager"
                )
            ],
        ]
    )


def manager_order_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """
    Клавиатура для действий менеджера с заказом.

    Предлагает три действия:
        - "Отправить готовый документ" — загрузить файл документа
        - "Отправить трек-номер" — ввести трек-номер отслеживания
        - "Заказ выполнен" — отметить заказ как выполненный

    Args:
        order_id: Номер заказа для формирования callback_data.

    Returns:
        InlineKeyboardMarkup с кнопками действий менеджера.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📎 Отправить готовый документ",
                    callback_data=f"send_doc_{order_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📦 Отправить трек-номер",
                    callback_data=f"send_track_{order_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Заказ выполнен", callback_data=f"order_done_{order_id}"
                )
            ],
        ]
    )


def cart_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для действий с корзиной заказа.

    Предлагает действия:
        - "Перейти к оплате" — оформление заказа
        - "Добавить ещё документ" — добавить ещё один тип документа
        - "Очистить корзину" — сбросить все позиции
        - "Связь с менеджером" — запросить помощь

    Returns:
        InlineKeyboardMarkup с кнопками управления корзиной.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💰 Перейти к оплате", callback_data="cart_checkout"
                )
            ],
            [
                InlineKeyboardButton(
                    text="➕ Добавить ещё документ", callback_data="cart_add_more"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Очистить корзину", callback_data="cart_clear"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🆘 Связь с менеджером", callback_data="help_manager"
                )
            ],
        ]
    )


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура главного меню бота.

    Предлагает три основных действия:
        - "Новый заказ" — начать оформление заказа
        - "Я постоянный клиент" — быстрый заказ без обработки
        - "Связь с менеджером" — запросить помощь менеджера

    Returns:
        InlineKeyboardMarkup с кнопками главного меню.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Новый заказ", callback_data="new_order")],
            [
                InlineKeyboardButton(
                    text="👤 Я постоянный клиент", callback_data="fast_order"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🆘 Связь с менеджером", callback_data="help_manager"
                )
            ],
        ]
    )


def confirm_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура подтверждения действия.

    Предлагает выбрать "Подтвердить" или "Отмена".

    Returns:
        InlineKeyboardMarkup с кнопками подтверждения/отмены.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_yes")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="confirm_no")],
        ]
    )


def back_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура с одной кнопкой "Назад".

    Используется для возврата к предыдущему шагу в различных сценариях.

    Returns:
        InlineKeyboardMarkup с кнопкой "Назад".
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back")]]
    )

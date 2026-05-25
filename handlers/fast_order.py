"""Fast order handlers for regular clients (only Russian)."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InaccessibleMessage, Message

from config import ROUTING
from fsm.states import OrderState

router = Router()


@router.callback_query(F.data == "fast_order")
async def callback_fast_order(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие кнопки "Я постоянный клиент" (быстрый заказ).

    Запрашивает у пользователя логин или номер телефона для верификации.
    После ввода данных заказ будет отправлен менеджеру без предоплаты.
    Переводит пользователя в состояние ожидания ввода данных для быстрого заказа.

    Args:
        callback: CallbackQuery с data == "fast_order".
        state: Контекст FSM для установки состояния fast_order_waiting.
    """
    user = callback.from_user
    user_id = user.id

    text = (
        "👤 **Я постоянный клиент**\n\n"
        "Введите ваш логин или номер телефона, который вы используете "
        "для постоянных заказов.\n\n"
        "После верификации вы сможете отправить заказ одним сообщением."
    )

    if callback.message is not None and not isinstance(
        callback.message, InaccessibleMessage
    ):
        try:
            await callback.message.edit_text(text)
        except Exception:
            await callback.message.answer(text)
    else:
        bot = callback.bot
        if bot is not None:
            await bot.send_message(chat_id=user_id, text=text)

    await state.set_state(OrderState.fast_order_waiting)
    await state.update_data(current_step="Верификация постоянного клиента")
    await callback.answer()


@router.message(OrderState.fast_order_waiting)
async def process_fast_order(message: Message, state: FSMContext):
    """
    Обрабатывает сообщение с данными для быстрого заказа.

    Пересылает полученные данные напрямую менеджеру без обработки
    и без ожидания оплаты. Менеджер обрабатывает заказ вручную.

    Args:
        message: Текстовое сообщение с данными заказа от клиента.
        state: Контекст FSM (очищается после отправки).
    """
    user = message.from_user
    if user is None:
        await message.answer("⚠️ Не удалось получить информацию о пользователе.")
        return

    user_id = user.id
    target = ROUTING["default"]

    bot = message.bot
    if bot is None:
        await message.answer("⚠️ Ошибка бота. Попробуйте ещё раз.")
        return

    text = (
        f"⚡ **БЫСТРЫЙ ЗАКАЗ (Постоянный клиент)**\n\n"
        f"👤 Клиент: @{user.username} (ID: {user_id})\n"
        f"📝 Данные от клиента:\n\n"
        f"```\n{message.text}\n```\n\n"
        f"⚠️ Без оплаты - требует ручной проверки менеджером"
    )

    await bot.send_message(chat_id=target, text=text, parse_mode="Markdown")

    await message.answer(
        "✅ **Ваш запрос отправлен менеджеру!**\n\n"
        "📞 В ближайшее время он свяжется с вами для подтверждения заказа "
        "и уточнения деталей оплаты.\n\n"
        "Спасибо! 👋"
    )

    await state.clear()


@router.message(Command("fast"))
async def cmd_fast_order(message: Message, state: FSMContext):
    """
    Альтернативная команда /fast для оформления быстрого заказа.

    Показывает инструкцию: отправить одним сообщением все данные.
    Менеджер свяжется с клиентом для подтверждения.

    Args:
        message: Сообщение от пользователя с командой /fast.
        state: Контекст FSM для установки состояния fast_order_waiting.
    """
    user = message.from_user
    if user is None:
        await message.answer("⚠️ Не удалось получить информацию о пользователе.")
        return

    await message.answer(
        "⚡ **Быстрый заказ**\n\n"
        "Отправьте одним сообщением всё, что вам нужно:\n"
        "- Какие документы\n"
        "- Данные для каждого документа\n"
        "- Доставка (если нужна)\n\n"
        "Менеджер свяжется с вами для подтверждения."
    )
    await state.set_state(OrderState.fast_order_waiting)
    await state.update_data(current_step="Быстрый заказ")

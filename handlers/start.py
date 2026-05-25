"""Start command and main menu handlers (only Russian)."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InaccessibleMessage, Message

from fsm.states import OrderState
from keyboards.buttons import main_menu_keyboard

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """
    Обрабатывает команду /start — начало работы с ботом.

    Очищает предыдущее состояние пользователя (если он был в процессе заказа),
    сразу показывает главное меню с доступными действиями.
    Язык интерфейса — только русский.

    Args:
        message: Сообщение от пользователя с командой /start.
        state: Контекст FSM, который очищается в начале обработки.
    """
    await state.clear()
    await message.answer(
        "👋 Добро пожаловать в бот оформления документов!\n\nВыберите действие:",
        reply_markup=main_menu_keyboard(),
    )
    await state.set_state(OrderState.choosing_document)


@router.callback_query(F.data == "new_order")
async def callback_new_order(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие кнопки "Новый заказ" в главном меню.

    Загружает список доступных шаблонов документов,
    показывает их пользователю в виде инлайн-кнопок и переводит
    в состояние выбора типа документа.

    Args:
        callback: CallbackQuery с data == "new_order".
        state: Контекст FSM.
    """
    from keyboards.buttons import document_keyboard
    from templates.documents import get_all_templates

    docs = get_all_templates()

    text = (
        "📋 **Выберите документ для заказа:**\n\n"
        "Также вы можете воспользоваться кнопкой 'Связь с менеджером'"
    )

    if callback.message is None or callback.bot is None:
        await callback.answer()
        return

    if isinstance(callback.message, InaccessibleMessage):
        await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text=text,
            reply_markup=document_keyboard(docs),
        )
    else:
        await callback.message.edit_text(text, reply_markup=document_keyboard(docs))
    await state.set_state(OrderState.choosing_document)
    await callback.answer()


@router.callback_query(F.data == "help_manager")
async def callback_help_manager(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие кнопки "Связь с менеджером".

    Пересылает запрос пользователя менеджеру в служебный чат через
    функцию forward_to_manager. Показывает пользователю уведомление
    о том, что его запрос передан и менеджер скоро свяжется с ним.

    Args:
        callback: CallbackQuery с data == "help_manager".
        state: Контекст FSM для определения текущего шага пользователя.
    """
    from utils.router import forward_to_manager

    user = callback.from_user
    data = await state.get_data()
    current_step = data.get("current_step", "Главное меню")

    if callback.bot is None:
        await callback.answer()
        return

    await forward_to_manager(
        bot=callback.bot,
        user_id=user.id,
        username=user.username or "unknown",
        message_text="Нажал кнопку 'Связь с менеджером'",
        current_step=current_step,
    )

    await callback.answer(
        "📞 Мы направили ваш запрос менеджеру.\n\nВ ближайшее время он свяжется с вами.",
        show_alert=True,
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    """
    Обрабатывает команду /menu — возврат в главное меню.

    Очищает состояние пользователя (сбрасывает текущий заказ)
    и показывает главное меню с доступными действиями.

    Args:
        message: Сообщение от пользователя с командой /menu.
        state: Контекст FSM, который очищается для сброса заказа.
    """
    await state.clear()
    await message.answer(
        "📋 Главное меню:\n\nВыберите действие:", reply_markup=main_menu_keyboard()
    )

"""Start command and main menu handlers.

Provides the /start landing, /menu command, new-order navigation,
and the "Contact manager" button handler.
"""

import asyncio

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InaccessibleMessage, Message

from fsm.states import OrderState
from keyboards.buttons import main_menu_keyboard
from utils.i18n import get_i18n, user_language

router = Router()


async def _clear_user_session(user_id: int):
    """Clean up the user session from order.py module."""
    try:
        from handlers.order import _sessions_lock, user_sessions

        async with _sessions_lock:
            user_sessions.pop(user_id, None)
    except (ImportError, KeyError):
        pass


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start — entry point of the bot.

    Clears any previous state and shows the main menu.
    Language is auto-detected from the user's Telegram settings.
    """
    await state.clear()

    if message.from_user:
        await _clear_user_session(message.from_user.id)

    user = message.from_user
    lang = user_language(user) if user else "en"
    i18n = get_i18n()
    text = i18n.get("welcome", language=lang)

    await message.answer(text, reply_markup=main_menu_keyboard())
    await state.set_state(OrderState.choosing_document)


@router.callback_query(F.data == "new_order")
async def callback_new_order(callback: CallbackQuery, state: FSMContext):
    """Handle "New order" button in main menu.

    Shows the list of available document templates as inline buttons.
    """
    from keyboards.buttons import document_keyboard
    from templates.documents import get_all_templates

    docs = get_all_templates()

    user = callback.from_user
    lang = user_language(user) if user else "en"
    i18n = get_i18n()
    text = i18n.get("choose_document", language=lang)

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
    """Handle "Contact manager" button.

    Forwards the user's help request to the manager's chat.
    """
    from utils.router import forward_to_manager

    user = callback.from_user
    if user is None:
        await callback.answer()
        return

    data = await state.get_data()
    current_step = data.get("current_step", "Main menu")

    if callback.bot is None:
        await callback.answer()
        return

    await forward_to_manager(
        bot=callback.bot,
        user_id=user.id,
        username=user.username or "unknown",
        message_text="Pressed 'Contact manager' button",
        current_step=current_step,
    )

    lang = user_language(user)
    i18n = get_i18n()

    await callback.answer(
        i18n.get("help_sent", language=lang),
        show_alert=True,
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    """Handle /menu — return to the main menu.

    Clears the current order state and shows the main menu.
    """
    await state.clear()

    if message.from_user:
        await _clear_user_session(message.from_user.id)

    user = message.from_user
    lang = user_language(user) if user else "en"
    i18n = get_i18n()
    text = i18n.get("menu", language=lang)

    await message.answer(text, reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "cancel_to_menu")
async def callback_cancel_to_menu(callback: CallbackQuery, state: FSMContext):
    """Handle "В главное меню" button — cancel current flow and return to main menu."""
    await state.clear()

    if callback.from_user:
        await _clear_user_session(callback.from_user.id)

    user = callback.from_user
    lang = user_language(user) if user else "en"
    i18n = get_i18n()
    text = i18n.get("menu", language=lang)

    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=main_menu_keyboard())
    elif callback.bot:
        await callback.bot.send_message(
            callback.from_user.id, text, reply_markup=main_menu_keyboard()
        )
    await callback.answer()

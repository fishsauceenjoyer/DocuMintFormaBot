"""Fast-order handlers for regular / repeat customers.

This module provides a shortcut for known clients who can send their request
in one free-form message, bypassing the step-by-step FSM.
"""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InaccessibleMessage, Message

from config import ROUTING
from config.loader import get_loader
from fsm.states import OrderState
from utils.i18n import get_i18n, user_language

router = Router()


@router.callback_query(F.data == "fast_order")
async def callback_fast_order(callback: CallbackQuery, state: FSMContext):
    """Handle "I'm a regular customer" button (fast order).

    Asks the user to enter their login or phone number for verification,
    then forwards the request to the manager without pre-payment.
    """
    user = callback.from_user
    if user is None:
        await callback.answer()
        return

    user_id = user.id
    lang = user_language(user)
    i18n = get_i18n()
    text = i18n.get("fast_order_intro", language=lang)

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
    await state.update_data(current_step="Fast order verification")
    await callback.answer()


@router.message(OrderState.fast_order_waiting)
async def process_fast_order(message: Message, state: FSMContext):
    """Handle fast-order message from the user.

    Forwards the raw message directly to the manager for manual processing.
    """
    user = message.from_user
    if user is None:
        lang = "en"
        i18n = get_i18n()
        await message.answer(i18n.get("error_no_user_info", language=lang))
        return

    lang = user_language(user)
    i18n = get_i18n()

    # Only text messages are accepted in fast order
    if not message.text:
        await message.answer(i18n.get("error_send_text", language=lang))
        return

    user_id = user.id
    target = ROUTING["default"]

    bot = message.bot
    if bot is None:
        await message.answer(i18n.get("error_bot_error", language=lang))
        return

    from utils.sanitizer import sanitize_for_telegram

    safe_message = sanitize_for_telegram(message.text)
    safe_username = sanitize_for_telegram(user.username or "unknown")

    text = (
        f"⚡ **FAST ORDER (Repeat customer)**\n\n"
        f"👤 Client: @{safe_username} (ID: {user_id})\n"
        f"📝 Client message:\n\n"
        f"```\n{safe_message}\n```\n\n"
        f"⚠️ Unpaid — requires manual check by manager"
    )

    await bot.send_message(chat_id=target, text=text, parse_mode="Markdown")

    lang = user_language(user)
    i18n = get_i18n()

    from keyboards.buttons import main_menu_keyboard

    await message.answer(
        i18n.get("fast_order_sent", language=lang), reply_markup=main_menu_keyboard()
    )

    await state.clear()


@router.message(Command("fast"))
async def cmd_fast_order(message: Message, state: FSMContext):
    """Alternative /fast command for fast order.

    Shows instructions and enters the fast-order waiting state.
    """
    user = message.from_user
    if user is None:
        i18n = get_i18n()
        await message.answer(i18n.get("error_no_user_info", language="en"))
        return

    lang = user_language(user)
    i18n = get_i18n()

    await message.answer(i18n.get("fast_order_cmd", language=lang))
    await state.set_state(OrderState.fast_order_waiting)
    await state.update_data(current_step="Fast order")

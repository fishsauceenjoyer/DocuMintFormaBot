"""Customer order flow handlers.

This module contains the main FSM path: document selection, quantity, form
fields, delivery, payment choice, payment proof, manager notification, and
database persistence. Temporary in-progress cart data lives in user_sessions;
completed orders are saved through db.crud.
"""

import asyncio
import logging
import secrets
from datetime import datetime, timezone
from typing import Any, Dict

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from config import DELIVERY_PRICE_EUR, DELIVERY_PRICE_PLN

# Import DB functions (lazy — imported inside handlers to avoid circular imports)
from db.crud import AsyncSessionLocal, create_order, create_order_item
from db.models import Order
from fsm.states import OrderState
from keyboards.buttons import choice_keyboard, delivery_keyboard, quantity_keyboard
from templates.documents import get_template
from utils.i18n import get_i18n, user_language

router = Router()

# Temporary user session storage (in production — use DB / Redis)
user_sessions: Dict[int, Dict[str, Any]] = {}
_sessions_lock = asyncio.Lock()

# ── Currency selection ──────────────────────────────────────────────
# For the demo, default to EUR. Change this logic as needed.
DEFAULT_CURRENCY = "EUR"


def _currency_symbol(currency: str) -> str:
    return "€" if currency == "EUR" else "zł"


def _currency_price(currency: str, doc_code: str) -> int:
    """Return the price for a document in the requested currency."""
    from data.business_config import get_price_eur, get_price_pln

    if currency == "EUR":
        return get_price_eur(doc_code)
    return get_price_pln(doc_code)


def _delivery_price(currency: str) -> int:
    return DELIVERY_PRICE_EUR if currency == "EUR" else DELIVERY_PRICE_PLN


async def _generate_order_id() -> str:
    """Generate a unique order ID with collision checking.

    Format: ORDER_YYYYMMDD_XXXX (date + 4 random hex chars).
    """
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    max_attempts = 5
    for _ in range(max_attempts):
        suffix = secrets.token_hex(2).upper()
        order_id = f"ORDER_{today}_{suffix}"

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Order).where(Order.order_id == order_id))
            if result.scalar_one_or_none() is None:
                return order_id

    suffix = secrets.token_hex(4).upper()
    return f"ORDER_{today}_{suffix}"


async def get_user_session(user_id: int) -> Dict[str, Any]:
    """Return the user session, creating a new one if necessary.

    Args:
        user_id: Telegram user ID.

    Returns:
        Session dictionary.
    """
    async with _sessions_lock:
        if user_id not in user_sessions:
            user_sessions[user_id] = {
                "cart": [],
                "current_doc_type": None,
                "current_template": None,
                "current_quantity": 0,
                "current_items": [],
                "temp_item_data": {},
                "current_field_index": 0,
                "current_item_index": 0,
                "delivery": None,
                "payment_method": None,
                "total_price": 0,
                "currency": DEFAULT_CURRENCY,
            }
        return user_sessions[user_id]


def _doc_name(template: Dict[str, Any], language: str) -> str:
    """Return the document name in the requested language.

    Falls back: language → en → ru → first found.
    """
    for key in (f"name_{language}", "name_en", "name_ru"):
        val = template.get(key)
        if val:
            return val
    # Ultimate fallback: any name_* key
    for k, v in template.items():
        if k.startswith("name_"):
            return v
    return template.get("code", "Unknown")


def calculate_total_price(session: Dict[str, Any]) -> int:
    """Calculate the total order price including delivery.

    Args:
        session: User session dictionary.

    Returns:
        Total price in the session's currency.
    """
    currency = session.get("currency", DEFAULT_CURRENCY)
    total = 0
    for item in session.get("cart", []):
        price = _currency_price(currency, item["type"])
        total += price * item["quantity"]

    if session.get("delivery"):
        total += _delivery_price(currency)

    return total


@router.message(OrderState.choosing_document)
async def fallback_choosing_document(message: Message, state: FSMContext):
    """Fallback: user sent text instead of choosing a document button."""
    if not message.from_user:
        return
    lang = user_language(message.from_user)
    i18n = get_i18n()
    await message.answer(i18n.get("error_use_buttons", language=lang))


@router.callback_query(OrderState.choosing_document, F.data.startswith("doc_"))
async def process_document_choice(callback: CallbackQuery, state: FSMContext):
    """Handle document type selection.

    Loads the template, shows price info and asks for quantity.
    """
    if not callback.data or not callback.from_user:
        await callback.answer("❌ Error processing request")
        return

    # The callback data format is "doc_{doc_type}" where doc_type may contain underscores
    # e.g. "doc_criminal_record_check" -> doc_type = "criminal_record_check"
    # Using split with maxsplit=1 to handle multi-part document codes
    parts = callback.data.split("_", 1)
    if len(parts) < 2:
        await callback.answer("❌ Error processing request")
        return
    doc_type = parts[1]
    template = get_template(doc_type)
    if not template:
        await callback.answer("❌ Template not found")
        return

    user_id = callback.from_user.id
    session = await get_user_session(user_id)
    lang = user_language(callback.from_user)

    session["current_doc_type"] = doc_type
    session["current_template"] = template
    session["current_items"] = []
    session["temp_item_data"] = {}
    session["current_field_index"] = 0

    currency = session.get("currency", DEFAULT_CURRENCY)
    price = _currency_price(currency, doc_type)
    sym = _currency_symbol(currency)
    name = _doc_name(template, lang)

    await state.update_data(current_step=f"Quantity: {name}")

    i18n = get_i18n()
    text = i18n.get(
        "choose_quantity",
        language=lang,
        name=name,
        price=price,
        currency=sym,
    )

    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=quantity_keyboard())
    elif callback.bot:
        await callback.bot.send_message(
            callback.from_user.id, text, reply_markup=quantity_keyboard()
        )
    await state.set_state(OrderState.entering_quantity)
    await callback.answer()


@router.message(OrderState.entering_quantity)
async def fallback_entering_quantity(message: Message, state: FSMContext):
    """Fallback: user sent text instead of choosing quantity."""
    if not message.from_user:
        return
    lang = user_language(message.from_user)
    i18n = get_i18n()
    await message.answer(i18n.get("error_use_buttons", language=lang))


@router.callback_query(OrderState.entering_quantity, F.data.startswith("qty_"))
async def process_quantity(callback: CallbackQuery, state: FSMContext):
    """Handle quantity selection (1–5)."""
    if (
        not callback.data
        or not isinstance(callback.message, Message)
        or not callback.from_user
    ):
        await callback.answer("❌ Error processing request")
        return

    try:
        quantity = int(callback.data.split("_")[1])
    except (ValueError, IndexError):
        await callback.answer("❌ Некорректное количество")
        return

    # Boundary check: the keyboard only offers 1–5, but guard against
    # crafted callback_data (qty_0, qty_6, qty_99, …).
    if quantity < 1 or quantity > 5:
        await callback.answer(
            "❌ Можно заказать от 1 до 5 документов.", show_alert=True
        )
        return

    user_id = callback.from_user.id
    session = await get_user_session(user_id)

    session["current_quantity"] = quantity
    session["current_items"] = []
    session["current_field_index"] = 0

    await ask_document_fields(callback.message, user_id, state)
    await state.set_state(OrderState.filling_document)
    await callback.answer()


async def ask_document_fields(message: Message, user_id: int, state: FSMContext):
    """Recursively ask the user to fill in document fields."""
    session = await get_user_session(user_id)
    template = session["current_template"]

    if not template:
        return

    fields = template["fields"]
    current_index = session.get("current_field_index", 0)

    if current_index >= len(fields):
        # All fields for this document instance are filled
        session["current_items"].append(session["temp_item_data"].copy())
        session["temp_item_data"] = {}

        if len(session["current_items"]) < session["current_quantity"]:
            session["current_field_index"] = 0
            await ask_document_fields(message, user_id, state)
        else:
            # Add to cart
            session["cart"].append(
                {
                    "type": session["current_doc_type"],
                    "quantity": session["current_quantity"],
                    "items": session["current_items"].copy(),
                }
            )

            user = message.from_user
            lang = user_language(user) if user else "en"
            i18n = get_i18n()
            name = _doc_name(template, lang)

            text = i18n.get(
                "doc_added",
                language=lang,
                quantity=session["current_quantity"],
                name=name,
            )

            await message.answer(text, reply_markup=delivery_keyboard())
            await state.set_state(OrderState.asking_delivery)
            await state.update_data(current_step="Delivery selection")
        return

    field = fields[current_index]
    prompt = field.prompt
    optional_note = ""
    if field.optional:
        user = message.from_user
        lang = user_language(user) if user else "en"
        i18n = get_i18n()
        optional_note = i18n.get("field_optional", language=lang)

    # Add type/length hint to the prompt
    type_hint = field.type_hint()

    # Build progress indicator: document X of Y
    current_doc_num = len(session["current_items"]) + 1
    total_docs = session["current_quantity"]
    progress_str = f"📄 *Документ {current_doc_num} из {total_docs}*"

    # Build summary of already-entered fields for the current document
    entered_fields = session.get("temp_item_data", {})
    summary_lines = []
    for i, f in enumerate(fields):
        if f.id in entered_fields:
            summary_lines.append(f"  ✅ {i+1}. {f.prompt}: {entered_fields[f.id]}")
        elif i < current_index:
            # Field was skipped or not yet filled
            summary_lines.append(f"  ⏭ {i+1}. {f.prompt}: (пропущено)")
    summary_text = ""
    if summary_lines:
        summary_text = "\n📋 *Заполнено:*\n" + "\n".join(summary_lines) + "\n"

    # Build current field indicator with visual progress bar
    field_indicator = f"📝 Поле {current_index + 1} из {len(fields)}"
    progress_bar = "█" * (current_index + 1) + "░" * (len(fields) - current_index - 1)

    text = (
        f"{progress_str}\n"
        f"{summary_text}\n"
        f"\n"
        f"{field_indicator} [{progress_bar}]\n\n"
        f"{prompt}{optional_note}\n\n"
        f"💡 *Подсказка:* {type_hint}\n\n"
        "Отправьте ответ одним сообщением."
    )

    # For "choice" fields, show an inline keyboard with the allowed options.
    if field.type == "choice" and field.choices:
        await message.answer(
            text,
            reply_markup=choice_keyboard(field.choices, field.id),
        )
    else:
        await message.answer(text)

    await state.update_data(current_field_index=current_index)
    session["current_field_index"] = current_index


async def _notify_admin_validation_error(
    message: Any,
    user_id: int,
    field_name: str,
    field_type: str,
    raw_value: str,
    error_message: str,
):
    """Send a validation error notification to the admin.

    Args:
        message: The user's original message.
        user_id: Telegram user ID.
        field_name: The field ID that failed validation.
        field_type: The expected field type.
        raw_value: The raw input that failed.
        error_message: The validation error description.
    """
    logger = logging.getLogger(__name__)
    try:
        from config import ROUTING

        target = ROUTING.get("default")
        if target is None or message.bot is None:
            logger.warning("Cannot notify admin: no default routing or bot")
            return

        username = message.from_user.username if message.from_user else "unknown"
        from utils.sanitizer import sanitize_for_telegram

        # Only user-supplied values need sanitization; field_name / field_type
        # are internal constants and stay readable in the notification.
        text = (
            f"⚠️ **Ошибка валидации поля**\n\n"
            f"👤 Клиент: @{sanitize_for_telegram(username)} (ID: {user_id})\n"
            f"📋 Поле: `{field_name}` (тип: {field_type})\n"
            f"💬 Введено: `{sanitize_for_telegram(raw_value[:200])}`\n"
            f"❌ Ошибка: {error_message}"
        )
        await message.bot.send_message(chat_id=target, text=text, parse_mode="Markdown")
    except Exception as e:
        logger.warning(f"Failed to notify admin about validation error: {e}")


@router.message(OrderState.filling_document)
async def process_document_field(message: Message, state: FSMContext):
    """Handle field value input from the user with validation."""
    if not message.from_user or not message.text:
        await message.answer("❌ Error. Please start again: /start")
        await state.clear()
        return

    user_id = message.from_user.id
    session = await get_user_session(user_id)

    data = await state.get_data()
    field_index = data.get("current_field_index", 0)

    template = session.get("current_template")
    if not template:
        await message.answer("❌ Error. Please start again: /start")
        await state.clear()
        return

    fields = template["fields"]
    if field_index >= len(fields):
        return

    field = fields[field_index]
    if not field:
        await message.answer("❌ Error. Please start again: /start")
        await state.clear()
        return

    raw_value = message.text.strip()

    # Optional field — allow empty
    if field.optional and not raw_value:
        session["temp_item_data"][field.id] = "-"
        await state.update_data(
            current_step=f"Filling document: field {field_index + 1}"
        )
        session["current_field_index"] = field_index + 1
        await ask_document_fields(message, user_id, state)
        return

    # Required field — reject empty
    if not field.optional and not raw_value:
        await message.answer("❌ This field is required. Please enter a value.")
        return

    # ── Validate the value ──────────────────────────────────────────
    from utils.validation import validate_field_value

    result = validate_field_value(
        value=raw_value,
        field_type=field.type,
        max_length=field.max_length,
        field_name=field.id,
        choices=field.choices,
        min_value=field.min_value,
        max_value=field.max_value,
    )

    if not result.is_valid:
        # Notify admin about the validation failure
        await _notify_admin_validation_error(
            message=message,
            user_id=user_id,
            field_name=field.id,
            field_type=field.type,
            raw_value=raw_value,
            error_message=result.error_message,
        )

        # Show error to user with retry
        await message.answer(
            f"❌ {result.error_message}\n\n"
            f"Пожалуйста, попробуйте снова.\n"
            f"💡 *Подсказка:* {field.type_hint()}"
        )
        return

    # ── Store validated value ───────────────────────────────────────
    session["temp_item_data"][field.id] = result.sanitized_value

    await state.update_data(current_step=f"Filling document: field {field_index + 1}")
    session["current_field_index"] = field_index + 1
    await ask_document_fields(message, user_id, state)


@router.callback_query(OrderState.filling_document, F.data.startswith("choice_"))
async def process_choice_field(callback: CallbackQuery, state: FSMContext):
    """Handle inline choice selection for a "choice" field.

    Callback data format: ``choice_{field_id}_{value}``. The field_id may
    contain underscores, so we split with maxsplit=2.
    """
    if not callback.data or not callback.from_user:
        await callback.answer("❌ Error processing request")
        return

    parts = callback.data.split("_", 2)
    if len(parts) < 3:
        await callback.answer("❌ Error processing request")
        return
    field_id = parts[1]
    raw_value = parts[2]

    user_id = callback.from_user.id
    session = await get_user_session(user_id)

    data = await state.get_data()
    field_index = data.get("current_field_index", 0)

    template = session.get("current_template")
    if not template:
        await callback.answer("❌ Error. Please start again: /start")
        await state.clear()
        return

    fields = template["fields"]
    if field_index >= len(fields):
        await callback.answer("❌ Error processing request")
        return

    field = fields[field_index]
    if not field or field.id != field_id or field.type != "choice":
        await callback.answer("❌ Error processing request")
        return

    # Validate the selected value against the field's allowed choices.
    from utils.validation import validate_field_value

    result = validate_field_value(
        value=raw_value,
        field_type="choice",
        field_name=field.id,
        choices=field.choices,
    )

    if not result.is_valid:
        await callback.answer(result.error_message, show_alert=True)
        return

    # Store the validated value and advance to the next field.
    session["temp_item_data"][field.id] = result.sanitized_value

    await state.update_data(current_step=f"Filling document: field {field_index + 1}")
    session["current_field_index"] = field_index + 1

    if isinstance(callback.message, Message):
        await ask_document_fields(callback.message, user_id, state)
    elif callback.bot:
        # Fallback: send a fresh message if the original is not editable.
        # ask_document_fields needs a Message; we send the next prompt directly.
        from aiogram.types import InlineKeyboardMarkup

        session = await get_user_session(user_id)
        template = session.get("current_template")
        if template:
            fields = template["fields"]
            next_index = session.get("current_field_index", 0)
            if next_index < len(fields):
                next_field = fields[next_index]
                text = (
                    f"📝 *Поле {next_index + 1} из {len(fields)}*\n\n"
                    f"{next_field.prompt}\n\n"
                    f"💡 *Подсказка:* {next_field.type_hint()}"
                )
                markup = None
                if next_field.type == "choice" and next_field.choices:
                    markup = choice_keyboard(next_field.choices, next_field.id)
                await callback.bot.send_message(
                    callback.from_user.id,
                    text,
                    reply_markup=markup,
                )

    await callback.answer()


@router.message(OrderState.asking_delivery)
async def fallback_asking_delivery(message: Message, state: FSMContext):
    """Fallback: user sent text instead of choosing delivery option."""
    if not message.from_user:
        return
    lang = user_language(message.from_user)
    i18n = get_i18n()
    await message.answer(i18n.get("error_use_buttons", language=lang))


@router.callback_query(OrderState.asking_delivery, F.data.startswith("delivery_"))
async def process_delivery_choice(callback: CallbackQuery, state: FSMContext):
    """Handle delivery choice (yes / no)."""
    if not callback.data or not callback.from_user:
        await callback.answer("❌ Error processing request")
        return

    choice = callback.data.split("_")[1]
    user_id = callback.from_user.id
    session = await get_user_session(user_id)
    lang = user_language(callback.from_user)
    i18n = get_i18n()

    if choice == "yes":
        text = i18n.get("delivery_prompt", language=lang)
        if isinstance(callback.message, Message):
            await callback.message.edit_text(text)
        elif callback.bot:
            await callback.bot.send_message(callback.from_user.id, text)
        await state.set_state(OrderState.filling_delivery)
        await state.update_data(current_step="Delivery details")
    else:
        session["delivery"] = None

        total = calculate_total_price(session)
        session["total_price"] = total

        currency = session.get("currency", DEFAULT_CURRENCY)
        sym = _currency_symbol(currency)

        text = i18n.get(
            "total_amount",
            language=lang,
            total=total,
            currency=sym,
        )

        from keyboards.buttons import payment_keyboard

        if isinstance(callback.message, Message):
            await callback.message.edit_text(text, reply_markup=payment_keyboard())
        elif callback.bot:
            await callback.bot.send_message(
                callback.from_user.id, text, reply_markup=payment_keyboard()
            )
        await state.set_state(OrderState.choosing_payment)

    await callback.answer()


@router.message(OrderState.filling_delivery)
async def save_delivery(message: Message, state: FSMContext):
    """Save delivery details from the user."""
    if not message.from_user or not message.text:
        await message.answer("❌ Error. Please start again: /start")
        await state.clear()
        return

    user_id = message.from_user.id
    session = await get_user_session(user_id)
    lang = user_language(message.from_user)
    i18n = get_i18n()

    lines = message.text.strip().split("\n")

    if len(lines) < 3:
        await message.answer(i18n.get("delivery_format_error", language=lang))
        return

    # Cap delivery values to the database column sizes. Markdown escaping is
    # applied later in utils.router when the message is composed for the
    # manager; the raw values must stay intact in the database.
    from utils.sanitizer import truncate_for_storage

    delivery = {
        "name": truncate_for_storage(
            lines[0].strip() if len(lines) > 0 else "-", max_length=255
        ),
        "phone": truncate_for_storage(
            lines[1].strip() if len(lines) > 1 else "-", max_length=20
        ),
        "email": truncate_for_storage(
            lines[2].strip() if len(lines) > 2 else "-", max_length=255
        ),
        "address": truncate_for_storage(
            lines[3].strip() if len(lines) > 3 else "-", max_length=100
        ),
    }
    session["delivery"] = delivery

    total = calculate_total_price(session)
    session["total_price"] = total

    currency = session.get("currency", DEFAULT_CURRENCY)
    sym = _currency_symbol(currency)
    del_price = _delivery_price(currency)

    text = i18n.get(
        "total_with_delivery",
        language=lang,
        total=total,
        currency=sym,
        delivery_price=del_price,
    )

    from keyboards.buttons import payment_keyboard

    await message.answer(text, reply_markup=payment_keyboard())
    await state.set_state(OrderState.choosing_payment)


@router.message(OrderState.choosing_payment)
async def fallback_choosing_payment(message: Message, state: FSMContext):
    """Fallback: user sent text instead of choosing payment method."""
    if not message.from_user:
        return
    lang = user_language(message.from_user)
    i18n = get_i18n()
    await message.answer(i18n.get("error_use_buttons", language=lang))


@router.callback_query(OrderState.choosing_payment, F.data.startswith("pay_"))
async def process_payment(callback: CallbackQuery, state: FSMContext):
    """Handle payment method selection."""
    if not callback.data or not callback.from_user:
        await callback.answer("❌ Error processing request")
        return

    payment_method = callback.data.split("_")[1]
    user_id = callback.from_user.id
    session = await get_user_session(user_id)
    lang = user_language(callback.from_user)
    i18n = get_i18n()

    session["payment_method"] = payment_method

    from config import PAYMENT_DETAILS

    details = PAYMENT_DETAILS.get(payment_method, "Details not available")

    text = i18n.get(
        "payment_details",
        language=lang,
        method=payment_method.upper(),
        details=details,
    )

    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, parse_mode="Markdown")
    elif callback.bot:
        await callback.bot.send_message(
            callback.from_user.id, text, parse_mode="Markdown"
        )

    await state.set_state(OrderState.waiting_for_payment_proof)
    await state.update_data(current_step="Waiting for payment proof")
    await callback.answer()


@router.message(OrderState.waiting_for_payment_proof)
async def process_payment_proof(message: Message, state: FSMContext):
    """Handle payment proof — photo or PDF receipt."""
    if not message.from_user or not message.bot:
        await message.answer("❌ Error. Please start again: /start")
        await state.clear()
        return

    user_id = message.from_user.id
    session = await get_user_session(user_id)
    cart = session.get("cart", [])
    lang = user_language(message.from_user)
    i18n = get_i18n()

    if not cart:
        await message.answer("❌ Cart is empty. Start again: /start.")
        await state.clear()
        async with _sessions_lock:
            user_sessions.pop(user_id, None)
        return

    # Validate that payment method and total price are set
    payment_method = session.get("payment_method")
    total_price = session.get("total_price", 0)
    if not payment_method or total_price <= 0:
        await message.answer(i18n.get("error_payment_incomplete", language=lang))
        await state.clear()
        async with _sessions_lock:
            user_sessions.pop(user_id, None)
        return

    file_id = None
    has_photo = False

    if message.photo:
        file_id = message.photo[-1].file_id
        has_photo = True
    elif message.document:
        file_id = message.document.file_id
        has_photo = True

    if not has_photo:
        await message.answer(i18n.get("payment_proof_required", language=lang))
        return

    order_id = await _generate_order_id()

    order_data = {
        "order_id": order_id,
        "documents": session.get("cart", []),
        "delivery": session.get("delivery"),
        "payment_method": session.get("payment_method"),
        "total_price": session.get("total_price"),
        "currency": session.get("currency", DEFAULT_CURRENCY),
        "user": {"id": user_id, "username": message.from_user.username},
    }

    from utils.router import send_order_to_manager

    try:
        await send_order_to_manager(
            bot=message.bot,
            order_data=order_data,
            user_id=user_id,
            payment_proof_file_id=file_id,
        )
    except Exception as e:
        import logging

        logging.getLogger(__name__).error(f"Failed to send order to manager: {e}")
        await message.answer(
            f"✅ **Order #{order_id} created, but failed to notify manager.**\n\n"
            "Please contact support."
        )

    # Save order to database
    async with AsyncSessionLocal() as db:
        db_order = await create_order(
            db=db,
            order_id=order_id,
            user_id=user_id,
            total_price=session.get("total_price", 0),
            status="paid",
            payment_method=session.get("payment_method"),
            payment_proof_file_id=file_id,
            delivery=session.get("delivery"),
            documents=cart,
        )

        for cart_item in cart:
            price = _currency_price(
                session.get("currency", DEFAULT_CURRENCY), cart_item["type"]
            )
            await create_order_item(
                db=db,
                order_id=db_order.id,
                document_type=cart_item["type"],
                quantity=cart_item["quantity"],
                unit_price=price,
                data=cart_item,
            )

    from keyboards.buttons import main_menu_keyboard

    await message.answer(
        i18n.get("order_accepted", language=lang, order_id=order_id),
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )

    await state.clear()
    async with _sessions_lock:
        user_sessions.pop(user_id, None)


@router.callback_query(F.data == "cart_add_more")
async def callback_add_more(callback: CallbackQuery, state: FSMContext):
    """Handle "Add more" button — show document list again."""
    if not callback.from_user:
        await callback.answer()
        return

    from keyboards.buttons import document_keyboard as doc_kb
    from templates.documents import get_all_templates as get_templates

    docs = get_templates()
    lang = user_language(callback.from_user)
    i18n = get_i18n()

    text = i18n.get("choose_document", language=lang)

    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=doc_kb(docs))
    elif callback.bot:
        await callback.bot.send_message(
            callback.from_user.id, text, reply_markup=doc_kb(docs)
        )
    await state.set_state(OrderState.choosing_document)
    await callback.answer()


@router.callback_query(F.data == "cart_clear")
async def callback_clear_cart(callback: CallbackQuery, state: FSMContext):
    """Handle "Clear cart" button."""
    if not callback.from_user:
        await callback.answer()
        return

    user_id = callback.from_user.id
    session = await get_user_session(user_id)
    session["cart"] = []
    session["delivery"] = None
    session["total_price"] = 0

    lang = user_language(callback.from_user)
    i18n = get_i18n()
    text = i18n.get("cart_cleared", language=lang)

    from keyboards.buttons import main_menu_keyboard

    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=main_menu_keyboard())
    elif callback.bot:
        await callback.bot.send_message(
            callback.from_user.id, text, reply_markup=main_menu_keyboard()
        )
    await state.set_state(OrderState.choosing_document)
    await callback.answer()


@router.callback_query(F.data == "cart_checkout")
async def callback_checkout(callback: CallbackQuery, state: FSMContext):
    """Handle "Proceed to payment" — show cart summary and payment options."""
    if not callback.from_user:
        await callback.answer()
        return

    user_id = callback.from_user.id
    session = await get_user_session(user_id)
    lang = user_language(callback.from_user)
    i18n = get_i18n()

    if not session.get("cart"):
        await callback.answer(
            "Cart is empty. Add a document before checkout.",
            show_alert=True,
        )
        await state.set_state(OrderState.choosing_document)
        return

    total = calculate_total_price(session)
    session["total_price"] = total

    currency = session.get("currency", DEFAULT_CURRENCY)
    sym = _currency_symbol(currency)

    # Build cart summary
    summary_lines = []
    for cart_item in session.get("cart", []):
        doc = get_template(cart_item["type"])
        name = _doc_name(doc, lang) if doc else cart_item["type"]
        price = _currency_price(currency, cart_item["type"])
        item_total = price * cart_item["quantity"]
        summary_lines.append(f"📄 {name} x{cart_item['quantity']} = {item_total} {sym}")

    delivery = session.get("delivery")
    if delivery:
        del_price = _delivery_price(currency)
        summary_lines.append(f"🚚 Delivery: +{del_price} {sym}")
        summary_lines.append(f"   📮 {delivery.get('name', '-')}")
    else:
        summary_lines.append("🚚 Pickup (no delivery)")

    summary_text = "\n".join(summary_lines)

    text = i18n.get(
        "cart_summary",
        language=lang,
        items=summary_text,
        delivery="",
        total=total,
        currency=sym,
    )

    from keyboards.buttons import payment_keyboard

    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=payment_keyboard())
    elif callback.bot:
        await callback.bot.send_message(
            callback.from_user.id, text, reply_markup=payment_keyboard()
        )
    else:
        await callback.answer()
        return

    await state.set_state(OrderState.choosing_payment)
    await callback.answer()

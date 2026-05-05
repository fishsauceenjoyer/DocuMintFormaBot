"""Order handlers - core order flow (only Russian)."""

import threading
import uuid
from typing import Any, Dict

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import DELIVERY_PRICE
from fsm.states import OrderState
from keyboards.buttons import (delivery_keyboard,
                               quantity_keyboard)
from templates.documents import get_template, get_template_price

router = Router()

# Хранилище временных данных пользователя (в реальном проекте - в БД/Redis)
user_sessions: Dict[int, Dict[str, Any]] = {}
_sessions_lock = threading.Lock()


def get_user_session(user_id: int) -> Dict[str, Any]:
    """
    Возвращает сессию пользователя, создавая новую при необходимости.

    Сессия хранит временные данные текущего заказа: корзину,
    выбранные документы, данные доставки, способ оплаты.
    В продакшене данные должны храниться в БД или Redis.

    Используется threading.Lock для защиты от race condition
    при одновременных запросах от одного пользователя.

    Args:
        user_id: ID пользователя Telegram.

    Returns:
        Словарь с данными сессии пользователя.
    """
    with _sessions_lock:
        if user_id not in user_sessions:
            user_sessions[user_id] = {
                "cart": [],
                "current_doc_type": None,
                "current_template": None,
                "current_quantity": 0,
                "current_items": [],
                "temp_item_data": {},
                "current_item_index": 0,
                "delivery": None,
                "payment_method": None,
                "total_price": 0,
            }
        return user_sessions[user_id]


def calculate_total(session: Dict[str, Any]) -> int:
    """
    Рассчитывает общую стоимость заказа с учётом доставки.

    Суммирует цены всех позиций в корзине (цена документа × количество).
    Если выбран самовывоз — стоимость доставки не добавляется.

    Args:
        session: Словарь сессии пользователя, содержащий корзину и данные доставки.

    Returns:
        Общая сумма заказа в злотых (int).
    """
    total = 0
    for item in session.get("cart", []):
        price = get_template_price(item["type"])
        total += price * item["quantity"]

    if session.get("delivery"):
        total += DELIVERY_PRICE

    return total


@router.callback_query(OrderState.choosing_document, F.data.startswith("doc_"))
async def process_document_choice(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор типа документа из списка доступных.

    Загружает шаблон выбранного документа, сохраняет его в сессию
    пользователя, показывает информацию о цене и предлагает выбрать
    количество экземпляров. Переводит пользователя в состояние
    ввода количества (OrderState.entering_quantity).

    Args:
        callback: CallbackQuery с data вида "doc_sanepid", "doc_bhp" и т.д.
        state: Контекст FSM для сохранения текущего шага.
    """
    if not callback.data:
        await callback.answer("❌ Ошибка обработки запроса")
        return
    doc_type = callback.data.split("_")[1]
    template = get_template(doc_type)
    if not template:
        await callback.answer("❌ Шаблон не найден")
        return

    user_id = callback.from_user.id
    session = get_user_session(user_id)

    session["current_doc_type"] = doc_type
    session["current_template"] = template
    session["current_items"] = []
    session["temp_item_data"] = {}
    session["current_item_index"] = 0

    await state.update_data(current_step=f"Выбор количества: {template['name']}")

    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            f"📄 *{template['name']}*\n\n"
            f"Цена за единицу: {template['price']} zł\n\n"
            f"Введите количество документов этого типа:",
            reply_markup=quantity_keyboard(),
        )
    elif callback.bot:
        await callback.bot.send_message(
            callback.from_user.id,
            f"📄 *{template['name']}*\n\n"
            f"Цена за единицу: {template['price']} zł\n\n"
            f"Введите количество документов этого типа:",
            reply_markup=quantity_keyboard(),
        )
    await state.set_state(OrderState.entering_quantity)
    await callback.answer()


@router.callback_query(OrderState.entering_quantity, F.data.startswith("qty_"))
async def process_quantity(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор количества документов (от 1 до 5).

    Сохраняет выбранное количество в сессию и запускает процесс
    заполнения полей для первого документа.

    Args:
        callback: CallbackQuery с data вида "qty_1", "qty_2" и т.д.
        state: Контекст FSM.
    """
    if not callback.data or not isinstance(callback.message, Message):
        await callback.answer("❌ Ошибка обработки запроса")
        return
    quantity = int(callback.data.split("_")[1])

    user_id = callback.from_user.id
    session = get_user_session(user_id)

    session["current_quantity"] = quantity
    session["current_items"] = []
    session["current_item_index"] = 0

    await ask_document_fields(callback.message, user_id, state)
    await state.set_state(OrderState.filling_document)
    await callback.answer()


async def ask_document_fields(message: Message, user_id: int, state: FSMContext):
    """
    Рекурсивно запрашивает у пользователя заполнение полей документа.

    Функция последовательно показывает поля из шаблона документа
    (ФИО, дата рождения, PESEL, адрес и т.д.). После заполнения всех
    полей одного документа переходит к следующему. Когда все документы
    данного типа заполнены — добавляет их в корзину и предлагает
    выбрать доставку.

    Args:
        message: Сообщение, в которое выводится запрос поля.
        user_id: ID пользователя для получения сессии.
        state: Контекст FSM для сохранения индекса текущего поля.
    """
    session = get_user_session(user_id)
    template = session["current_template"]

    if not template:
        return

    fields = template["fields"]
    current_index = session.get("current_field_index", 0)

    if current_index >= len(fields):
        session["current_items"].append(session["temp_item_data"].copy())
        session["temp_item_data"] = {}

        if len(session["current_items"]) < session["current_quantity"]:
            session["current_field_index"] = 0
            await ask_document_fields(message, user_id, state)
        else:
            session["cart"].append(
                {
                    "type": session["current_doc_type"],
                    "quantity": session["current_quantity"],
                    "items": session["current_items"].copy(),
                }
            )

            await message.answer(
                f"✅ *{session['current_quantity']}x {template['name']}* добавлено в заказ!\n\n"
                "Что делаем дальше?",
                reply_markup=delivery_keyboard(),
            )

            await state.set_state(OrderState.asking_delivery)
            await state.update_data(current_step="Выбор доставки")
        return

    field = fields[current_index]
    prompt = field.prompt
    optional_note = " (необязательно)" if field.optional else ""

    await message.answer(
        f"📝 *Поле {current_index + 1}/{len(fields)}*\n\n"
        f"{prompt}{optional_note}\n\n"
        f"Отправьте ответ одним сообщением."
    )

    await state.update_data(current_field_index=current_index)
    session["current_field_index"] = current_index


@router.message(OrderState.filling_document)
async def process_document_field(message: Message, state: FSMContext):
    """
    Обрабатывает ввод значения поля документа от пользователя.

    Проверяет корректность данных: для дат проверяет формат,
    для обязательных полей — что значение не пустое.
    Сохраняет введённое значение и переходит к следующему полю.

    Args:
        message: Текстовое сообщение с ответом пользователя.
        state: Контекст FSM с индексом текущего поля.
    """
    if not message.from_user or not message.text:
        await message.answer("❌ Ошибка данных. Начните заказ заново /start")
        await state.clear()
        return

    user_id = message.from_user.id
    session = get_user_session(user_id)

    data = await state.get_data()
    field_index = data.get("current_field_index", 0)

    template = session.get("current_template")
    if not template:
        await message.answer("❌ Ошибка. Начните заказ заново /start")
        await state.clear()
        return

    fields = template["fields"]

    if field_index >= len(fields):
        return

    field = fields[field_index]
    if not field:
        await message.answer("❌ Ошибка поля. Начните заказ заново /start")
        await state.clear()
        return

    value = message.text.strip()

    if field.type == "date":
        if len(value) < 6 or len(value) > 10:
            await message.answer("❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ")
            return

    if not field.optional and not value:
        await message.answer(
            f"❌ Поле '{field.prompt}' обязательное. Пожалуйста, введите значение."
        )
        return

    session["temp_item_data"][field.id] = value if value else "-"

    await state.update_data(
        current_step=f"Заполнение документа: поле {field_index + 1}"
    )

    session["current_field_index"] = field_index + 1
    await ask_document_fields(message, user_id, state)


@router.callback_query(OrderState.asking_delivery, F.data.startswith("delivery_"))
async def process_delivery_choice(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор пользователя: нужна доставка или самовывоз.

    Если выбрана доставка (delivery_yes) — запрашивает данные.
    Если выбран самовывоз (delivery_no) — показывает сумму и оплату.

    Args:
        callback: CallbackQuery с data "delivery_yes" или "delivery_no".
        state: Контекст FSM.
    """
    if not callback.data:
        await callback.answer("❌ Ошибка обработки запроса")
        return
    choice = callback.data.split("_")[1]
    user_id = callback.from_user.id
    session = get_user_session(user_id)

    if choice == "yes":
        if isinstance(callback.message, Message):
            await callback.message.edit_text(
                "🚚 **Доставка InPost**\n\n"
                "Введите данные для доставки одним сообщением в формате:\n\n"
                "Имя и фамилия:\n"
                "Номер телефона:\n"
                "Email:\n"
                "Номер пачкомата или адрес"
            )
        elif callback.bot:
            await callback.bot.send_message(
                callback.from_user.id,
                "🚚 **Доставка InPost**\n\n"
                "Введите данные для доставки одним сообщением в формате:\n\n"
                "Имя и фамилия:\n"
                "Номер телефона:\n"
                "Email:\n"
                "Номер пачкомата или адрес"
            )
        await state.set_state(OrderState.filling_delivery)
        await state.update_data(current_step="Заполнение данных доставки")
    else:
        session["delivery"] = None

        total = calculate_total(session)
        session["total_price"] = total

        text = f"💰 **Сумма к оплате:** {total} zł\n\n" "Выберите способ оплаты:"

        from keyboards.buttons import payment_keyboard

        if isinstance(callback.message, Message):
            await callback.message.edit_text(text, reply_markup=payment_keyboard())
        elif callback.bot:
            await callback.bot.send_message(callback.from_user.id, text, reply_markup=payment_keyboard())
        await state.set_state(OrderState.choosing_payment)

    await callback.answer()


@router.message(OrderState.filling_delivery)
async def save_delivery(message: Message, state: FSMContext):
    """
    Сохраняет данные доставки от пользователя.

    Ожидает текст в формате (построчно):
        - Имя и фамилия
        - Номер телефона
        - Email
        - Номер пачкомата или адрес

    Args:
        message: Текстовое сообщение с данными доставки.
        state: Контекст FSM.
    """
    if not message.from_user or not message.text:
        await message.answer("❌ Ошибка данных. Начните заказ заново /start")
        await state.clear()
        return

    user_id = message.from_user.id
    session = get_user_session(user_id)

    lines = message.text.strip().split("\n")

    if len(lines) < 3:
        await message.answer(
            "❌ Пожалуйста, введите данные в правильном формате:\n\n"
            "Имя и фамилия:\n"
            "Номер телефона:\n"
            "Email:\n"
            "Номер пачкомата"
        )
        return

    delivery = {
        "name": lines[0].strip() if len(lines) > 0 else "-",
        "phone": lines[1].strip() if len(lines) > 1 else "-",
        "email": lines[2].strip() if len(lines) > 2 else "-",
        "paczkomat": lines[3].strip() if len(lines) > 3 else "-",
    }
    session["delivery"] = delivery

    total = calculate_total(session)
    session["total_price"] = total

    text = (
        f"💰 **Сумма к оплате:** {total} zł (включая доставку {DELIVERY_PRICE} zł)\n\n"
        "Выберите способ оплаты:"
    )

    from keyboards.buttons import payment_keyboard

    await message.answer(text, reply_markup=payment_keyboard())
    await state.set_state(OrderState.choosing_payment)


@router.callback_query(OrderState.choosing_payment, F.data.startswith("pay_"))
async def process_payment(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор способа оплаты (Blik, гривна, USDT).

    Показывает платёжные реквизиты и предупреждение об уточнении
    курса/суммы при оплате не в день заказа.

    Args:
        callback: CallbackQuery с data "pay_blik", "pay_uah" или "pay_usdt".
        state: Контекст FSM.
    """
    if not callback.data:
        await callback.answer("❌ Ошибка обработки запроса")
        return
    payment_method = callback.data.split("_")[1]
    user_id = callback.from_user.id
    session = get_user_session(user_id)

    session["payment_method"] = payment_method

    from config import PAYMENT_DETAILS

    if payment_method == "blik":
        details = PAYMENT_DETAILS["blik"]
    elif payment_method == "uah":
        details = PAYMENT_DETAILS["uah"]
    else:
        details = PAYMENT_DETAILS["usdt"]

    warning = "\n\n⚠️ Если оплата не сегодня, перед оплатой уточните изменения у менеджера."

    message_text = (
        f"💳 **Способ оплаты: {payment_method.upper()}**\n\n"
        f"{details}{warning}\n\n"
        "После оплаты отправьте фото/скриншот чека."
    )

    if isinstance(callback.message, Message):
        await callback.message.edit_text(message_text, parse_mode="Markdown")
    elif callback.bot:
        await callback.bot.send_message(callback.from_user.id, message_text, parse_mode="Markdown")

    await state.set_state(OrderState.waiting_for_payment_proof)
    await state.update_data(current_step="Ожидание подтверждения оплаты")
    await callback.answer()


@router.message(OrderState.waiting_for_payment_proof)
async def process_payment_proof(message: Message, state: FSMContext):
    """
    Обрабатывает подтверждение оплаты — фото или PDF чека.

    Генерирует номер заказа, формирует данные и отправляет менеджеру.
    После отправки очищает сессию пользователя.

    Args:
        message: Сообщение с фото/документом чека оплаты.
        state: Контекст FSM (очищается после обработки).
    """
    if not message.from_user or not message.bot:
        await message.answer("❌ Ошибка. Начните заказ заново /start")
        await state.clear()
        return

    user_id = message.from_user.id
    session = get_user_session(user_id)

    file_id = None
    has_photo = False

    if message.photo:
        file_id = message.photo[-1].file_id
        has_photo = True
    elif message.document:
        file_id = message.document.file_id
        has_photo = True

    if not has_photo:
        await message.answer(
            "📸 Пожалуйста, отправьте фото или скриншот чека об оплате."
        )
        return

    order_id = f"ORDER_{uuid.uuid4().hex[:8].upper()}"

    order_data = {
        "order_id": order_id,
        "documents": session.get("cart", []),
        "delivery": session.get("delivery"),
        "payment_method": session.get("payment_method"),
        "total_price": session.get("total_price"),
        "user": {"id": user_id, "username": message.from_user.username},
    }

    from utils.router import send_order_to_manager

    await send_order_to_manager(
        bot=message.bot,
        order_data=order_data,
        user_id=user_id,
        payment_proof_file_id=file_id,
    )

    await message.answer(
        f"✅ **Заказ #{order_id} принят!**\n\n"
        "📮 Завтра/послезавтра будет готово.\n"
        "Мы сообщим вам, когда документ будет готов к отправке.\n\n"
        "Спасибо за заказ! 👋",
        parse_mode="Markdown",
    )

    await state.clear()
    user_sessions.pop(user_id, None)


@router.callback_query(F.data == "cart_add_more")
async def callback_add_more(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие кнопки "Добавить ещё документ" в корзине.

    Показывает список доступных типов документов для добавления
    новых позиций в уже существующий заказ.

    Args:
        callback: CallbackQuery с data == "cart_add_more".
        state: Контекст FSM.
    """
    from keyboards.buttons import document_keyboard as doc_kb
    from templates.documents import get_all_templates as get_templates

    docs = get_templates()

    text = (
        "📋 **Выберите документ для заказа:**\n\n"
        "Также вы можете воспользоваться кнопкой 'Связь с менеджером'"
    )

    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=doc_kb(docs))
    elif callback.bot:
        await callback.bot.send_message(callback.from_user.id, text, reply_markup=doc_kb(docs))
    await state.set_state(OrderState.choosing_document)
    await callback.answer()


@router.callback_query(F.data == "cart_clear")
async def callback_clear_cart(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие кнопки "Очистить корзину".

    Удаляет все позиции из корзины пользователя и показывает главное меню.

    Args:
        callback: CallbackQuery с data == "cart_clear".
        state: Контекст FSM.
    """
    user_id = callback.from_user.id
    session = get_user_session(user_id)
    session["cart"] = []
    session["delivery"] = None
    session["total_price"] = 0

    text = "🗑 Корзина очищена.\n\nНачните новый заказ:"

    from keyboards.buttons import main_menu_keyboard

    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=main_menu_keyboard())
    elif callback.bot:
        await callback.bot.send_message(callback.from_user.id, text, reply_markup=main_menu_keyboard())
    await state.set_state(OrderState.choosing_document)
    await callback.answer()


@router.callback_query(F.data == "cart_checkout")
async def callback_checkout(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие кнопки "Перейти к оплате" в корзине.

    Рассчитывает итоговую сумму заказа и показывает способы оплаты.

    Args:
        callback: CallbackQuery с data == "cart_checkout".
        state: Контекст FSM.
    """
    user_id = callback.from_user.id
    session = get_user_session(user_id)

    total = calculate_total(session)
    session["total_price"] = total

    text = f"💰 **Сумма к оплате:** {total} zł\n\n" "Выберите способ оплаты:"

    from keyboards.buttons import payment_keyboard

    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=payment_keyboard())
    elif callback.bot:
        await callback.bot.send_message(callback.from_user.id, text, reply_markup=payment_keyboard())
    else:
        await callback.answer()
        return

    await state.set_state(OrderState.choosing_payment)
    await callback.answer()
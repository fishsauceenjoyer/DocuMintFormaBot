"""Admin/manager handlers for sending documents and tracking."""

import re
import threading
from typing import Any, Dict, Optional

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from fsm.states import AdminState
from utils.auth import admin_only, is_admin

router = Router()

# Simple order storage (in production, use database)
orders: Dict[str, Dict[str, Any]] = {}
_orders_lock = threading.Lock()


def extract_order_id(text: str) -> Optional[str]:
    """
    Извлекает номер заказа из текста.

    Ищет паттерн вида ORDER_123ABC или просто 123ABC в тексте.
    Используется для парсинга команд менеджера.

    Args:
        text: Строка, в которой нужно найти номер заказа.

    Returns:
        Извлечённый номер заказа (без префикса ORDER_) или None, если не найден.
    """
    # Match patterns like ORDER_123ABC or just 123ABC
    match = re.search(r"ORDER_([A-Z0-9]+)", text, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return None


@router.message(Command("send_doc"))
@admin_only
async def cmd_send_doc(message: Message, state: FSMContext):
    """
    Команда менеджера для отправки готового документа клиенту.

    Запрашивает у менеджера номер заказа в формате /send_doc ORDER_123ABC,
    после чего ожидает файл документа. Переводит в состояние
    ожидания файла (AdminState.waiting_for_file).

    Args:
        message: Сообщение с командой /send_doc.
        state: Контекст FSM для установки состояния ожидания файла.
    """
    await message.answer(
        "📎 **Отправить документ клиенту**\n\n"
        "Введите номер заказа в формате:\n"
        "/send_doc ORDER_123ABC\n\n"
        "После этого отправьте файл документа."
    )
    await state.set_state(AdminState.waiting_for_file)
    await state.update_data(action="send_doc")


@router.message(Command("track"))
@admin_only
async def cmd_track(message: Message, state: FSMContext):
    """
    Команда менеджера для отправки трек-номера клиенту.

    Ожидает формат: /track ORDER_123ABC TRACKING123.
    Извлекает номер заказа и трек-номер, сохраняет информацию.
    В текущей версии только подтверждает получение (без реальной отправки).

    Args:
        message: Сообщение с командой /track и параметрами.
        state: Контекст FSM (не используется в текущей реализации).
    """
    if not message.text:
        await message.answer("❌ Ошибка: не удалось получить текст сообщения.")
        return

    parts = message.text.split()

    if len(parts) < 3:
        await message.answer(
            "📦 **Отправить трек-номер**\n\n"
            "Введите команду в формате:\n"
            "/track ORDER_123ABC TRACKING123\n\n"
            "Где:\n"
            "- ORDER_123ABC - номер заказа\n"
            "- TRACKING123 - трек-номер"
        )
        return

    order_id = parts[1]
    tracking = parts[2]

    # In a real system, we would look up the client ID from the database
    # For now, just acknowledge
    await message.answer(
        f"📦 Трек-номер для заказа {order_id}:\n"
        f"`{tracking}`\n\n"
        "⚠️ Для реальной отправки нужно связать заказ с клиентом в базе данных."
    )


@router.callback_query(F.data.startswith("send_doc_"))
async def callback_send_doc(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие кнопки "Отправить готовый документ" в сообщении заказа.

    Извлекает номер заказа из callback_data, просит менеджера отправить файл
    и переводит в состояние ожидания файла.

    Args:
        callback: CallbackQuery с data вида "send_doc_ORDER_123ABC".
        state: Контекст FSM для установки состояния ожидания файла.
    """
    # Check admin rights
    if callback.from_user and not is_admin(callback.from_user.username):
        await callback.answer("⛔ У вас нет прав для этого действия.", show_alert=True)
        return
    if not callback.data:
        await callback.answer("Ошибка: данные не найдены", show_alert=True)
        return

    order_id = callback.data.replace("send_doc_", "")

    # Check if message is accessible (has edit_text method)
    if callback.message is None or not hasattr(callback.message, "edit_text"):
        await callback.answer("Ошибка: сообщение недоступно", show_alert=True)
        return

    await callback.message.edit_text(  # type: ignore[union-attr]
        f"📎 **Отправка документа для заказа {order_id}**\n\n"
        "Отправьте файл документа."
    )

    await state.set_state(AdminState.waiting_for_file)
    await state.update_data(order_id=order_id, action="send_doc")
    await callback.answer()


@router.callback_query(F.data.startswith("send_track_"))
async def callback_send_track(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие кнопки "Отправить трек-номер" в сообщении заказа.

    Извлекает номер заказа из callback_data, просит менеджера ввести
    трек-номер и переводит в состояние ожидания трек-номера.

    Args:
        callback: CallbackQuery с data вида "send_track_ORDER_123ABC".
        state: Контекст FSM для установки состояния ожидания трек-номера.
    """
    # Check admin rights
    if callback.from_user and not is_admin(callback.from_user.username):
        await callback.answer("⛔ У вас нет прав для этого действия.", show_alert=True)
        return
    if not callback.data:
        await callback.answer("Ошибка: данные не найдены", show_alert=True)
        return

    order_id = callback.data.replace("send_track_", "")

    # Check if message is accessible (has edit_text method)
    if callback.message is None or not hasattr(callback.message, "edit_text"):
        await callback.answer("Ошибка: сообщение недоступно", show_alert=True)
        return

    await callback.message.edit_text(  # type: ignore[union-attr]
        f"📦 **Отправка трек-номера для заказа {order_id}**\n\n" "Введите трек-номер:"
    )

    await state.set_state(AdminState.waiting_for_tracking)
    await state.update_data(order_id=order_id, action="send_track")
    await callback.answer()


@router.callback_query(F.data.startswith("order_done_"))
async def callback_order_done(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие кнопки "Заказ выполнен".

    Отмечает заказ как выполненный (completed) в локальном хранилище
    и показывает уведомление менеджеру.

    Args:
        callback: CallbackQuery с data вида "order_done_ORDER_123ABC".
        state: Контекст FSM (не используется).
    """
    # Check admin rights
    if callback.from_user and not is_admin(callback.from_user.username):
        await callback.answer("⛔ У вас нет прав для этого действия.", show_alert=True)
        return
    if not callback.data:
        await callback.answer("Ошибка: данные не найдены", show_alert=True)
        return

    order_id = callback.data.replace("order_done_", "")

    # Update order status
    with _orders_lock:
        if order_id in orders:
            orders[order_id]["status"] = "completed"

    await callback.answer(
        f"✅ Заказ {order_id} отмечен как выполненный", show_alert=True
    )


@router.message(AdminState.waiting_for_file)
async def process_document_file(message: Message, state: FSMContext):
    """
    Обрабатывает загрузку файла документа от менеджера.

    Принимает фото или документ, извлекает file_id.
    В текущей версии только подтверждает получение — для реальной
    отправки нужно связать заказ с клиентом в базе данных.

    Args:
        message: Сообщение с файлом (фото или документ).
        state: Контекст FSM (очищается после обработки).
    """
    data = await state.get_data()
    order_id = data.get("order_id", "UNKNOWN")

    file_id = None

    # Get file ID from photo or document
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document:
        file_id = message.document.file_id

    if not file_id:
        await message.answer(
            "❌ Пожалуйста, отправьте файл документа (фото или документ)."
        )
        return

    # Look up client info from orders storage
    with _orders_lock:
        order_info = orders.get(order_id)

    if order_info is None or not order_info.get("user_id"):
        await message.answer(
            f"❌ Заказ {order_id} не найден. Невозможно определить клиента.\n\n"
            "Убедитесь, что номер заказа правильный."
        )
        await state.clear()
        return

    client_id = order_info["user_id"]

    if message.bot is None:
        await message.answer("❌ Ошибка бота. Попробуйте ещё раз.")
        await state.clear()
        return

    # Actually send the document to the client
    from utils.router import send_document_to_client

    await send_document_to_client(
        bot=message.bot,
        client_id=client_id,
        order_id=order_id,
        file_id=file_id,
    )

    await message.answer(
        f"✅ Документ для заказа {order_id} отправлен клиенту (ID: {client_id})!\n\n"
        f"📄 Файл документа передан."
    )

    await state.clear()


@router.message(AdminState.waiting_for_tracking)
async def process_tracking_number(message: Message, state: FSMContext):
    """
    Обрабатывает ввод трек-номера от менеджера.

    Сохраняет трек-номер для указанного заказа. В текущей версии
    только подтверждает получение — для реальной отправки нужно
    связать заказ с клиентом в базе данных.

    Args:
        message: Текстовое сообщение с трек-номером.
        state: Контекст FSM (очищается после обработки).
    """
    if not message.text:
        await message.answer("❌ Пожалуйста, введите трек-номер текстом.")
        return

    data = await state.get_data()
    order_id = data.get("order_id", "UNKNOWN")
    tracking = message.text.strip()

    # Look up client info from orders storage
    with _orders_lock:
        order_info = orders.get(order_id)

    if order_info is None or not order_info.get("user_id"):
        await message.answer(
            f"❌ Заказ {order_id} не найден. Невозможно определить клиента.\n\n"
            "Убедитесь, что номер заказа правильный."
        )
        await state.clear()
        return

    client_id = order_info["user_id"]

    if message.bot is None:
        await message.answer("❌ Ошибка бота. Попробуйте ещё раз.")
        await state.clear()
        return

    # Actually send the tracking number to the client
    from utils.router import send_tracking_to_client

    await send_tracking_to_client(
        bot=message.bot,
        client_id=client_id,
        order_id=order_id,
        tracking_number=tracking,
    )

    await message.answer(
        f"✅ Трек-номер для заказа {order_id} отправлен клиенту (ID: {client_id})!\n\n"
        f"🔢 Трек: `{tracking}`",
        parse_mode="Markdown",
    )

    await state.clear()


@router.message(Command("orders"))
@admin_only
async def cmd_orders_list(message: Message, state: FSMContext):
    """
    Команда /orders — показывает список всех заказов (для менеджера).

    Загружает заказы из базы данных и отображает номера заказов,
    их статусы и суммы.

    Args:
        message: Сообщение с командой /orders.
        state: Контекст FSM (не используется).
    """
    from db.crud import SessionLocal, get_all_orders

    db = SessionLocal()
    try:
        all_orders = get_all_orders(db)
        if not all_orders:
            await message.answer("📋 Заказов пока нет.")
            return

        text = "📋 **Список заказов:**\n\n"
        for order in all_orders:
            text += f"• {order.order_id} - {order.status} - {order.total_price} zł\n"

        await message.answer(text, parse_mode="Markdown")
    finally:
        db.close()


@router.message(Command("stats"))
@admin_only
async def cmd_stats(message: Message):
    """
    Команда /stats — показывает статистику заказов (для администратора).

    Загружает статистику всех заказов из базы данных:
    общее количество, распределение по статусам.

    Args:
        message: Сообщение с командой /stats.
    """
    from db.crud import SessionLocal, get_order_stats

    db = SessionLocal()
    try:
        stats = get_order_stats(db)

        text = (
            "📊 **Статистика заказов:**\n\n"
            f"📋 Всего: {stats['total']}\n"
            f"⏳ Ожидают оплаты: {stats['pending']}\n"
            f"✅ Оплачены: {stats['paid']}\n"
            f"🔄 В обработке: {stats['processing']}\n"
            f"📄 Готовы: {stats['ready']}\n"
            f"📦 Отправлены: {stats['shipped']}\n"
            f"🎉 Выполнены: {stats['completed']}\n"
            f"❌ Отменены: {stats['cancelled']}"
        )

        await message.answer(text)
    finally:
        db.close()


@router.message(Command("help_admin"))
@admin_only
async def cmd_help_admin(message: Message):
    """
    Команда /help_admin — показывает справку по доступным командам менеджера.

    Отображает список всех доступных команд для работы с заказами:
    отправка документов, трек-номеров, просмотр заказов и статистики.

    Args:
        message: Сообщение с командой /help_admin.
    """
    await message.answer(
        "🛠 **Команды для менеджера:**\n\n"
        "/send_doc - отправить документ клиенту\n"
        "/track - отправить трек-номер\n"
        "/orders - список всех заказов\n"
        "/stats - статистика\n\n"
        "Также доступны кнопки в сообщениях с заказами."
    )
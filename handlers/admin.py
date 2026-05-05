"""Admin/manager handlers for sending documents and tracking."""

import re
import threading
from typing import Any, Dict, Optional

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from fsm.states import AdminState

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

    # Send to client (in real system, look up client_id from order)
    # await send_document_to_client(message.bot, client_id, order_id, file_id)

    await message.answer(
        f"✅ Документ для заказа {order_id} отправлен клиенту!\n\n"
        "⚠️ Примечание: для реальной отправки нужно связать заказ с клиентом в базе данных."
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

    # Send to client (in real system, look up client_id from order)
    # await send_tracking_to_client(message.bot, client_id, order_id, tracking)

    await message.answer(
        f"✅ Трек-номер для заказа {order_id} отправлен клиенту!\n\n"
        f"Трек: `{tracking}`\n\n"
        "⚠️ Примечание: для реальной отправки нужно связать заказ с клиентом в базе данных.",
        parse_mode="Markdown",
    )

    await state.clear()


@router.message(Command("orders"))
async def cmd_orders_list(message: Message, state: FSMContext):
    """
    Команда /orders — показывает список всех заказов (для менеджера).

    Отображает номера заказов, их статусы и суммы из локального хранилища.
    В продакшене данные должны загружаться из базы данных.

    Args:
        message: Сообщение с командой /orders.
        state: Контекст FSM (не используется).
    """
    if not orders:
        await message.answer("📋 Заказов пока нет.")
        return

    text = "📋 **Список заказов:**\n\n"
    for order_id, order_data in orders.items():
        status = order_data.get("status", "unknown")
        total = order_data.get("total_price", 0)
        text += f"• {order_id} - {status} - {total} zł\n"

    await message.answer(text, parse_mode="Markdown")


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """
    Команда /stats — показывает статистику заказов (для администратора).

    Отображает общее количество заказов из локального хранилища.
    Для полной статистики требуется подключение базы данных.

    Args:
        message: Сообщение с командой /stats.
    """
    await message.answer(
        "📊 **Статистика:**\n\n"
        f"Всего заказов: {len(orders)}\n\n"
        "Для полной статистики нужно подключить базу данных."
    )


@router.message(Command("help_admin"))
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
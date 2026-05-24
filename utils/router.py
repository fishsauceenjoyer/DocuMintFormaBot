"""
Маршрутизация заказов соответствующим менеджерам.

Содержит функции для отправки заказов в нужные чаты менеджеров
в зависимости от типа документа, а также для пересылки готовых
документов и трек-номеров клиентам.
"""

import json
import logging
from typing import Optional

from aiogram import Bot

from config import ROUTING
from templates.documents import get_template

# Import admin's order storage to save user_id for later client notifications
# This is a bridging fix; in production, use database
from handlers.admin import orders

logger = logging.getLogger(__name__)


async def send_order_to_manager(
    bot: Bot,
    order_data: dict,
    user_id: int,
    payment_proof_file_id: Optional[str] = None,
) -> int:
    """
    Отправляет заказ нужному менеджеру в зависимости от типа документа.

    Определяет целевой чат по типу первого документа в заказе.
    Формирует красивое сообщение с деталями заказа: состав документов,
    данные доставки, сумму, способ оплаты. Если есть фото чека —
    отправляет его с подписью.

    Args:
        bot: Экземпляр бота для отправки сообщений.
        order_data: Словарь с данными заказа:
            - order_id: номер заказа
            - documents: список заказанных документов
            - delivery: данные доставки или None
            - payment_method: способ оплаты
            - total_price: итоговая сумма
            - user: информация о пользователе
        user_id: ID пользователя Telegram.
        payment_proof_file_id: File_id фото/документа с чеком (если есть).

    Returns:
        ID чата, в который был отправлен заказ.

    Note:
        После текстового сообщения дополнительно отправляется
        JSON-версия заказа для удобной пересылки.
    """
    # Определяем, какой тип документа основной (первый в списке)
    if not order_data.get("documents"):
        logger.error("No documents in order data")
        return ROUTING["default"]

    main_doc_type = order_data["documents"][0]["type"]
    target = ROUTING.get(main_doc_type, ROUTING["default"])

    # Формируем красивое сообщение
    text = f"🆕 **НОВЫЙ ЗАКАЗ #{order_data['order_id']}**\n"
    text += f"👤 Клиент: {order_data['user'].get('username') or f'ID: {user_id}'}\n\n"

    for doc in order_data["documents"]:
        doc_type = doc["type"]
        template = get_template(doc_type)
        doc_name = template["name"] if template else doc_type

        text += f"📄 *{doc_name.upper()}* x{doc['quantity']}\n"

        for idx, item in enumerate(doc.get("items", []), 1):
            text += f"  {idx}. "
            for k, v in item.items():
                text += f"{k}: {v} "
            text += "\n"
        text += "\n"

    # Delivery info
    delivery = order_data.get("delivery")
    if delivery:
        text += "🚚 **Доставка:**\n"
        text += f"  Имя: {delivery.get('name', '-')}\n"
        text += f"  Телефон: {delivery.get('phone', '-')}\n"
        text += f"  Email: {delivery.get('email', '-')}\n"
        text += f"  Пачкомат: {delivery.get('paczkomat', '-')}\n\n"
    else:
        text += "🚚 Самовывоз (без доставки)\n\n"

    text += f"💰 **Сумма:** {order_data['total_price']} zł\n"
    text += f"💳 **Оплата:** {order_data['payment_method']}\n"

    # Send with payment proof if available
    if payment_proof_file_id:
        text += "\n🖼 Доказательство оплаты: приложено ниже"
        try:
            await bot.send_photo(
                chat_id=target,
                photo=payment_proof_file_id,
                caption=text,
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
            await bot.send_message(
                chat_id=target,
                text=text + "\n\n❌ Ошибка отправки фото",
                parse_mode="Markdown",
            )
    else:
        await bot.send_message(chat_id=target, text=text, parse_mode="Markdown")

    # Send JSON for easy forwarding
    json_data = json.dumps(order_data, ensure_ascii=False, indent=2)
    await bot.send_message(
        chat_id=target, text=f"```json\n{json_data}\n```", parse_mode="Markdown"
    )

    # Save order info (including user_id for admin lookup) to the orders dict
    # This enables admin to send documents/tracking back to the correct client
    orders[order_data["order_id"]] = {
        "status": "new",
        "user_id": user_id,
        "username": order_data.get("user", {}).get("username", "unknown"),
        "total_price": order_data.get("total_price", 0),
    }

    logger.info(f"Order {order_data['order_id']} sent to {target}")
    return target


async def send_tracking_to_client(
    bot: Bot, client_id: int, order_id: str, tracking_number: str
) -> None:
    """
    Отправляет клиенту уведомление с трек-номером для отслеживания посылки.

    Уведомляет клиента, что заказ готов и отправлен, и что посылку
    можно забрать в пачкомате в течение 2 дней.

    Args:
        bot: Экземпляр бота для отправки сообщения.
        client_id: ID чата клиента в Telegram.
        order_id: Номер заказа.
        tracking_number: Трек-номер для отслеживания.
    """
    text = (
        f"📦 **Ваш заказ готов!**\n\n"
        f"📋 Номер заказа: {order_id}\n"
        f"🔢 Трек-номер: `{tracking_number}`\n\n"
        f"📮 Заберите посылку в пачкомате в течение 2 дней.\n\n"
        f"Спасибо за заказ! 👋"
    )

    await bot.send_message(chat_id=client_id, text=text, parse_mode="Markdown")


async def send_document_to_client(
    bot: Bot,
    client_id: int,
    order_id: str,
    file_id: str,
    tracking_number: Optional[str] = None,
) -> None:
    """
    Отправляет клиенту готовый файл документа с уведомлением.

    Если указан трек-номер — добавляет информацию об отслеживании.
    В случае ошибки отправки файла отправляет только текстовое сообщение.

    Args:
        bot: Экземпляр бота для отправки файла.
        client_id: ID чата клиента в Telegram.
        order_id: Номер заказа.
        file_id: File_id готового документа в Telegram.
        tracking_number: Опциональный трек-номер для отслеживания.
    """
    text = f"📄 **Ваш заказ #{order_id} готов!**\n\n"

    if tracking_number:
        text += f"🔢 Трек-номер: `{tracking_number}`\n"
        text += "📮 Заберите посылку в пачкомате в течение 2 дней.\n\n"

    text += "Спасибо за заказ! 👋"

    try:
        await bot.send_document(
            chat_id=client_id, document=file_id, caption=text, parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error sending document: {e}")
        await bot.send_message(chat_id=client_id, text=text, parse_mode="Markdown")


async def forward_to_manager(
    bot: Bot, user_id: int, username: str, message_text: str, current_step: str
) -> None:
    """
    Пересылает запрос помощи от пользователя менеджеру.

    Вызывается при нажатии кнопки "Связь с менеджером".
    Отправляет в служебный чат информацию о пользователе,
    на каком этапе он находится и его последнее сообщение.

    Args:
        bot: Экземпляр бота для отправки сообщения.
        user_id: ID пользователя Telegram.
        username: Username пользователя (или "unknown").
        message_text: Текст последнего сообщения или причина запроса.
        current_step: Текущий шаг пользователя в процессе заказа.
    """
    # Send to default manager chat
    target = ROUTING["default"]

    text = (
        f"🆘 **Клиент запросил помощь**\n\n"
        f"👤 Клиент: @{username} (ID: {user_id})\n"
        f"📍 Застрял на этапе: {current_step}\n\n"
        f"💬 Последнее сообщение:\n"
        f"```\n{message_text}\n```"
    )

    await bot.send_message(chat_id=target, text=text, parse_mode="Markdown")

    logger.info(f"Help request from user {user_id} forwarded to manager")
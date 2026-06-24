"""Telegram delivery helpers for manager and client messages.

Order handlers call this module after checkout. It chooses the manager chat by
document type, sends the human-readable order and JSON payload, and stores the
minimum metadata admins need to send documents or tracking updates later.
"""

import json
import logging
from typing import Optional

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup

from config import ROUTING

# Import admin's order storage to save user_id for later client notifications
# This is a bridging fix; in production, use database
from handlers.admin import _orders_lock, orders
from keyboards.buttons import manager_order_keyboard
from templates.documents import get_template

logger = logging.getLogger(__name__)


async def _safe_send(
    bot: Bot,
    chat_id: int,
    text: str,
    parse_mode: Optional[str] = None,
    photo: Optional[str] = None,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
) -> None:
    """Safely send a message or photo to a Telegram chat.

    Catches all exceptions and logs them without re-raising.

    Args:
        bot: Bot instance.
        chat_id: Target chat ID.
        text: Message text.
        parse_mode: Parsing mode (Markdown / HTML).
        photo: File ID of a photo (if sending a photo).
        reply_markup: Inline keyboard markup.
    """
    try:
        if photo:
            await bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
            )
        else:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
            )
    except Exception as e:
        logger.warning(
            f"Failed to send {'photo' if photo else 'message'} to {chat_id}: {e}"
        )


async def send_order_to_manager(
    bot: Bot,
    order_data: dict,
    user_id: int,
    payment_proof_file_id: Optional[str] = None,
) -> int:
    """Send the order to the appropriate manager chat based on document type.

    Determines target chat by the first document's type.
    Builds a readable message with order details: document list, delivery info,
    total and payment method.

    Args:
        bot: Bot instance for sending messages.
        order_data: Order payload dictionary.
        user_id: Telegram user ID.
        payment_proof_file_id: File ID of the payment proof image (if any).

    Returns:
        Chat ID that the order was sent to.
    """
    if not order_data.get("documents"):
        logger.error("No documents in order data")
        return ROUTING["default"]

    main_doc_type = order_data["documents"][0]["type"]
    target = ROUTING.get(main_doc_type, ROUTING["default"])

    currency = order_data.get("currency", "EUR")

    # Build readable message
    text = f"🆕 **NEW ORDER #{order_data['order_id']}**\n"
    text += f"👤 Client: {order_data['user'].get('username') or f'ID: {user_id}'}\n\n"

    for doc in order_data["documents"]:
        doc_type = doc["type"]
        template = get_template(doc_type)
        doc_name = (template.get("name_en") or template.get("name_ru") or doc_type) \
            if template else doc_type

        text += f"📄 *{doc_name}* x{doc['quantity']}\n"

        for idx, item in enumerate(doc.get("items", []), 1):
            text += f"  {idx}. "
            for k, v in item.items():
                text += f"{k}: {v} "
            text += "\n"
        text += "\n"

    # Delivery info
    delivery = order_data.get("delivery")
    if delivery:
        text += "🚚 **Delivery:**\n"
        text += f"  Name: {delivery.get('name', '-')}\n"
        text += f"  Phone: {delivery.get('phone', '-')}\n"
        text += f"  Email: {delivery.get('email', '-')}\n"
        text += f"  Address: {delivery.get('address', '-')}\n\n"
    else:
        text += "🚚 Pickup (no delivery)\n\n"

    text += f"💰 **Total:** {order_data['total_price']} {currency}\n"
    text += f"💳 **Payment:** {order_data['payment_method']}\n"

    # Send with payment proof if available
    manager_keyboard = manager_order_keyboard(order_data["order_id"])
    if payment_proof_file_id:
        text += "\n🖼 Payment proof attached below"
        await _safe_send(
            bot=bot,
            chat_id=target,
            text=text,
            parse_mode="Markdown",
            photo=payment_proof_file_id,
            reply_markup=manager_keyboard,
        )
    else:
        await _safe_send(
            bot=bot,
            chat_id=target,
            text=text,
            parse_mode="Markdown",
            reply_markup=manager_keyboard,
        )

    # Send JSON for easy forwarding
    json_data = json.dumps(order_data, ensure_ascii=False, indent=2)
    await _safe_send(
        bot=bot,
        chat_id=target,
        text=f"```json\n{json_data}\n```",
        parse_mode="Markdown",
    )

    # Save order info (including user_id for admin lookup) to the orders dict
    with _orders_lock:
        orders[order_data["order_id"]] = {
            "status": "new",
            "user_id": user_id,
            "username": order_data.get("user", {}).get("username", "unknown"),
            "total_price": order_data.get("total_price", 0),
        }

    logger.info(f"Order {order_data['order_id']} processed (target: {target})")
    return target


async def send_tracking_to_client(
    bot: Bot, client_id: int, order_id: str, tracking_number: str
) -> None:
    """Send a tracking-number notification to the client.

    Args:
        bot: Bot instance.
        client_id: Client's Telegram chat ID.
        order_id: Order number.
        tracking_number: Tracking number.
    """
    text = (
        f"📦 **Your order is ready!**\n\n"
        f"📋 Order number: {order_id}\n"
        f"🔢 Tracking: `{tracking_number}`\n\n"
        f"📮 Please pick up your package within 2 days.\n\n"
        f"Thank you for your order! 👋"
    )

    await _safe_send(bot=bot, chat_id=client_id, text=text, parse_mode="Markdown")


async def send_document_to_client(
    bot: Bot,
    client_id: int,
    order_id: str,
    file_id: str,
    tracking_number: Optional[str] = None,
) -> None:
    """Send a completed document file to the client.

    Args:
        bot: Bot instance.
        client_id: Client's Telegram chat ID.
        order_id: Order number.
        file_id: Telegram file ID of the completed document.
        tracking_number: Optional tracking number.
    """
    text = f"📄 **Your order #{order_id} is ready!**\n\n"

    if tracking_number:
        text += f"🔢 Tracking: `{tracking_number}`\n"
        text += "Please pick up your package within 2 days.\n\n"

    text += "Thank you for your order! 👋"

    try:
        await bot.send_document(
            chat_id=client_id, document=file_id, caption=text, parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error sending document: {e}")
        await _safe_send(bot=bot, chat_id=client_id, text=text, parse_mode="Markdown")


async def forward_to_manager(
    bot: Bot, user_id: int, username: str, message_text: str, current_step: str
) -> None:
    """Forward a help request from a user to the manager chat.

    Args:
        bot: Bot instance.
        user_id: Telegram user ID.
        username: Username (or "unknown").
        message_text: Last message content or request reason.
        current_step: User's current step in the order flow.
    """
    target = ROUTING["default"]

    text = (
        f"🆘 **Client requested help**\n\n"
        f"👤 Client: @{username} (ID: {user_id})\n"
        f"📍 Stuck at: {current_step}\n\n"
        f"💬 Last message:\n"
        f"```\n{message_text}\n```"
    )

    await _safe_send(bot=bot, chat_id=target, text=text, parse_mode="Markdown")

    logger.info(f"Help request from user {user_id} forwarded to manager")

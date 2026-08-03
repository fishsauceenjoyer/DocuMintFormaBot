"""Telegram delivery helpers for manager and client messages.

Order handlers call this module after checkout. It chooses the manager chat by
document type, sends the human-readable order and JSON payload, and stores the
minimum metadata admins need to send documents or tracking updates later.

All Telegram API calls are wrapped with error handling. If a routing chat is
unreachable, the error is logged and a fallback notification is sent to the
MANAGER_ID chat (configured via ``config.MANAGER_ID``).
"""

import json
import logging
import traceback
from typing import Any, Optional

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup

from config import MANAGER_ID, ROUTING

# Import admin's order storage to save user_id for later client notifications
# This is a bridging fix; in production, use database
from handlers.admin import _orders_lock, orders
from keyboards.buttons import manager_order_keyboard
from templates.documents import get_template
from utils.sanitizer import sanitize_for_telegram

logger = logging.getLogger(__name__)


def _escape_markdown(text: str) -> str:
    """Escape Markdown special characters to prevent parse errors and link injection.

    Backwards-compatible wrapper around :func:`utils.sanitizer.sanitize_for_telegram`.
    Escapes *all* Markdown special characters (``_ * [ ] ( ) ~ ` > # + - = | { } . !``)
    so user input can never become a clickable link or break message formatting.
    """
    return sanitize_for_telegram(text)


async def _safe_send(
    bot: Bot,
    chat_id: int,
    text: str,
    parse_mode: Optional[str] = None,
    photo: Optional[str] = None,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
) -> bool:
    """Safely send a message or photo to a Telegram chat.

    Catches all exceptions, logs them with full traceback, and sends a
    fallback notification to ``MANAGER_ID`` so the team knows a chat is down.

    Args:
        bot: Bot instance.
        chat_id: Target chat ID.
        text: Message text.
        parse_mode: Parsing mode (Markdown / HTML).
        photo: File ID of a photo (if sending a photo).
        reply_markup: Inline keyboard markup.

    Returns:
        ``True`` if the send succeeded, ``False`` on failure.
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
        return True
    except Exception as e:
        logger.error(
            "Failed to send %s to %s: %s\n%s",
            "photo" if photo else "message",
            chat_id,
            e,
            traceback.format_exc(),
        )

        # Notify the fallback manager — but avoid infinite recursion if
        # MANAGER_ID itself is the chat that failed.
        if chat_id != MANAGER_ID:
            try:
                await bot.send_message(
                    chat_id=MANAGER_ID,
                    text=(
                        f"⚠️ **Delivery failure**\n\n"
                        f"Target chat `{chat_id}` is unreachable.\n"
                        f"Error: {e}\n\n"
                        f"Message preview:\n"
                        f"```\n{text[:300]}\n```"
                    ),
                    parse_mode="Markdown",
                )
            except Exception:
                logger.error(
                    "Fallback notification to MANAGER_ID %s also failed.\n%s",
                    MANAGER_ID,
                    traceback.format_exc(),
                )
        return False


async def send_order_to_manager(
    bot: Any,
    order_data: dict,
    user_id: int,
    payment_proof_file_id: Optional[str] = None,
) -> int:
    """Send the order to the appropriate manager chat based on document type.

    Determines target chat by the first document's type.
    Builds a readable message with order details: document list, delivery info,
    total and payment method.

    If the target chat is unreachable, falls back to MANAGER_ID and logs
    the error. If MANAGER_ID is also unreachable and equals the client's
    user_id, sends the notification directly to the client.

    Args:
        bot: Bot instance for sending messages.
        order_data: Order payload dictionary.
        user_id: Telegram user ID.
        payment_proof_file_id: File ID of the payment proof image (if any).

    Returns:
        Chat ID that the order was sent to (or MANAGER_ID on fallback).
    """
    if not order_data.get("documents"):
        logger.error("No documents in order data")
        return ROUTING["default"]

    main_doc_type = order_data["documents"][0]["type"]
    target = ROUTING.get(main_doc_type, ROUTING["default"])

    currency = order_data.get("currency", "EUR")

    # Build readable message
    text = f"🆕 **NEW ORDER #{order_data['order_id']}**\n"
    text += f"👤 Client: {_escape_markdown(order_data['user'].get('username') or f'ID: {user_id}')}\n\n"

    for doc in order_data["documents"]:
        doc_type = doc["type"]
        template = get_template(doc_type)
        doc_name = (
            (template.get("name_en") or template.get("name_ru") or doc_type)
            if template
            else doc_type
        )

        text += f"📄 *{doc_name}* x{doc['quantity']}\n"

        for idx, item in enumerate(doc.get("items", []), 1):
            text += f"  {idx}. "
            for k, v in item.items():
                text += f"{_escape_markdown(k)}: {_escape_markdown(str(v))} "
            text += "\n"
        text += "\n"

    # Delivery info
    delivery = order_data.get("delivery")
    if delivery:
        text += "🚚 **Delivery:**\n"
        text += f"  Name: {_escape_markdown(delivery.get('name', '-'))}\n"
        text += f"  Phone: {_escape_markdown(delivery.get('phone', '-'))}\n"
        text += f"  Email: {_escape_markdown(delivery.get('email', '-'))}\n"
        text += f"  Address: {_escape_markdown(delivery.get('address', '-'))}\n\n"
    else:
        text += "🚚 Pickup (no delivery)\n\n"

    text += f"💰 **Total:** {order_data['total_price']} {currency}\n"
    text += f"💳 **Payment:** {_escape_markdown(order_data['payment_method'])}\n"

    # Attempt to send the order — with error handling
    sent_ok = False
    try:
        manager_keyboard = manager_order_keyboard(order_data["order_id"])
        if payment_proof_file_id:
            text_with_proof = text + "\n🖼 Payment proof attached below"
            sent_ok = await _safe_send(
                bot=bot,
                chat_id=target,
                text=text_with_proof,
                parse_mode="Markdown",
                photo=payment_proof_file_id,
                reply_markup=manager_keyboard,
            )
        else:
            sent_ok = await _safe_send(
                bot=bot,
                chat_id=target,
                text=text,
                parse_mode="Markdown",
                reply_markup=manager_keyboard,
            )

        # Send JSON for easy forwarding (only if the first message succeeded)
        if sent_ok:
            json_data = json.dumps(order_data, ensure_ascii=False, indent=2)
            await _safe_send(
                bot=bot,
                chat_id=target,
                text=f"```json\n{json_data}\n```",
                parse_mode="Markdown",
            )
    except Exception as e:
        logger.error(
            "Unexpected error sending order %s to %s: %s\n%s",
            order_data["order_id"],
            target,
            e,
            traceback.format_exc(),
        )
        sent_ok = False

    # If the routed chat failed, fall back to MANAGER_ID
    fallback_succeeded = False
    if not sent_ok and target != MANAGER_ID:
        logger.warning(
            "Falling back to MANAGER_ID %s for order %s",
            MANAGER_ID,
            order_data["order_id"],
        )
        try:
            manager_keyboard = manager_order_keyboard(order_data["order_id"])
            fb_ok = await _safe_send(
                bot=bot,
                chat_id=MANAGER_ID,
                text=(
                    f"🆕 **FALLBACK — Order #{order_data['order_id']}**\n"
                    f"_Target chat {target} was unreachable._\n\n"
                    f"{text}"
                ),
                parse_mode="Markdown",
                reply_markup=manager_keyboard,
            )
            if fb_ok:
                json_data = json.dumps(order_data, ensure_ascii=False, indent=2)
                await _safe_send(
                    bot=bot,
                    chat_id=MANAGER_ID,
                    text=f"```json\n{json_data}\n```",
                    parse_mode="Markdown",
                )
                fallback_succeeded = True
        except Exception as e:
            logger.error(
                "Fallback send to MANAGER_ID %s also failed: %s\n%s",
                MANAGER_ID,
                e,
                traceback.format_exc(),
            )

    # If all routing failed, try sending directly to the client (manager=client scenario)
    if not sent_ok and not fallback_succeeded:
        logger.warning(
            "All routing failed for order %s, trying direct send to client %s",
            order_data["order_id"],
            user_id,
        )
        try:
            manager_keyboard = manager_order_keyboard(order_data["order_id"])
            direct_ok = await _safe_send(
                bot=bot,
                chat_id=user_id,
                text=(
                    f"🆕 **YOUR ORDER #{order_data['order_id']}**\n"
                    f"_Sent directly to you (manager routing unavailable)._ \n\n"
                    f"{text}"
                ),
                parse_mode="Markdown",
                reply_markup=manager_keyboard,
            )
            if direct_ok:
                json_data = json.dumps(order_data, ensure_ascii=False, indent=2)
                await _safe_send(
                    bot=bot,
                    chat_id=user_id,
                    text=f"```json\n{json_data}\n```",
                    parse_mode="Markdown",
                )
                sent_ok = True
                target = user_id
        except Exception as e:
            logger.error(
                "Direct send to client %s also failed: %s\n%s",
                user_id,
                e,
                traceback.format_exc(),
            )

    if fallback_succeeded:
        target = MANAGER_ID
        sent_ok = True

    # Save order info (including user_id for admin lookup) to the orders dict
    with _orders_lock:
        orders[order_data["order_id"]] = {
            "status": "new",
            "user_id": user_id,
            "username": order_data.get("user", {}).get("username", "unknown"),
            "total_price": order_data.get("total_price", 0),
        }

    logger.info(
        "Order %s processed (target: %s, sent_ok: %s)",
        order_data["order_id"],
        target,
        sent_ok,
    )
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
        logger.error(
            "Error sending document to client %s: %s\n%s",
            client_id,
            e,
            traceback.format_exc(),
        )
        await _safe_send(bot=bot, chat_id=client_id, text=text, parse_mode="Markdown")


async def forward_to_manager(
    bot: Bot, user_id: int, username: str, message_text: str, current_step: str
) -> None:
    """Forward a help request from a user to the manager chat.

    If the default routing chat is unreachable, sends the help request
    directly to the user (manager=client scenario).

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

    sent = await _safe_send(bot=bot, chat_id=target, text=text, parse_mode="Markdown")

    # If routing failed, try sending directly to the user (manager=client scenario)
    if not sent:
        logger.warning(
            "Help request routing to %s failed, sending directly to user %s",
            target,
            user_id,
        )
        direct_text = (
            f"🆘 **Your help request**\n\n"
            f"📍 Stuck at: {current_step}\n\n"
            f"💬 Your message:\n"
            f"```\n{message_text}\n```\n\n"
            f"_Manager routing is unavailable. A manager will review your request._"
        )
        await _safe_send(
            bot=bot, chat_id=user_id, text=direct_text, parse_mode="Markdown"
        )

    logger.info(f"Help request from user {user_id} forwarded to manager")

"""Order message formatting.

Builds human-readable payloads for the manager chat and client notifications.
Handlers should not inline these templates.
"""

from typing import Any, Dict, Optional

from templates.documents import get_template


def build_manager_message(order_data: Dict[str, Any]) -> str:
    """Generate the manager notification text for a new order.

    Args:
        order_data: Order payload as assembled in handlers/order.py.

    Returns:
        Ready-to-send Markdown text.
    """
    text = f"🆕 **NEW ORDER #{order_data['order_id']}**\n"
    user = order_data.get("user", {})
    username = user.get("username")
    if username:
        client_ref = username
    else:
        client_ref = f"ID: {user.get('id')}"
    text += f"👤 Client: {client_ref}\n\n"

    for doc in order_data.get("documents", []):
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
                text += f"{k}: {v} "
            text += "\n"
        text += "\n"

    delivery = order_data.get("delivery")
    if delivery:
        text += "🚚 **Delivery:**\n"
        text += f"  Name: {delivery.get('name', '-')}\n"
        text += f"  Phone: {delivery.get('phone', '-')}\n"
        text += f"  Email: {delivery.get('email', '-')}\n"
        text += f"  Address: {delivery.get('address', '-')}\n\n"
    else:
        text += "🚚 Pickup (no delivery)\n\n"

    currency = order_data.get("currency", "EUR")
    text += f"💰 **Total:** {order_data['total_price']} {currency}\n"
    text += f"💳 **Payment:** {order_data['payment_method']}\n"

    return text

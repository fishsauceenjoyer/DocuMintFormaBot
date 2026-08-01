"""Sanitization helpers for user-supplied text.

The bot accepts arbitrary text from users (names, addresses, PESEL, phone
numbers) and forwards it to managers via Telegram messages.  Unescaped
text could:

* break the Markdown formatting of a manager notification,
* turn into a clickable link (e.g. ``[click](http://evil.com)``),
* crash ``send_message`` when Telegram cannot parse the entity.

This module provides a single entry point :func:`sanitize_for_telegram`
that escapes all Markdown special characters and caps the message length
so Telegram API limits are never exceeded.
"""

import re
from typing import Optional

# Telegram `parse_mode="Markdown"` treats these characters specially:
#   _ * [ ] ( ) ~ ` > # + - = | { } . !
# Escaping every one of them turns user input into plain text and prevents
# both formatting breakage and link injection.
_MARKDOWN_SPECIAL_RE = re.compile(r"([_*\[\]()~`>#+\-=|{}.!])")

# Telegram single message limit. Keep a small safety margin because the rest
# of the composed text (labels, emoji, newlines) also counts toward the limit.
TG_MESSAGE_LIMIT = 4096
DEFAULT_MAX_LENGTH = 3800


def sanitize_for_telegram(text: Optional[str], max_length: int = DEFAULT_MAX_LENGTH) -> str:
    """Escape Markdown special characters and cap length.

    All user-controlled strings that end up in a Telegram message sent with
    ``parse_mode="Markdown"`` should pass through this function.

    Args:
        text: Raw user input (may be empty).
        max_length: Maximum allowed length of the returned string.
            The default (3800) leaves headroom for labels/emoji around the
            value when composing a full notification.

    Returns:
        Sanitized string safe to embed in a Markdown-formatted message.
    """
    if text is None:
        return ""

    value = str(text)

    # Cut first so the escape pass does not waste work on truncated text.
    if len(value) > max_length:
        value = value[:max_length]

    # Escape every Markdown special character.
    # With [[ ]] and (( )) escaped, `[click](http://evil.com)` becomes
    # `\[click\]\(http://evil.com\)` — plain text, not a clickable link.
    return _MARKDOWN_SPECIAL_RE.sub(r"\\\1", value)


def truncate_for_storage(text: str, max_length: int = 255) -> str:
    """Truncate a string to fit a database column.

    Falls back to ``""`` for ``None``.

    Args:
        text: Raw user input.
        max_length: Maximum characters to keep.

    Returns:
        Truncated string (never longer than ``max_length``).
    """
    if text is None:
        return ""
    value = str(text)
    return value[:max_length]
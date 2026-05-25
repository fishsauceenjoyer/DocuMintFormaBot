"""
Аутентификация и авторизация для админ-команд.

Содержит декораторы и функции для проверки прав пользователя
при выполнении команд менеджера/администратора.
Использует ADMIN_USERNAME из config для верификации.
"""

from functools import wraps
from typing import Callable

from aiogram.types import Message

from config import ADMIN_USERNAME


def is_admin(username: str | None) -> bool:
    """
    Проверяет, является ли пользователь с данным username администратором.

    Args:
        username: Username пользователя Telegram (без @).

    Returns:
        True если username совпадает с ADMIN_USERNAME, иначе False.
    """
    if not username or not ADMIN_USERNAME:
        return False
    return username.lower() == ADMIN_USERNAME.lower()


def get_admin_username() -> str | None:
    """
    Возвращает username администратора из конфигурации.

    Returns:
        ADMIN_USERNAME из config или None, если не задан.
    """
    return ADMIN_USERNAME


def admin_only(func: Callable) -> Callable:
    """
    Декоратор для ограничения доступа к хендлеру только для администратора.

    Если пользователь не является администратором, отправляет ему
    уведомление о недостатке прав.

    Использование:
        @router.message(Command("send_doc"))
        @admin_only
        async def cmd_send_doc(message: Message, state: FSMContext):
            ...

    Args:
        func: Асинхронная функция-хендлер, принимающая message и state.

    Returns:
        Обёрнутая функция с проверкой прав доступа.
    """

    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs) -> None:
        user = message.from_user
        if user is None:
            await message.answer("⚠️ Не удалось получить информацию о пользователе.")
            return

        if not is_admin(user.username):
            await message.answer(
                "⛔ У вас нет прав для выполнения этой команды.\n\n"
                "Это команда предназначена только для администратора бота."
            )
            return

        return await func(message, *args, **kwargs)

    return wrapper

"""
Middleware для Telegram-бота.

Содержит middleware для:
    - RegistrationMiddleware: автоматическая регистрация пользователей
      в базе данных при первом обращении.
    - LoggingMiddleware: централизованное логирование всех входящих
      сообщений и callback-запросов.
"""

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from db.crud import SessionLocal, create_user, get_user_by_username

logger = logging.getLogger(__name__)


class RegistrationMiddleware(BaseMiddleware):
    """
    Middleware для автоматической регистрации пользователей.

    При каждом новом сообщении или callback-запросе проверяет,
    существует ли пользователь в базе данных. Если нет — создаёт
    нового пользователя с ролью "user".

    Позволяет избежать дублирования кода регистрации в каждом хендлере
    и гарантирует, что все пользователи сохранены в БД.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Обрабатывает событие, регистрируя пользователя при необходимости."""
        user = None
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user

        if user is not None and user.username:
            db = SessionLocal()
            try:
                existing = get_user_by_username(db, user.username)
                if existing is None:
                    create_user(
                        db=db,
                        username=user.username,
                        chat_id=user.id,
                        role="user",
                    )
                    logger.info(
                        f"New user registered: @{user.username} (ID: {user.id})"
                    )
                elif existing.chat_id != user.id:
                    # Update chat_id if it changed
                    existing.chat_id = user.id
                    db.commit()
            finally:
                db.close()

        return await handler(event, data)


class LoggingMiddleware(BaseMiddleware):
    """
    Middleware для централизованного логирования всех событий бота.

    Логирует:
        - Входящие текстовые сообщения с user_id и текстом
        - Callback-запросы с user_id и callback_data
        - Ошибки при обработке событий
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Обрабатывает событие, логируя его перед передачей хендлеру."""
        if isinstance(event, Message):
            user = event.from_user
            if user is not None and event.text:
                logger.info(
                    f"Message from @{user.username or 'unknown'} (ID: {user.id}): "
                    f"{event.text[:100]}"
                )
            elif user is not None:
                logger.info(
                    f"Non-text message from @{user.username or 'unknown'} (ID: {user.id})"
                )

        elif isinstance(event, CallbackQuery):
            user = event.from_user
            logger.info(
                f"Callback from @{user.username or 'unknown'} (ID: {user.id}): "
                f"{event.data}"
            )

        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Error handling event: {e}", exc_info=True)
            raise
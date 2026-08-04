"""Application entry point.

The module validates environment configuration, initializes the database,
registers all aiogram routers, and starts Telegram polling.
"""

import logging
import os
from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, validate_config
from db.crud import init_db
from handlers.admin import router as admin_router
from handlers.fast_order import router as fast_order_router
from handlers.order import router as order_router
from handlers.start import router as start_router

validate_config()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

if BOT_TOKEN is None:
    raise ValueError("BOT_TOKEN not found in .env file")


async def main() -> None:
    """Start polling and wire together storage, middlewares, and routers.

    Completed orders are stored in the SQL database. Conversation state is
    stored in Redis when REDIS_URL is present; otherwise MemoryStorage is used
    and unfinished user flows are lost after process restart.
    """
    logger.info("Starting bot...")

    # Initialize the database (async engine + default document types)
    await init_db()

    # Initialize storage — prefer Redis in production, fallback to MemoryStorage
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            from aiogram.fsm.storage.redis import RedisStorage

            storage: Any = RedisStorage.from_url(redis_url)
            logger.info("Using RedisStorage (production)")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis at {redis_url}: {e}")
            logger.info("Falling back to MemoryStorage")
            storage = MemoryStorage()
    else:
        logger.info("REDIS_URL not set, using MemoryStorage (sessions lost on restart)")
        storage = MemoryStorage()

    bot = Bot(token=BOT_TOKEN)  # type: ignore
    dp = Dispatcher(storage=storage)

    # Register middleware
    from utils.middleware import LoggingMiddleware, RegistrationMiddleware

    dp.message.middleware(RegistrationMiddleware())
    dp.callback_query.middleware(RegistrationMiddleware())
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    logger.info("Middleware registered: RegistrationMiddleware, LoggingMiddleware")

    # Include routers
    dp.include_router(start_router)
    dp.include_router(order_router)
    dp.include_router(fast_order_router)
    dp.include_router(admin_router)

    logger.info("Bot started successfully!")

    # Start polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

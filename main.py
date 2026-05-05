"""Main entry point for the Telegram bot."""

import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from handlers.admin import router as admin_router
from handlers.fast_order import router as fast_order_router
from handlers.order import router as order_router
# Import handlers
from handlers.start import router as start_router

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get token
BOT_TOKEN = os.getenv("BOT_TOKEN")
if BOT_TOKEN is None:
    raise ValueError("BOT_TOKEN not found in .env file")


async def main() -> None:
    """
    Запускает бота и начинает обработку сообщений от пользователей.

    Функция выполняет следующие шаги:
    1. Создаёт экземпляр Bot с токеном из переменной окружения BOT_TOKEN.
    2. Создаёт Dispatcher с хранилищем состояний (MemoryStorage).
    3. Подключает все обработчики команд (start, order, fast_order, admin).
    4. Запускает цикл опроса Telegram API (polling) для получения новых сообщений.

    Внимание: MemoryStorage хранит данные сессий в оперативной памяти,
    поэтому после перезапуска бота все незавершённые заказы будут потеряны.
    В продакшене рекомендуется заменить на RedisStorage.

    Raises:
        ValueError: Если BOT_TOKEN не найден в переменных окружения.
    """
    logger.info("Starting bot...")

    # Initialize bot and dispatcher
    # For production, use RedisStorage instead of MemoryStorage
    # storage = RedisStorage.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
    storage = MemoryStorage()

    bot = Bot(token=BOT_TOKEN) # type: ignore
    dp = Dispatcher(storage=storage)

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

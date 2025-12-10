import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import settings
from bot.routers import start_router, navigation_router, chat_router


def setup_logging() -> None:
    """Базовая настройка логирования по уровню из конфига."""
    level_name = (settings.log_level or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    logging.getLogger("aiogram").setLevel(level)
    logging.getLogger("httpx").setLevel(level)


async def main() -> None:
    """Точка входа для бота."""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("🚀 BlackBox GPT бот запускается...")

    bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())

    # Подключаем все роутеры
    dp.include_router(start_router)
    dp.include_router(navigation_router)
    dp.include_router(chat_router)

    logger.info("✅ Роутеры зарегистрированы, запускаем polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

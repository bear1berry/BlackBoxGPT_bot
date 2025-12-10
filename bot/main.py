import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import settings
from bot.routers import start_router, navigation_router, chat_router


def setup_logging() -> None:
    """
    Базовая настройка логирования по уровню из конфига.

    Уровень берём из settings.log_level (по умолчанию INFO).
    """
    level_name = (settings.log_level or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    logging.getLogger("aiogram").setLevel(level)
    logging.getLogger("httpx").setLevel(level)


async def main() -> None:
    """Точка входа для BlackBox GPT бота."""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("🚀 BlackBox GPT бот запускается...")

    # Инициализация бота
    bot = Bot(
        token=settings.bot_token,
        parse_mode=ParseMode.HTML,
    )

    # Память FSM — можно потом заменить на Redis / БД
    dp = Dispatcher(storage=MemoryStorage())

    # Подключаем роутеры
    dp.include_router(start_router)
    dp.include_router(navigation_router)
    dp.include_router(chat_router)

    logger.info("✅ Роутеры зарегистрированы, запускаем polling...")
    try:
        await dp.start_polling(bot)
    finally:
        logger.info("🛑 Останавливаем бота...")
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.routers import chat_router, navigation_router, start_router


def setup_logging() -> None:
    """
    Настройка логгера на основе settings.log_level.
    """
    level_name = getattr(settings, "log_level", "INFO")
    level = getattr(logging, level_name.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logging.getLogger("aiogram.event").setLevel(logging.INFO)


async def main() -> None:
    """
    Точка входа Telegram-бота.
    """
    setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("=== BlackBox GPT bot starting ===")

    # Создаём бота
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Диспетчер и маршрутизаторы
    dp = Dispatcher()

    # Подключаем роутеры
    dp.include_router(start_router)
    dp.include_router(navigation_router)
    dp.include_router(chat_router)

    logger.info("Routers are included. Start polling...")

    # Запуск long-polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.getLogger(__name__).info("Bot stopped by user/system.")

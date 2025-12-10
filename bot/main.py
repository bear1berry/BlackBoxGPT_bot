# bot/main.py

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.routers import chat_router, navigation_router, start_router


def setup_logging() -> None:
    """
    Настройка логирования на основе settings.log_level.
    Если уровень в .env невалидный, по умолчанию используем INFO.
    """
    level_name = getattr(settings, "log_level", "INFO")
    level = getattr(logging, str(level_name).upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logging.getLogger("aiogram").setLevel(level)


async def main() -> None:
    """
    Точка входа бота.
    Запускает long polling через aiogram 3.x.
    """
    setup_logging()
    logger = logging.getLogger("bot.main")

    # Создаём Bot
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Диспетчер и роутеры
    dp = Dispatcher()

    # Порядок важен: сначала старт, потом навигация, потом чат
    dp.include_router(start_router)
    dp.include_router(navigation_router)
    dp.include_router(chat_router)

    # На всякий случай очищаем висящие апдейты
    await bot.delete_webhook(drop_pending_updates=True)

    logger.info("BlackBox GPT bot is starting polling...")

    # Стартуем polling
    try:
        await dp.start_polling(bot)
    finally:
        logger.info("BlackBox GPT bot stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.getLogger("bot.main").info("BlackBox GPT bot terminated by user.")

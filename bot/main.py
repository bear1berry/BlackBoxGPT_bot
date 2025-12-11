# bot/main.py

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import Settings
from bot.handlers import register_all_handlers


logger = logging.getLogger(__name__)


async def main() -> None:
    """
    Entry point for BlackBox GPT Telegram bot.
    """

    # ----- Logging -----
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info("Starting BlackBox GPT bot...")

    # ----- Settings -----
    settings = Settings()

    # ----- Bot & Dispatcher -----
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # ----- Routers / handlers -----
    # Вся регистрация хэндлеров — внутри bot/handlers/__init__.py
    register_all_handlers(dp)

    # ----- Webhook cleanup before start -----
    # На всякий случай гасим возможный вебхук, чтобы polling не конфликтовал.
    await bot.delete_webhook(drop_pending_updates=True)

    # ----- Polling loop -----
    try:
        logger.info("Bot polling started")
        await dp.start_polling(bot)
    except Exception:
        logger.exception("Unexpected error in polling loop")
        raise
    finally:
        # Корректно закрываем HTTP-сессию aiogram, чтобы не было
        # Unclosed client session / Unclosed connector.
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())

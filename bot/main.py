# bot/main.py
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode

from .config import settings
from .db import init_db
from .routers import start_router, navigation_router, chat_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("Starting BlackBox GPT bot...")

    await init_db()

    bot = Bot(token=settings.BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(navigation_router)
    dp.include_router(chat_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from .config import get_settings
from .db.db import create_db_pool, close_db_pool, init_db
from .routers import setup_routers


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()

    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is not set")

    bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    # DB
    await create_db_pool(settings.db_dsn)
    await init_db()
    logger.info("Database pool initialised")

    setup_routers(dp)

    try:
        logger.info("Starting polling")
        await dp.start_polling(bot)
    finally:
        await close_db_pool()
        logger.info("Database pool closed")


if __name__ == "__main__":
    asyncio.run(main())

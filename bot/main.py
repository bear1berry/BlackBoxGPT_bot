import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from .config import settings
from .routers import setup_routers
from .db import db


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = Dispatcher(storage=MemoryStorage())
    setup_routers(dp)

    await db.connect()
    logging.getLogger(__name__).info("Database pool initialised")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logging.getLogger(__name__).info("Starting polling")
        await dp.start_polling(bot)
    finally:
        await db.close()
        logging.getLogger(__name__).info("Database pool closed")


if __name__ == "__main__":
    asyncio.run(main())

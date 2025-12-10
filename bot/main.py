from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from bot.config import settings
from bot.handlers import (
    admin,
    chat,
    modes,
    profile,
    referrals,
    start,
    subscription,
)
from bot.middlewares.user_context import UserContextMiddleware
from bot.storage.db import init_db
from bot.utils.logging import setup_logging


async def main() -> None:
    setup_logging(level=settings.log_level)

    bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    # Routers
    dp.include_router(start.router)
    dp.include_router(modes.router)
    dp.include_router(profile.router)
    dp.include_router(subscription.router)
    dp.include_router(referrals.router)
    dp.include_router(admin.router)
    dp.include_router(chat.router)

    # Middlewares
    dp.update.outer_middleware(UserContextMiddleware())

    # DB init
    await init_db()

    logging.getLogger(__name__).info("Starting polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.getLogger(__name__).info("Bot stopped.")

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import Settings
from bot.routers import admin, chat, navigation, start
from db import create_all, init_engine


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    settings = Settings()

    # Init DB
    await init_engine(settings.DB_URL)
    await create_all()

    # Init bot
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Routers
    dp.include_router(start.router)
    dp.include_router(navigation.router)
    dp.include_router(admin.router)
    dp.include_router(chat.router)

    logging.info("Starting polling as @%s", settings.BOT_USERNAME)

    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types(),
    )


if __name__ == "__main__":
    asyncio.run(main())

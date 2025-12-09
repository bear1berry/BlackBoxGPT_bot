from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.routers import start_router, navigation_router, chat_router, voice_router


def setup_logging() -> None:
    level_name = settings.log_level.upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


async def main() -> None:
    setup_logging()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    dp.include_router(start_router)
    dp.include_router(navigation_router)
    dp.include_router(voice_router)
    dp.include_router(chat_router)

    logging.getLogger(__name__).info("Starting BlackBox GPT bot polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

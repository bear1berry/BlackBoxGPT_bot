from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import Settings
from bot.routers import setup_routers
from bot.middlewares import UsageLimitMiddleware
from bot.services.llm import LLMClient


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )


async def main() -> None:
    setup_logging()

    settings = Settings()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    bot["settings"] = settings
    bot["llm_client"] = LLMClient(settings)

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(setup_routers())

    dp.message.middleware(UsageLimitMiddleware())

    logging.getLogger(__name__).info("Starting BlackBox GPT bot...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass

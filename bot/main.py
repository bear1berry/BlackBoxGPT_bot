import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import get_settings
from bot.routers import admin, chat, navigation, start
from services.llm import init_llm_clients, close_llm_clients


async def on_startup(router, bot: Bot) -> None:
    """Initialize external services (LLM clients, etc.)."""
    settings = get_settings()
    await init_llm_clients(settings)
    logging.getLogger(__name__).info("LLM clients initialized")


async def on_shutdown(router, bot: Bot) -> None:
    """Gracefully shutdown external services."""
    await close_llm_clients()
    logging.getLogger(__name__).info("LLM clients closed")


async def main() -> None:
    settings = get_settings()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(navigation.router)
    dp.include_router(admin.router)
    dp.include_router(chat.router)

    # Register lifecycle hooks
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logging.info("Starting polling as @%s", settings.BOT_USERNAME)

    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types(),
    )


if __name__ == "__main__":
    asyncio.run(main())

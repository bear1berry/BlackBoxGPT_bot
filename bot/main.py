# bot/main.py

import asyncio
import logging
import pkgutil
import importlib

from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode

from bot.config import settings


logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Базовая настройка логирования для всего бота."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    # Уменьшаем шум от httpx / aiohttp, если нужно
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


def include_all_routers(dp: Dispatcher) -> None:
    """
    Автоматически находит и подключает все Router'ы из пакета bot.handlers.

    Ожидается, что в каждом файле в bot/handlers/*.py
    есть объект `router` типа aiogram.Router (паттерн aiogram v3).
    Если где-то его нет или модуль падает при импорте — это не ломает запуск,
    а просто логируется.
    """
    import bot.handlers as handlers_pkg  # type: ignore

    for module_info in pkgutil.iter_modules(handlers_pkg.__path__):
        module_name = module_info.name
        full_name = f"{handlers_pkg.__name__}.{module_name}"

        try:
            module = importlib.import_module(full_name)
        except Exception as e:
            logger.exception("Не удалось импортировать модуль хэндлеров %s: %s", full_name, e)
            continue

        router = getattr(module, "router", None)

        if isinstance(router, Router):
            dp.include_router(router)
            logger.info("✅ Router подключён: %s.router", full_name)
        else:
            logger.info("ℹ️ В модуле %s нет router, пропускаем", full_name)


async def main() -> None:
    """Точка входа в приложение."""
    setup_logging()
    logger.info("🚀 Запуск BlackBox GPT bot")

    # Токен и прочие настройки берём из pydantic-конфига
    bot_token = settings.BOT_TOKEN

    # Используем контекстный менеджер, чтобы корректно закрыть HTTP-сессию бота
    async with Bot(token=bot_token, parse_mode=ParseMode.HTML) as bot:
        dp = Dispatcher()

        # Кладём настройки в контекст диспетчера, чтобы их можно было забирать в хэндлерах
        dp["settings"] = settings

        # Подключаем все routers из bot/handlers/*
        include_all_routers(dp)

        logger.info("🤖 Бот запускает long polling...")
        # Здесь нет никаких startup-хендлеров с кривой сигнатурой — только чистый polling
        await dp.start_polling(bot)

    logger.info("🛑 Бот остановлен корректно")


if __name__ == "__main__":
    asyncio.run(main())

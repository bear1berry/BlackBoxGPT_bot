import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import settings
from bot.routers import start, menu, profile, subscription, referrals, chat
from bot.db.db import init_db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    # Инициализация базы данных
    await init_db()

    # Инициализация бота и диспетчера
    bot = Bot(token=settings.BOT_TOKEN.get_secret_value(), parse_mode=ParseMode.MARKDOWN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Регистрация роутеров
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(profile.router)
    dp.include_router(subscription.router)
    dp.include_router(referrals.router)
    dp.include_router(chat.router)

    # Запуск поллинга
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

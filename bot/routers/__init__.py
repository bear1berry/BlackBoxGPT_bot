from aiogram import Dispatcher

from . import start, chat


def setup_routers(dp: Dispatcher) -> None:
    dp.include_router(start.router)
    dp.include_router(chat.router)

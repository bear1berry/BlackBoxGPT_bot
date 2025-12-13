from aiogram import Router

from bot.routers.start import router as start_router
from bot.routers.menu import router as menu_router
from bot.routers.chat import router as chat_router
from bot.routers.continue_ import router as continue_router


def setup_routers() -> Router:
    r = Router()
    r.include_router(start_router)
    r.include_router(menu_router)
    r.include_router(continue_router)
    r.include_router(chat_router)
    return r

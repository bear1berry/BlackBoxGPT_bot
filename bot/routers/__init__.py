from aiogram import Router

from . import start, navigation, chat


def setup_routers() -> Router:
    router = Router(name="root")
    router.include_router(start.router)
    router.include_router(navigation.router)
    router.include_router(chat.router)
    return router

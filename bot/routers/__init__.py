from __future__ import annotations

from aiogram import Router

from . import start, chat


def setup_routers() -> Router:
    router = Router()
    router.include_router(start.router)
    router.include_router(chat.router)
    return router

from aiogram import Router

from . import start, modes, profile, chat, subscription, referral


def setup_routers() -> Router:
    root_router = Router()
    root_router.include_router(start.router)
    root_router.include_router(modes.router)
    root_router.include_router(profile.router)
    root_router.include_router(subscription.router)
    root_router.include_router(referral.router)
    root_router.include_router(chat.router)
    return root_router

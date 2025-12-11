from aiogram import Dispatcher

from .start import router as start_router
from .menu import router as menu_router
from .profile import router as profile_router
from .subscription import router as subscription_router
from .referrals import router as referrals_router
from .chat import router as chat_router


def setup_routers(dp: Dispatcher) -> None:
    dp.include_router(start_router)
    dp.include_router(menu_router)
    dp.include_router(profile_router)
    dp.include_router(subscription_router)
    dp.include_router(referrals_router)
    dp.include_router(chat_router)

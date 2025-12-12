from .start import router as start_router
from .menu import router as menu_router
from .profile import router as profile_router
from .subscription import router as subscription_router
from .referrals import router as referrals_router
from .chat import router as chat_router

__all__ = [
    "start_router",
    "menu_router",
    "profile_router",
    "subscription_router",
    "referrals_router",
    "chat_router"
]

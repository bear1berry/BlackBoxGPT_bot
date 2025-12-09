from .start import router as start_router
from .navigation import router as navigation_router
from .chat import router as chat_router
from .voice import router as voice_router

__all__ = ["start_router", "navigation_router", "chat_router", "voice_router"]

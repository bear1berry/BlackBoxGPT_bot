from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.storage.repo import UserRepository


class UserContextMiddleware:
    """
    Простая обёртка: гарантирует, что пользователь есть в БД.
    """

    def __init__(self) -> None:
        self._repo = UserRepository()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        tg_user = None
        if isinstance(event, Message):
            tg_user = event.from_user
        elif isinstance(event, CallbackQuery):
            tg_user = event.from_user

        if tg_user:
            await self._repo.get_or_create(
                user_id=tg_user.id,
                username=tg_user.username,
            )

        return await handler(event, data)

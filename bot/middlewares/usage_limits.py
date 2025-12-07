from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.session import async_session_maker
from bot.db.models import User
from bot.services.subscriptions import get_user_tariff
from bot.services.usage import can_make_request

logger = logging.getLogger(__name__)


class UsageLimitMiddleware(BaseMiddleware):
    """
    Проверяет лимит запросов перед отправкой в LLM.
    Работает только для обычных текстовых сообщений (не команд).
    """

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        message = event

        if not message.text or message.text.startswith("/"):
            return await handler(message, data)

        session_maker = async_session_maker

        async with session_maker() as session:  # type: AsyncSession
            user = await self._ensure_user(session, message)
            plan = await get_user_tariff(session, user.id)

            allowed = await can_make_request(session, user.id, plan)
            if not allowed:
                await message.answer(
                    "Лимит запросов на сегодня исчерпан.\n\n"
                    "Обнови план в разделе 💎 Подписка, чтобы продолжить диалог.",
                )
                return

        return await handler(message, data)

    async def _ensure_user(self, session: AsyncSession, message: Message) -> User:
        from bot.services.profiles import get_or_create_user

        tg = message.from_user
        assert tg is not None

        user = await get_or_create_user(
            session=session,
            tg_id=tg.id,
            username=tg.username,
            first_name=tg.first_name,
            last_name=tg.last_name,
            language_code=tg.language_code,
        )
        await session.commit()
        return user

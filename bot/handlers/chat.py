from __future__ import annotations

from typing import List

import logging
from aiogram import Router, F
from aiogram.types import Message

from sqlalchemy import select

from bot.db.base import async_session_factory
from bot.db.models import User, MessageLog
from services.llm import ask_llm, get_system_prompt
from services.user_service import ensure_daily_quota, get_or_create_user


router = Router()


@router.message(F.text & ~F.text.startswith("/"))
async def handle_chat(message: Message) -> None:
    async with async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            user = await get_or_create_user(session, message.from_user)

        allowed, reason = await ensure_daily_quota(session, user)
        if not allowed:
            await session.commit()
            await message.answer(reason)
            return

        # load last 10 messages from history
        result = await session.execute(
            select(MessageLog)
            .where(MessageLog.user_id == user.id)
            .order_by(MessageLog.id.desc())
            .limit(10)
        )
        history = list(reversed(result.scalars().all()))

        messages: List[dict[str, str]] = [
            {"role": "system", "content": get_system_prompt(user.mode)}
        ]
        for m in history:
            messages.append({"role": m.role, "content": m.content})
        messages.append({"role": "user", "content": message.text})

        # log user message
        session.add(
            MessageLog(user_id=user.id, role="user", content=message.text)
        )

        await session.commit()  # commit user + log before LLM

    waiting = await message.answer("🧠 Думаю над ответом...")

    try:
        reply_text = await ask_llm(messages)
    except Exception:
        logging.exception("LLM error")
        await waiting.edit_text(
            "Произошла ошибка при обращении к модели ИИ. "
            "Попробуй ещё раз чуть позже."
        )
        return

    async with async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.id == message.from_user.id)
        )
        user = result.scalar_one()
        session.add(
            MessageLog(user_id=user.id, role="assistant", content=reply_text)
        )
        await session.commit()

    await waiting.edit_text(reply_text)

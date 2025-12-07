from __future__ import annotations

import math

from aiogram import Router, F
from aiogram.types import Message

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import User, UserProfile
from bot.db.session import async_session_maker
from bot.services.modes import get_mode
from bot.services.llm import get_llm_client
from bot.services.profiles import build_profile_summary
from bot.services.subscriptions import get_user_tariff
from bot.services.usage import register_request
from bot.keyboards import main_menu_kb

router = Router(name="chat")


def _estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


@router.message(F.text & ~F.text.startswith("/"))
async def handle_chat(message: Message) -> None:
    session_maker = async_session_maker
    llm = get_llm_client()

    tg = message.from_user
    assert tg is not None

    async with session_maker() as session:  # type: AsyncSession
        stmt = (
            select(User, UserProfile)
            .join(UserProfile, UserProfile.user_id == User.id, isouter=True)
            .where(User.tg_id == tg.id)
        )
        res = await session.execute(stmt)
        row = res.one_or_none()

        if not row:
            await message.answer(
                "Сначала используй /start, чтобы зарегистрироваться.",
                reply_markup=main_menu_kb(),
            )
            return

        user, profile = row
        plan = await get_user_tariff(session, user.id)

        prompt_tokens = _estimate_tokens(message.text or "")

        mode = get_mode(user.current_mode)
        profile_summary = build_profile_summary(profile)

        thinking_msg = await message.answer("Думаю над ответом…")

        answer_text = await llm.ask(
            mode=mode,
            user_message=message.text,
            profile_summary=profile_summary,
        )

        completion_tokens = _estimate_tokens(answer_text)

        await register_request(
            session=session,
            user_id=user.id,
            plan=plan,
            tokens_prompt=prompt_tokens,
            tokens_completion=completion_tokens,
        )
        await session.commit()

    await thinking_msg.edit_text(answer_text)

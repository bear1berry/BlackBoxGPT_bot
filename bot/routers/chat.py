from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from bot.config import Settings
from bot.keyboards import (
    main_menu_kb,
    MAIN_BUTTON_MODES,
    MAIN_BUTTON_PROFILE,
    MAIN_BUTTON_SUBSCRIPTION,
    MAIN_BUTTON_REFERRALS,
    MODE_BUTTON_TEXTS_WITH_CHECK,
    BACK_BUTTON_TEXT,
)
from bot.texts import LIMIT_REACHED_TEXT
from db import (
    get_session_factory,
    get_last_dialog_history,
    increment_daily_counter,
    log_message,
    User,
)
from services.llm import ask_llm

router = Router(name="chat")

# Все «сервисные» тексты, которые относятся к навигации, а не к диалогу
MENU_TEXTS = {
    MAIN_BUTTON_MODES,
    MAIN_BUTTON_PROFILE,
    MAIN_BUTTON_SUBSCRIPTION,
    MAIN_BUTTON_REFERRALS,
    BACK_BUTTON_TEXT,
    *MODE_BUTTON_TEXTS_WITH_CHECK,
}


@router.message(
    ~CommandStart(),
    ~Command(commands=["set_tier"]),
)
async def handle_text_message(message: Message) -> None:
    if not message.text:
        return

    # Если это нажатие кнопки меню — навигация разрулится в другом роутере
    if message.text in MENU_TEXTS:
        return

    settings = Settings()
    session_factory = get_session_factory()

    async with session_factory() as session:
        from sqlalchemy import select
        from db import get_or_create_user

        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            # Автосоздание юзера, если /start не вызывался
            user = await get_or_create_user(
                session,
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                referred_by_code=None,
            )

        allowed, used, limit = await increment_daily_counter(user)
        await session.commit()

        if not allowed:
            await message.answer(
                LIMIT_REACHED_TEXT.format(
                    tier=user.subscription_tier.upper(),
                    used=used,
                    limit=limit,
                ),
                reply_markup=main_menu_kb(),
            )
            return

        history_pairs = await get_last_dialog_history(
            session, user_id=user.id, limit=10
        )

    # Запрос к LLM
    reply_text = await ask_llm(
        settings=settings,
        mode=user.current_mode,
        user_message=message.text,
        history=history_pairs,
    )

    # Логируем диалог
    session_factory = get_session_factory()
    async with session_factory() as session:
        await log_message(
            session,
            user_id=user.id,
            role="user",
            content=message.text,
        )
        await log_message(
            session,
            user_id=user.id,
            role="assistant",
            content=reply_text,
        )

    # После ответа возвращаем главный таскбар
    await message.answer(reply_text, reply_markup=main_menu_kb())

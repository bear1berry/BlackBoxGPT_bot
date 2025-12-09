from __future__ import annotations

import logging
from typing import Optional

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.keyboards import main_menu_kb
from bot.texts import build_main_menu_text, build_onboarding_text
from db.crud import get_or_create_user

logger = logging.getLogger(__name__)

router = Router(name="start")


def _extract_ref_code(message: Message) -> Optional[str]:
    text = message.text or ""
    parts = text.split(maxsplit=1)
    if len(parts) == 2:
        payload = parts[1].strip()
        if payload:
            return payload
    return None


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    ref_code = _extract_ref_code(message)
    user, created = await get_or_create_user(message.from_user, referred_by_code=ref_code)

    if created:
        # Красивый онбординг для новых пользователей
        onboarding = build_onboarding_text(message.from_user.first_name)
        await message.answer(onboarding, reply_markup=main_menu_kb())
    else:
        # Для старых — просто обновляем главный экран
        text = build_main_menu_text(user.current_mode)
        await message.answer(text, reply_markup=main_menu_kb())

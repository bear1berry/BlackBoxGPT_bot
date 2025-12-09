from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.config import get_settings
from bot.keyboards import main_menu_kb
from bot.texts import build_welcome_text
from db import get_session_factory, get_or_create_user

router = Router(name="start")


def _extract_ref_code(text: str | None) -> str | None:
    if not text:
        return None
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return None
    payload = parts[1].strip()
    if payload.startswith("ref_"):
        return payload
    return None


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    settings = get_settings()
    ref_code = _extract_ref_code(message.text)

    session_factory = get_session_factory()
    async with session_factory() as session:
        await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            language_code=message.from_user.language_code,
            referred_by_code=ref_code,
        )

    text = build_welcome_text(settings)
    await message.answer(text, reply_markup=main_menu_kb())

# bot/routers/start.py
from __future__ import annotations
from aiogram import Router, F
from aiogram.types import Message

from ..db import get_session
from ..keyboards import main_menu_keyboard
from ..texts import build_onboarding_text, build_main_menu_text
from ..services.referrals import get_or_create_user, apply_referral

router = Router(name="start")


@router.message(F.text == "/start")
async def cmd_start(message: Message) -> None:
    """
    /start без параметров.
    """
    async with (await get_session()) as session:
        user = await get_or_create_user(session, message.from_user)
        text = build_onboarding_text(message.from_user.first_name)
        await message.answer(text, reply_markup=main_menu_keyboard())

        # После онбординга сразу показываем главное меню
        menu_text = build_main_menu_text(user)
        await message.answer(menu_text, reply_markup=main_menu_keyboard())


@router.message(F.text.startswith("/start "))
async def cmd_start_with_ref(message: Message) -> None:
    """
    /start <ref_code>
    """
    parts = message.text.split(maxsplit=1)
    ref_code = parts[1].strip() if len(parts) > 1 else None

    async with (await get_session()) as session:
        user = await get_or_create_user(session, message.from_user)
        await apply_referral(session, user, ref_code)

        text = build_onboarding_text(message.from_user.first_name)
        await message.answer(text, reply_markup=main_menu_keyboard())

        menu_text = build_main_menu_text(user)
        await message.answer(menu_text, reply_markup=main_menu_keyboard())

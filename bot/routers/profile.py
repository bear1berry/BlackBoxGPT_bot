from __future__ import annotations

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from sqlalchemy import select

from bot.db.models import User, UserProfile
from bot.db.session import async_session_maker
from bot.keyboards import back_to_main_kb
from bot.services.profiles import get_or_create_profile

router = Router(name="profile")


class ProfileStates(StatesGroup):
    waiting_bio = State()
    waiting_goals = State()


@router.callback_query(F.data == "menu:profile")
async def cb_profile(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()

    tg = callback.from_user
    async with async_session_maker() as session:
        stmt = (
            select(User, UserProfile)
            .join(UserProfile, UserProfile.user_id == User.id, isouter=True)
            .where(User.tg_id == tg.id)
        )
        res = await session.execute(stmt)
        row = res.one_or_none()

    if not row:
        text = "Пока нет профиля. Нажми, чтобы заполнить."
        await callback.message.edit_text(text, reply_markup=back_to_main_kb())
        await callback.answer()
        return

    user, profile = row
    parts = ["👤 <b>Твой профиль</b>"]
    if profile and profile.bio:
        parts.append(f"\n<b>О себе:</b> {profile.bio}")
    if profile and profile.goals:
        parts.append(f"\n<b>Цели:</b> {profile.goals}")
    if profile and profile.interests:
        parts.append(f"\n<b>Интересы:</b> {profile.interests}")
    if profile and (profile.style_tone or profile.style_length or profile.style_emotion):
        parts.append("\n<b>Стиль ответов:</b> ")
        if profile.style_tone:
            parts.append(profile.style_tone + " ")
        if profile.style_length:
            parts.append(profile.style_length + " ")
        if profile.style_emotion:
            parts.append(profile.style_emotion + " ")

    parts.append(
        "\n\nНапиши /setbio чтобы задать краткое описание, "
        "и /setgoals чтобы прописать текущие цели."
    )

    await callback.message.edit_text("".join(parts), reply_markup=back_to_main_kb())
    await callback.answer()


@router.message(F.text == "/setbio")
async def cmd_set_bio(message: Message, state: FSMContext) -> None:
    await state.set_state(ProfileStates.waiting_bio)
    await message.answer(
        "Напиши короткое описание о себе (кто ты, чем занимаешься, что важно)."
    )


@router.message(ProfileStates.waiting_bio)
async def process_bio(message: Message, state: FSMContext) -> None:
    bio = message.text.strip()
    tg = message.from_user
    async with async_session_maker() as session:
        stmt = select(User).where(User.tg_id == tg.id)
        res = await session.execute(stmt)
        user = res.scalar_one()
        profile = await get_or_create_profile(session, user.id)
        profile.bio = bio
        await session.commit()

    await state.clear()
    await message.answer("Сохранил описание. Это поможет мне подстраиваться под тебя.")


@router.message(F.text == "/setgoals")
async def cmd_set_goals(message: Message, state: FSMContext) -> None:
    await state.set_state(ProfileStates.waiting_goals)
    await message.answer(
        "Опиши свои ключевые цели на ближайшие месяцы (работа, проекты, здоровье и т.д.)."
    )


@router.message(ProfileStates.waiting_goals)
async def process_goals(message: Message, state: FSMContext) -> None:
    goals = message.text.strip()
    tg = message.from_user
    async with async_session_maker() as session:
        stmt = select(User).where(User.tg_id == tg.id)
        res = await session.execute(stmt)
        user = res.scalar_one()
        profile = await get_or_create_profile(session, user.id)
        profile.goals = goals
        await session.commit()

    await state.clear()
    await message.answer("Цели сохранены. Теперь ответы будут чуть более прицельными.")

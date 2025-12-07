from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import User, UserProfile


async def get_or_create_user(
    session: AsyncSession,
    tg_id: int,
    username: str | None,
    first_name: str | None,
    last_name: str | None,
    language_code: str | None,
) -> User:
    stmt = select(User).where(User.tg_id == tg_id)
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()
    if user:
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.language_code = language_code
        await session.flush()
        return user

    user = User(
        tg_id=tg_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        language_code=language_code,
    )
    session.add(user)
    await session.flush()
    return user


async def get_or_create_profile(session: AsyncSession, user_id: int) -> UserProfile:
    stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    res = await session.execute(stmt)
    profile = res.scalar_one_or_none()
    if profile:
        return profile

    profile = UserProfile(user_id=user_id)
    session.add(profile)
    await session.flush()
    return profile


def build_profile_summary(profile: UserProfile | None) -> str | None:
    if profile is None:
        return None

    parts: list[str] = []
    if profile.bio:
        parts.append(f"О себе: {profile.bio}")
    if profile.goals:
        parts.append(f"Цели: {profile.goals}")
    if profile.interests:
        parts.append(f"Интересы: {profile.interests}")
    if profile.style_tone or profile.style_length or profile.style_emotion:
        style = "Стиль ответов: "
        if profile.style_tone:
            style += f"{profile.style_tone}; "
        if profile.style_length:
            style += f"{profile.style_length}; "
        if profile.style_emotion:
            style += f"{profile.style_emotion}; "
        parts.append(style.strip())

    return "\n".join(parts) if parts else None

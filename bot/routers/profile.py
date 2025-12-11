from datetime import datetime, timezone, date

from aiogram import Router, F
from aiogram.types import Message

from ..keyboards import main_menu_keyboard
from ..services.storage import get_user_by_telegram_id
from ..db import db

router = Router(name="profile")


@router.message(F.text == "👤 Профиль")
async def show_profile(message: Message) -> None:
    tg_id = message.from_user.id
    user = await get_user_by_telegram_id(tg_id)
    if not user:
        await message.answer(
            "Не нашёл твой профиль, попробуй ещё раз через /start.",
            reply_markup=main_menu_keyboard(),
        )
        return

    now = datetime.now(timezone.utc)
    sub_expires = user["subscription_expires_at"]
    if sub_expires and sub_expires > now:
        tariff = "Premium"
        until = sub_expires.astimezone().strftime("%d.%m.%Y")
    else:
        tariff = "Free"
        until = "—"

    stats = await db.fetchrow(
        "SELECT messages_count, tokens_used FROM usage_stats WHERE user_id=$1 AND date=$2",
        user["id"],
        date.today(),
    )
    messages_today = stats["messages_count"] if stats else 0
    tokens_today = stats["tokens_used"] if stats else 0

    me = await message.bot.get_me()
    referral_code = user["referral_code"]
    ref_link = f"https://t.me/{me.username}?start=ref_{referral_code}"

    text = (
        "👤 **Профиль**\n\n"
        f"ID: `{user['telegram_id']}`\n"
        f"Тариф: **{tariff}** (до: {until})\n"
        f"Сегодня запросов: **{messages_today}**\n"
        f"Оценка использованных токенов: **{tokens_today}**\n\n"
        "👥 **Реферальная программа**\n"
        f"Твой реф-код: `{referral_code}`\n"
        f"Твоя ссылка:\n{ref_link}\n\n"
        "Отправь ссылку друзьям и получай бонусы, когда они активируются. "
        "Условия бонусов можно будет настроить отдельно."
    )
    await message.answer(text, reply_markup=main_menu_keyboard())

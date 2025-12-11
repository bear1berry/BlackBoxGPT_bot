from aiogram import Router, F
from aiogram.types import Message

from ..keyboards import referrals_keyboard
from ..services.storage import get_user_by_telegram_id
from ..db import db

router = Router(name="referrals")


@router.message(F.text == "👥 Рефералы")
async def show_referrals(message: Message) -> None:
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Не нашёл твой профиль, отправь /start.", reply_markup=referrals_keyboard())
        return

    me = await message.bot.get_me()
    referral_code = user["referral_code"]
    ref_link = f"https://t.me/{me.username}?start=ref_{referral_code}"

    total_invited = await db.fetchval(
        "SELECT COUNT(*) FROM referrals WHERE referrer_id=$1",
        user["id"],
    )
    premium_invited = await db.fetchval(
        "SELECT COUNT(*) FROM users WHERE referrer_id=$1 AND is_premium = TRUE",
        user["id"],
    )

    text = (
        "👥 **Реферальная программа**\n\n"
        f"Твой реф-код: `{referral_code}`\n"
        f"Твоя ссылка для приглашений:\n{ref_link}\n\n"
        f"Всего приглашено: **{total_invited or 0}**\n"
        f"Из них с Premium: **{premium_invited or 0}**\n\n"
        "🔹 За друзей можно начислять бонусы: дни подписки, доп. лимиты, скидки.\n"
        "Логику бонусов легко донастроить в коде."
    )
    await message.answer(text, reply_markup=referrals_keyboard())

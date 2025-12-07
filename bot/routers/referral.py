from __future__ import annotations

from aiogram import Router, F
from aiogram.types import CallbackQuery

from sqlalchemy import select

from bot.db.models import User
from bot.db.session import async_session_maker
from bot.keyboards import referrals_menu_kb
from bot.services.referrals import build_ref_code, get_referral_stats

router = Router(name="referrals")


@router.callback_query(F.data == "menu:referrals")
async def cb_referrals(callback: CallbackQuery) -> None:
    tg = callback.from_user
    async with async_session_maker() as session:
        stmt = select(User).where(User.tg_id == tg.id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            await callback.message.edit_text(
                "Сначала используй /start, чтобы зарегистрироваться.",
            )
            await callback.answer()
            return

        total_invited, total_rewarded = await get_referral_stats(session, user)

    ref_code = build_ref_code(tg.id)
    bot_username = (await callback.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={ref_code}"

    text = (
        "👥 <b>Реферальная программа</b>\n\n"
        "Поделись ссылкой, чтобы друзья подключались к BlackBox GPT.\n"
        "За активных приглашённых в будущем будут бонусы: дни подписки, лимиты и т.д.\n\n"
        f"<b>Твоя ссылка:</b>\n{ref_link}\n\n"
        f"Приглашено всего: <b>{total_invited}</b>\n"
        f"С выданной наградой: <b>{total_rewarded}</b>\n\n"
        "Реальные бонусы будут подключены на этапе монетизации (Фаза 3)."
    )

    await callback.message.edit_text(text, reply_markup=referrals_menu_kb(ref_link))
    await callback.answer()

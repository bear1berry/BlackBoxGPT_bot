from __future__ import annotations

import time
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Router
from aiogram.types import Message

from bot.keyboards import (
    BTN_BACK,
    BTN_CHECKIN_TOGGLE,
    BTN_INVITE,
    BTN_MODE_PRO,
    BTN_MODE_UNIVERSAL,
    BTN_MODES,
    BTN_PROFILE,
    BTN_REFERRALS,
    BTN_RENEW,
    BTN_SUBSCRIPTION,
    BTN_SUB_1M,
    BTN_SUB_3M,
    BTN_SUB_12M,
    kb_back_only,
    kb_main,
    kb_modes,
    kb_profile,
    kb_subscription,
)
from bot import texts
from services import users as users_repo
from services import referrals as refs_repo
from services import limits as limits_service
from services import payments as payments_service


router = Router()


def _fmt_date(ts: int, tz: str) -> str:
    if ts <= 0:
        return "—"
    dt = datetime.fromtimestamp(ts, tz=ZoneInfo(tz))
    return dt.strftime("%Y-%m-%d")


@router.message(lambda m: m.text == BTN_BACK)
async def back_to_main(message: Message) -> None:
    await message.answer("⚙️ Меню", reply_markup=kb_main())


@router.message(lambda m: m.text == BTN_MODES)
async def open_modes(message: Message) -> None:
    await message.answer(texts.MODE_MENU_TEXT, reply_markup=kb_modes())


@router.message(lambda m: m.text == BTN_PROFILE)
async def open_profile(message: Message) -> None:

    u = await limits_service.ensure_plan_fresh(db, message.from_user.id)
    ref_link = f"https://t.me/{settings.bot_username}?start={u.ref_code}"

    daily_limit = settings.premium_daily_limit if u.is_premium else settings.premium_daily_limit
    trial_left = max(0, settings.basic_trial_limit - u.trial_used)
    plan = "Premium" if u.is_premium else "Базовый"
    mode = "Профессиональный" if u.mode == "pro" else "Универсальный"
    checkin = "Вкл" if u.checkin_enabled else "Выкл"

    txt = texts.PROFILE_TEMPLATE.format(
        plan=plan,
        premium_until=_fmt_date(u.premium_until, settings.timezone),
        used_today=u.daily_used,
        daily_limit=daily_limit if u.is_premium else "—",
        trial_left=trial_left,
        mode=mode,
        checkin=checkin,
        ref_link=ref_link,
    )

    await message.answer(txt, reply_markup=kb_profile())


@router.message(lambda m: m.text == BTN_REFERRALS)
async def open_referrals(message: Message) -> None:

    u = await users_repo.get_user(db, message.from_user.id)
    if not u:
        await message.answer(texts.GENERIC_ERROR, reply_markup=kb_main())
        return

    stats = await refs_repo.get_ref_stats(db, message.from_user.id)
    ref_link = f"https://t.me/{settings.bot_username}?start={u.ref_code}"

    txt = texts.REFERRALS_TEMPLATE.format(ref_link=ref_link, total=stats.total, premium=stats.premium)
    await message.answer(txt, reply_markup=kb_back_only())


@router.message(lambda m: m.text == BTN_SUBSCRIPTION)
async def open_subscription(message: Message) -> None:
    settings = message.bot["settings"]
    txt = texts.SUBSCRIPTION_MENU_TEXT.format(
        price_1m=f"{settings.price_1m:.2f}",
        price_3m=f"{settings.price_3m:.2f}",
        price_12m=f"{settings.price_12m:.2f}",
    )
    await message.answer(txt, reply_markup=kb_subscription())


@router.message(lambda m: m.text in (BTN_SUB_1M, BTN_SUB_3M, BTN_SUB_12M))
async def create_invoice(message: Message) -> None:

    months = 1 if message.text == BTN_SUB_1M else 3 if message.text == BTN_SUB_3M else 12
    amount = settings.price_1m if months == 1 else settings.price_3m if months == 3 else settings.price_12m

    inv = await payments_service.create_subscription_invoice(
        db,
        cryptopay,
        user_id=message.from_user.id,
        months=months,
        amount_usdt=float(amount),
    )

    pay_url = inv.bot_invoice_url or ""
    await message.answer(texts.PAYMENT_CREATED + f"\n\n🔗 {pay_url}", reply_markup=kb_subscription())


@router.message(lambda m: m.text == BTN_MODE_UNIVERSAL)
async def set_universal(message: Message) -> None:
    db = message.bot["db"]
    await users_repo.set_mode(db, message.from_user.id, "universal")
    await message.answer("✅ Режим: <b>Универсальный</b>", reply_markup=kb_main())


@router.message(lambda m: m.text == BTN_MODE_PRO)
async def set_pro(message: Message) -> None:
    db = message.bot["db"]
    await users_repo.set_mode(db, message.from_user.id, "pro")
    await message.answer("✅ Режим: <b>Профессиональный</b>", reply_markup=kb_main())


@router.message(lambda m: m.text == BTN_RENEW)
async def renew(message: Message) -> None:
    await open_subscription(message)


@router.message(lambda m: m.text == BTN_INVITE)
async def invite(message: Message) -> None:
    await open_referrals(message)


@router.message(lambda m: m.text == BTN_CHECKIN_TOGGLE)
async def toggle_checkin(message: Message) -> None:
    db = message.bot["db"]
    new_val = await users_repo.toggle_checkin(db, message.from_user.id)
    status = "Вкл ✅" if new_val else "Выкл ❌"
    await message.answer(f"🫂 Ежедневный чек-ин: <b>{status}</b>", reply_markup=kb_profile())

from __future__ import annotations

from datetime import datetime

from aiogram import Router, F
from aiogram.types import CallbackQuery

from sqlalchemy import select

from bot.db.models import Subscription, User
from bot.db.session import async_session_maker
from bot.keyboards import subscription_menu_kb, back_to_main_kb
from bot.services.tariffs import resolve_user_plan

router = Router(name="subscription")


@router.callback_query(F.data == "menu:subscription")
async def cb_subscription_menu(callback: CallbackQuery) -> None:
    tg = callback.from_user
    async with async_session_maker() as session:
        stmt = select(User).where(User.tg_id == tg.id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        sub_stmt = (
            select(Subscription)
            .where(Subscription.user_id == user.id)
            .order_by(Subscription.started_at.desc())
        )
        sub_res = await session.execute(sub_stmt)
        last_sub = sub_res.scalars().first()

    if user is None:
        await callback.message.edit_text(
            "Для начала используй /start.",
            reply_markup=back_to_main_kb(),
        )
        await callback.answer()
        return

    plan_code = last_sub.plan_code if last_sub else "free"
    plan = resolve_user_plan(plan_code)

    info_lines = [
        "💎 <b>Твоя подписка</b>",
        "\nТекущий план: <b>{}</b>".format(plan.title),
        "\nЛимит запросов в день: <b>{}</b>".format(plan.daily_requests_limit),
    ]

    if last_sub and last_sub.expires_at:
        info_lines.append(
            "\nОплачено до: <b>{}</b>".format(last_sub.expires_at.strftime("%d.%m.%Y"))
        )
    elif plan_code == "free":
        info_lines.append("\nУ тебя сейчас бесплатный план.")

    info_lines.append("\n\nВыбери вариант подписки:")

    await callback.message.edit_text(
        "".join(info_lines),
        reply_markup=subscription_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sub:plan:"))
async def cb_subscription_plan(callback: CallbackQuery) -> None:
    plan_key = callback.data.split(":", 2)[2]

    duration_map = {
        "1m": 30,
        "3m": 90,
        "12m": 365,
    }
    duration = duration_map.get(plan_key, 30)

    until = datetime.utcnow().strftime("%d.%m.%Y")
    await callback.message.edit_text(
        "Скоро здесь появится оплата через крипту и банковские карты.\n\n"
        f"План: {plan_key}, длительность ~{duration} дней.\n"
        "На уровне ядра всё уже готово: БД, подписки, лимиты.\n\n"
        "Пока можешь продолжать тестировать функционал Free-плана.",
        reply_markup=back_to_main_kb(),
    )
    await callback.answer("Оплата пока не подключена (MVP ядро).")

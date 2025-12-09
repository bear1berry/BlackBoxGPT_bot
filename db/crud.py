from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from aiogram.types import User as TgUser
from sqlalchemy import select

from bot.config import settings
from db.models import DialogMessage, Payment, User
from db.session import async_session


# ---------- USERS & REFERRALS ----------


async def get_or_create_user(
    tg_user: TgUser,
    referred_by_code: Optional[str] = None,
) -> Tuple[User, bool]:
    """Get existing user or create new.

    Returns (user, created_flag).
    """
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.tg_id == tg_user.id)
        )
        user = result.scalar_one_or_none()

        if user:
            # Normalize subscription on every touch
            user = await _normalize_user_subscription(user, session)
            return user, False

        user = User(
            tg_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
            language_code=tg_user.language_code,
            current_mode="universal",
            subscription_tier="free",
        )
        session.add(user)
        await session.flush()  # get user.id

        # Ref code = tg_id as string for simplicity
        user.ref_code = str(tg_user.id)

        # Handle referral if provided
        if referred_by_code:
            inviter_result = await session.execute(
                select(User).where(User.ref_code == referred_by_code)
            )
            inviter = inviter_result.scalar_one_or_none()
            if inviter and inviter.id != user.id:
                user.referred_by_code = referred_by_code
                inviter.referrals_count = (inviter.referrals_count or 0) + 1

                # Reward inviter with extra premium days
                reward_days = settings.referral_reward_days
                now = datetime.now(timezone.utc)
                if (
                    inviter.subscription_tier == "premium"
                    and inviter.subscription_expires_at
                    and inviter.subscription_expires_at > now
                ):
                    inviter.subscription_expires_at = (
                        inviter.subscription_expires_at
                        + timedelta(days=reward_days)
                    )
                else:
                    inviter.subscription_tier = "premium"
                    inviter.subscription_expires_at = now + timedelta(
                        days=reward_days
                    )

        await session.commit()
        await session.refresh(user)
        return user, True


async def get_user_by_tg_id(tg_id: int) -> Optional[User]:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
        if not user:
            return None
        return await _normalize_user_subscription(user, session)


async def update_user_mode(tg_id: int, mode: str) -> Optional[User]:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
        if not user:
            return None
        user.current_mode = mode
        await session.commit()
        await session.refresh(user)
        return user


async def _normalize_user_subscription(
    user: User,
    session,
) -> User:
    """Downgrade to free if premium expired."""
    if user.subscription_tier != "free" and user.subscription_expires_at:
        now = datetime.now(timezone.utc)
        if user.subscription_expires_at <= now:
            user.subscription_tier = "free"
            user.subscription_expires_at = None
            await session.commit()
            await session.refresh(user)
    return user


# ---------- DIALOG HISTORY ----------


async def add_dialog_message(user_id: int, role: str, content: str) -> None:
    async with async_session() as session:
        msg = DialogMessage(user_id=user_id, role=role, content=content)
        session.add(msg)
        await session.commit()


async def get_last_dialog_messages(
    user_id: int,
    limit: int = 10,
) -> List[DialogMessage]:
    async with async_session() as session:
        result = await session.execute(
            select(DialogMessage)
            .where(DialogMessage.user_id == user_id)
            .order_by(DialogMessage.id.desc())
            .limit(limit)
        )
        rows = list(result.scalars().all())
        rows.reverse()
        return rows


# ---------- PAYMENTS & SUBSCRIPTIONS ----------


PLAN_CONFIG = {
    "1m": {"days": 30, "price_attr": "subscription_price_1m"},
    "3m": {"days": 90, "price_attr": "subscription_price_3m"},
    "12m": {"days": 365, "price_attr": "subscription_price_12m"},
}


def get_plan_config(plan_code: str) -> dict:
    if plan_code not in PLAN_CONFIG:
        raise ValueError(f"Unknown plan code: {plan_code}")
    cfg = PLAN_CONFIG[plan_code]
    days = cfg["days"]
    price = getattr(settings, cfg["price_attr"])
    return {"days": days, "price": price}


async def create_payment(
    user_id: int,
    plan_code: str,
    invoice_id: int,
    pay_url: str,
) -> Payment:
    cfg = get_plan_config(plan_code)
    amount_usd = cfg["price"]

    async with async_session() as session:
        payment = Payment(
            user_id=user_id,
            plan_code=plan_code,
            amount_usd=amount_usd,
            invoice_id=invoice_id,
            pay_url=pay_url,
            status="pending",
        )
        session.add(payment)
        await session.commit()
        await session.refresh(payment)
        return payment


async def get_payment_by_invoice_id(invoice_id: int) -> Optional[Payment]:
    async with async_session() as session:
        result = await session.execute(
            select(Payment).where(Payment.invoice_id == invoice_id)
        )
        return result.scalar_one_or_none()


async def get_pending_payments(user_id: int) -> List[Payment]:
    async with async_session() as session:
        result = await session.execute(
            select(Payment)
            .where(Payment.user_id == user_id, Payment.status == "pending")
            .order_by(Payment.id.desc())
        )
        return list(result.scalars().all())


async def mark_payment_paid_and_extend_subscription(
    payment_id: int,
) -> User:
    async with async_session() as session:
        payment = await session.get(Payment, payment_id)
        if not payment:
            raise RuntimeError("Payment not found")

        user = await session.get(User, payment.user_id)
        if not user:
            raise RuntimeError("User not found for payment")

        cfg = get_plan_config(payment.plan_code)
        subscription_days = cfg["days"]

        now = datetime.now(timezone.utc)
        user.subscription_tier = "premium"
        if user.subscription_expires_at and user.subscription_expires_at > now:
            user.subscription_expires_at = user.subscription_expires_at + timedelta(
                days=subscription_days
            )
        else:
            user.subscription_expires_at = now + timedelta(days=subscription_days)

        payment.status = "paid"
        payment.expires_at = user.subscription_expires_at

        await session.commit()
        await session.refresh(user)
        return user

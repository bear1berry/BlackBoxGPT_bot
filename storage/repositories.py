from __future__ import annotations

import datetime as dt
import logging
import secrets
from typing import Optional, Sequence

from aiogram.types import User as TgUser
from sqlalchemy import select, func, update
from sqlalchemy.exc import SQLAlchemyError

from .db import async_session_factory
from .models import (
    User,
    Message,
    Payment,
    Referral,
    ModeEnum,
    SubscriptionEnum,
    MessageRoleEnum,
    PaymentProviderEnum,
    PaymentStatusEnum,
)

logger = logging.getLogger(__name__)


class UsersRepository:
    async def get_or_create_from_telegram(
        self,
        tg_user: TgUser,
        referred_by_code: Optional[str] = None,
    ) -> User:
        async with async_session_factory() as session:
            try:
                result = await session.execute(
                    select(User).where(User.telegram_id == tg_user.id)
                )
                user = result.scalar_one_or_none()
                if user:
                    # Обновляем базовые поля
                    user.username = tg_user.username
                    user.first_name = tg_user.first_name
                    user.last_name = tg_user.last_name
                    await session.commit()
                    return user

                user = User(
                    telegram_id=tg_user.id,
                    username=tg_user.username,
                    first_name=tg_user.first_name,
                    last_name=tg_user.last_name,
                    created_at=dt.datetime.utcnow(),
                    current_mode=ModeEnum.UNIVERSAL,
                    subscription_type=SubscriptionEnum.FREE,
                )

                # Генерация реф-кода
                user.referral_code = await self._generate_referral_code(session)

                # Привязка реферера
                if referred_by_code:
                    ref_user = await self.get_by_referral_code(session, referred_by_code)
                    if ref_user:
                        user.referred_by = ref_user.id

                session.add(user)
                await session.commit()
                await session.refresh(user)

                # Записываем явный referral, если есть
                if user.referred_by:
                    ref = Referral(user_id=user.referred_by, referred_user_id=user.id)
                    session.add(ref)
                    await session.commit()

                return user
            except SQLAlchemyError:
                logger.exception("Failed to get_or_create user")
                await session.rollback()
                raise

    async def _generate_referral_code(self, session) -> str:
        for _ in range(10):
            code = secrets.token_urlsafe(6)
            result = await session.execute(
                select(User).where(User.referral_code == code)
            )
            if result.scalar_one_or_none() is None:
                return code
        # fallback
        return secrets.token_urlsafe(8)

    async def get_by_referral_code(self, session, code: str) -> Optional[User]:
        result = await session.execute(select(User).where(User.referral_code == code))
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        async with async_session_factory() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none()

    async def update_mode(self, telegram_id: int, mode: ModeEnum) -> None:
        async with async_session_factory() as session:
            await session.execute(
                update(User)
                .where(User.telegram_id == telegram_id)
                .values(current_mode=mode)
            )
            await session.commit()

    async def update_bio(self, telegram_id: int, bio: str) -> None:
        async with async_session_factory() as session:
            await session.execute(
                update(User)
                .where(User.telegram_id == telegram_id)
                .values(profile_bio=bio)
            )
            await session.commit()

    async def toggle_motivation(self, telegram_id: int) -> bool:
        async with async_session_factory() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                return False
            user.wants_motivation = not user.wants_motivation
            await session.commit()
            return user.wants_motivation

    async def toggle_science(self, telegram_id: int) -> bool:
        async with async_session_factory() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                return False
            user.wants_science_facts = not user.wants_science_facts
            await session.commit()
            return user.wants_science_facts

    async def set_subscription(
        self,
        user_id: int,
        subscription_type: SubscriptionEnum,
        months: int,
    ) -> None:
        async with async_session_factory() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                return
            now = dt.datetime.utcnow()
            if user.subscription_until and user.subscription_until > now:
                base = user.subscription_until
            else:
                base = now
            user.subscription_type = subscription_type
            user.subscription_until = base + dt.timedelta(days=30 * months)
            await session.commit()

    async def get_ref_stats(self, user_id: int) -> tuple[int, int]:
        """
        Возвращает (кол-во рефералов, бонусные дни).
        Бонусные дни считаем как 7 дней за каждый оплаченный реферал.
        """
        async with async_session_factory() as session:
            # Количество приглашённых пользователей
            result = await session.execute(
                select(func.count(Referral.id)).where(Referral.user_id == user_id)
            )
            ref_count = result.scalar_one() or 0

            # Количество оплаченных подписок у рефералов
            result2 = await session.execute(
                select(func.count(Payment.id))
                .join(Referral, Payment.user_id == Referral.referred_user_id)
                .where(
                    Referral.user_id == user_id,
                    Payment.status == PaymentStatusEnum.PAID,
                )
            )
            paid_count = result2.scalar_one() or 0
            bonus_days = paid_count * 7
            return ref_count, bonus_days
        

class MessagesRepository:
    async def add_message(
        self,
        user_id: int,
        role: MessageRoleEnum,
        content: str,
    ) -> None:
        async with async_session_factory() as session:
            msg = Message(
                user_id=user_id,
                role=role,
                content=content,
                created_at=dt.datetime.utcnow(),
            )
            session.add(msg)
            await session.commit()

    async def get_last_messages(
        self,
        user_id: int,
        limit: int = 10,
    ) -> Sequence[Message]:
        async with async_session_factory() as session:
            result = await session.execute(
                select(Message)
                .where(Message.user_id == user_id)
                .order_by(Message.created_at.desc())
                .limit(limit)
            )
            msgs = list(result.scalars().all())
            return list(reversed(msgs))

    async def clear_user_history(self, user_id: int) -> None:
        async with async_session_factory() as session:
            await session.execute(
                Message.__table__.delete().where(Message.user_id == user_id)
            )
            await session.commit()


class PaymentsRepository:
    async def create_payment(
        self,
        user_id: int,
        provider: PaymentProviderEnum,
        plan: str,
        amount: str,
        currency: str,
        invoice_id: str,
    ) -> Payment:
        async with async_session_factory() as session:
            payment = Payment(
                user_id=user_id,
                provider=provider,
                plan=plan,
                amount=amount,
                currency=currency,
                invoice_id=invoice_id,
                status=PaymentStatusEnum.PENDING,
            )
            session.add(payment)
            await session.commit()
            await session.refresh(payment)
            return payment

    async def update_status(
        self,
        invoice_id: str,
        status: PaymentStatusEnum,
    ) -> None:
        async with async_session_factory() as session:
            await session.execute(
                update(Payment)
                .where(Payment.invoice_id == invoice_id)
                .values(status=status)
            )
            await session.commit()

    async def get_pending(self) -> list[Payment]:
        async with async_session_factory() as session:
            result = await session.execute(
                select(Payment).where(
                    Payment.status == PaymentStatusEnum.PENDING,
                    Payment.provider == PaymentProviderEnum.CRYPTO,
                )
            )
            return list(result.scalars().all())

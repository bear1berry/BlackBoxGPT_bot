# bot/models.py
from datetime import datetime, timedelta, timezone
import secrets
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True, index=True, nullable=False)

    username = Column(String(64), nullable=True)
    first_name = Column(String(64), nullable=True)
    last_name = Column(String(64), nullable=True)
    language_code = Column(String(8), nullable=True)

    current_mode = Column(String(32), default="universal", nullable=False)

    is_premium = Column(Boolean, default=False, nullable=False)
    premium_until = Column(DateTime(timezone=True), nullable=True)

    ref_code = Column(String(32), unique=True, index=True, nullable=False)
    referred_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=now_utc,
        onupdate=now_utc,
        nullable=False,
    )

    referrals = relationship(
        "Referral", back_populates="referrer", foreign_keys="Referral.referrer_id"
    )

    def ensure_ref_code(self) -> None:
        if not self.ref_code:
            self.ref_code = secrets.token_urlsafe(8)


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    referral_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)

    referrer = relationship("User", foreign_keys=[referrer_id])
    referral_user = relationship("User", foreign_keys=[referral_user_id])


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    plan_code = Column(String(16), nullable=False)  # "1m", "3m", "12m"
    invoice_id = Column(Integer, nullable=False)
    status = Column(String(32), default="pending", nullable=False)

    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")


def calculate_expiry(months: int) -> datetime:
    return now_utc() + timedelta(days=30 * months)

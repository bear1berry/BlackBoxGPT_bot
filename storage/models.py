from __future__ import annotations

import datetime as dt
from enum import Enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class ModeEnum(str, Enum):
    UNIVERSAL = "universal"
    MEDICINE = "medicine"
    MENTOR = "mentor"
    BUSINESS = "business"
    CREATIVE = "creative"


class SubscriptionEnum(str, Enum):
    FREE = "free"
    PRO = "pro"


class MessageRoleEnum(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class PaymentStatusEnum(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELED = "canceled"


class PaymentProviderEnum(str, Enum):
    CRYPTO = "crypto"
    CARD = "card"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    current_mode = Column(SAEnum(ModeEnum), default=ModeEnum.UNIVERSAL, nullable=False)
    profile_bio = Column(Text, default="", nullable=False)

    subscription_type = Column(
        SAEnum(SubscriptionEnum),
        default=SubscriptionEnum.FREE,
        nullable=False,
    )
    subscription_until = Column(DateTime, nullable=True)

    referral_code = Column(String(64), unique=True, index=True, nullable=True)
    referred_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    wants_motivation = Column(Boolean, default=False, nullable=False)
    wants_science_facts = Column(Boolean, default=False, nullable=False)

    referred_users = relationship("User", remote_side=[id])
    messages = relationship("Message", back_populates="user")
    payments = relationship("Payment", back_populates="user")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(SAEnum(MessageRoleEnum), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="messages")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(SAEnum(PaymentProviderEnum), nullable=False)
    plan = Column(String(32), nullable=False)
    status = Column(SAEnum(PaymentStatusEnum), default=PaymentStatusEnum.PENDING)
    amount = Column(String(32), nullable=True)
    currency = Column(String(16), nullable=True)
    invoice_id = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=dt.datetime.utcnow,
        onupdate=dt.datetime.utcnow,
        nullable=False,
    )

    user = relationship("User", back_populates="payments")


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    referred_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

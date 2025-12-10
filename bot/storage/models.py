from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserMode(str, enum.Enum):
    UNIVERSAL = "универсальный"
    MEDICINE = "медицина"
    MENTOR = "наставник"
    BUSINESS = "бизнес"
    CREATIVE = "креатив"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)

    mode: Mapped[UserMode] = mapped_column(
        Enum(UserMode),
        default=UserMode.UNIVERSAL,
        nullable=False,
    )

    subscription_tier: Mapped[str] = mapped_column(
        String(32),
        default="free",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

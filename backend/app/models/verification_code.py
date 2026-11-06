import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class VerificationPurpose(str, enum.Enum):
    REGISTER = "register"
    RESET_PASSWORD = "reset_password"


class VerificationCode(Base, TimestampMixin):
    __tablename__ = "verification_codes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(String(20), index=True)
    code: Mapped[str] = mapped_column(String(10))
    out_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    purpose: Mapped[VerificationPurpose] = mapped_column(Enum(VerificationPurpose))
    role: Mapped[str | None] = mapped_column(String(20), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_used: Mapped[bool] = mapped_column(default=False)

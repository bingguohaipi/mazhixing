from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class AiDailyUsage(Base):
    __tablename__ = "ai_daily_usage"
    __table_args__ = (UniqueConstraint("user_id", "usage_date", name="uq_ai_daily_usage"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    usage_date: Mapped[date] = mapped_column(Date, index=True)
    count: Mapped[int] = mapped_column(Integer, default=0)

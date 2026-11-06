from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class EventLog(Base, TimestampMixin):
    __tablename__ = "event_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    user_role: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    event_name: Mapped[str] = mapped_column(String(64), index=True)
    page: Mapped[str | None] = mapped_column(String(128), nullable=True)
    module: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import AuditMixin, Base, TimestampMixin


class KnowledgePoint(Base, TimestampMixin, AuditMixin):
    __tablename__ = "knowledge_points"
    __table_args__ = (UniqueConstraint("name", name="uq_knowledge_points_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), index=True)
    summary: Mapped[str] = mapped_column(String(512), default="")
    content_markdown: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=100)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

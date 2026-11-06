from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditMixin, Base, TimestampMixin


class Notice(Base, TimestampMixin, AuditMixin):
    __tablename__ = "notices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)

    class_links: Mapped[list["NoticeClass"]] = relationship("NoticeClass", back_populates="notice")


class NoticeClass(Base):
    __tablename__ = "notice_classes"
    __table_args__ = (UniqueConstraint("notice_id", "class_id", name="uq_notice_class"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    notice_id: Mapped[int] = mapped_column(ForeignKey("notices.id"), index=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), index=True)

    notice: Mapped["Notice"] = relationship("Notice", back_populates="class_links")


class NoticeRead(Base):
    __tablename__ = "notice_reads"
    __table_args__ = (UniqueConstraint("notice_id", "user_id", name="uq_notice_read_user"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    notice_id: Mapped[int] = mapped_column(ForeignKey("notices.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ParentStudentBinding(Base, TimestampMixin):
    __tablename__ = "parent_student_bindings"
    __table_args__ = (UniqueConstraint("parent_id", "student_id", name="uq_parent_student"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)


class OperationLog(Base, TimestampMixin):
    __tablename__ = "operation_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(64))
    resource: Mapped[str | None] = mapped_column(String(128), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)

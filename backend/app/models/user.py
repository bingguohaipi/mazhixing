import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import AuditMixin, Base, TimestampMixin
from app.models.enum_utils import enum_values


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    PARENT = "parent"


class User(Base, TimestampMixin, AuditMixin):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("account", "role", name="uq_users_account_role"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account: Mapped[str] = mapped_column(String(64), index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, values_callable=enum_values),
        index=True,
    )
    display_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    nickname: Mapped[str | None] = mapped_column(String(32), nullable=True)
    avatar_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    student_no: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    created_by_teacher_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    token_version: Mapped[int] = mapped_column(default=0)
    arena_ranking_opt_out: Mapped[bool] = mapped_column(default=False)
    arena_agreed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

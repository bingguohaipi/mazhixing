"""Arena (擂台) sessions, results, and user notifications."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.models.enum_utils import enum_values
from app.models.submission import SubmissionStatus


class ArenaSessionStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    EXITED = "exited"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ArenaReviewStatus(str, enum.Enum):
    NONE = "none"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ArenaSession(Base, TimestampMixin):
    __tablename__ = "arena_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    language: Mapped[str] = mapped_column(String(16))
    status: Mapped[ArenaSessionStatus] = mapped_column(
        Enum(ArenaSessionStatus, values_callable=enum_values),
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    exited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submission_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)


class ArenaSessionMetrics(Base, TimestampMixin):
    __tablename__ = "arena_session_metrics"

    arena_session_id: Mapped[int] = mapped_column(
        ForeignKey("arena_sessions.id"),
        primary_key=True,
    )
    first_keystroke_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paste_count: Mapped[int] = mapped_column(Integer, default=0)
    paste_char_count: Mapped[int] = mapped_column(Integer, default=0)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_flags: Mapped[str | None] = mapped_column(Text, nullable=True)
    similarity_max: Mapped[float | None] = mapped_column(Float, nullable=True)


class ArenaResult(Base, TimestampMixin):
    __tablename__ = "arena_results"
    __table_args__ = (UniqueConstraint("arena_session_id", name="uq_arena_result_session"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    arena_session_id: Mapped[int] = mapped_column(ForeignKey("arena_sessions.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    language: Mapped[str] = mapped_column(String(16), index=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), unique=True)
    judge_status: Mapped[SubmissionStatus] = mapped_column(Enum(SubmissionStatus))
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    arena_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_status: Mapped[ArenaReviewStatus] = mapped_column(
        Enum(ArenaReviewStatus, values_callable=enum_values),
        default=ArenaReviewStatus.NONE,
        index=True,
    )
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reject_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    ranked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    achieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class UserNotification(Base, TimestampMixin):
    __tablename__ = "user_notifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    event_key: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(100))
    body: Mapped[str] = mapped_column(Text)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

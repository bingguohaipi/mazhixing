from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class LeaderboardSnapshot(Base, TimestampMixin):
    """Daily frozen class leaderboard row (refreshed at midnight)."""

    __tablename__ = "leaderboard_snapshots"
    __table_args__ = (
        UniqueConstraint("class_id", "snapshot_date", "student_id", name="uq_lb_snapshot_student"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    rank: Mapped[int] = mapped_column(Integer)
    display_name: Mapped[str] = mapped_column(String(64))
    completed_problems: Mapped[int] = mapped_column(Integer, default=0)
    accuracy_rate: Mapped[float] = mapped_column(Float, default=0.0)
    accuracy_score: Mapped[float] = mapped_column(Float, default=0.0)
    time_score: Mapped[float] = mapped_column(Float, default=0.0)
    total_score: Mapped[float] = mapped_column(Float, default=0.0)
    avg_runtime_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    refreshed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

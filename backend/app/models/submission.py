import enum
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class SubmissionStatus(str, enum.Enum):
    PENDING = "PENDING"
    AC = "AC"
    WA = "WA"
    CE = "CE"
    TLE = "TLE"
    RE = "RE"


class Submission(Base, TimestampMixin):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    homework_id: Mapped[int | None] = mapped_column(ForeignKey("homeworks.id"), nullable=True, index=True)
    arena_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("arena_sessions.id"),
        nullable=True,
        index=True,
    )
    code: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(16))
    status: Mapped[SubmissionStatus] = mapped_column(Enum(SubmissionStatus), index=True)
    runtime_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    memory_kb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_late: Mapped[bool] = mapped_column(default=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    compile_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)

    case_results: Mapped[list["SubmissionCaseResult"]] = relationship(
        "SubmissionCaseResult",
        back_populates="submission",
        cascade="all, delete-orphan",
    )


class SubmissionCaseResult(Base):
    __tablename__ = "submission_case_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), index=True)
    test_case_id: Mapped[int | None] = mapped_column(ForeignKey("test_cases.id"), nullable=True)
    case_index: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[SubmissionStatus] = mapped_column(Enum(SubmissionStatus))
    actual_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    runtime_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    submission: Mapped["Submission"] = relationship("Submission", back_populates="case_results")

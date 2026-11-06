from datetime import datetime

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class WrongBookDismissal(Base, TimestampMixin):
    """Student manually cleared a problem from wrong-book view."""

    __tablename__ = "wrong_book_dismissals"
    __table_args__ = (UniqueConstraint("student_id", "problem_id", name="uq_wrong_book_dismiss"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    dismissed_at: Mapped[datetime] = mapped_column(index=True)

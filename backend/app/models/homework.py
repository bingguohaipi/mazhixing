from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditMixin, Base, TimestampMixin


class Homework(Base, TimestampMixin, AuditMixin):
    __tablename__ = "homeworks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    allow_late_submission: Mapped[bool] = mapped_column(Boolean, default=False)
    content_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    class_links: Mapped[list["HomeworkClass"]] = relationship("HomeworkClass", back_populates="homework")
    problem_links: Mapped[list["HomeworkProblem"]] = relationship("HomeworkProblem", back_populates="homework")
    student_links: Mapped[list["HomeworkStudent"]] = relationship("HomeworkStudent", back_populates="homework")


class HomeworkClass(Base):
    __tablename__ = "homework_classes"
    __table_args__ = (UniqueConstraint("homework_id", "class_id", name="uq_homework_class"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    homework_id: Mapped[int] = mapped_column(ForeignKey("homeworks.id"), index=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), index=True)

    homework: Mapped["Homework"] = relationship("Homework", back_populates="class_links")


class HomeworkProblem(Base):
    __tablename__ = "homework_problems"
    __table_args__ = (UniqueConstraint("homework_id", "problem_id", name="uq_homework_problem"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    homework_id: Mapped[int] = mapped_column(ForeignKey("homeworks.id"), index=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    homework: Mapped["Homework"] = relationship("Homework", back_populates="problem_links")


class HomeworkStudent(Base):
    __tablename__ = "homework_students"
    __table_args__ = (UniqueConstraint("homework_id", "student_id", name="uq_homework_student"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    homework_id: Mapped[int] = mapped_column(ForeignKey("homeworks.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    homework: Mapped["Homework"] = relationship("Homework", back_populates="student_links")


class HomeworkStudentAck(Base, TimestampMixin):
    __tablename__ = "homework_student_acks"
    __table_args__ = (UniqueConstraint("homework_id", "student_id", name="uq_homework_student_ack"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    homework_id: Mapped[int] = mapped_column(ForeignKey("homeworks.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

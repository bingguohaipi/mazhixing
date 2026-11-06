from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditMixin, Base, TimestampMixin


class TeachingClass(Base, TimestampMixin, AuditMixin):
    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    course_type: Mapped[str] = mapped_column(String(64))
    schedule: Mapped[str] = mapped_column(String(128))
    expected_student_count: Mapped[int] = mapped_column(default=30)
    lesson_count: Mapped[int] = mapped_column(default=16)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)

    enrollments: Mapped[list["ClassEnrollment"]] = relationship("ClassEnrollment", back_populates="teaching_class")
    groups: Mapped[list["StudentGroup"]] = relationship("StudentGroup", back_populates="teaching_class")


class StudentGroup(Base, TimestampMixin):
    __tablename__ = "student_groups"
    __table_args__ = (UniqueConstraint("class_id", "name", name="uq_class_group_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), index=True)
    name: Mapped[str] = mapped_column(String(64))
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)

    teaching_class: Mapped["TeachingClass"] = relationship("TeachingClass", back_populates="groups")


class ClassEnrollment(Base, TimestampMixin):
    __tablename__ = "class_students"
    __table_args__ = (UniqueConstraint("class_id", "student_id", name="uq_class_student"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    group_id: Mapped[int | None] = mapped_column(ForeignKey("student_groups.id"), nullable=True, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)

    teaching_class: Mapped["TeachingClass"] = relationship("TeachingClass", back_populates="enrollments")
    group: Mapped["StudentGroup | None"] = relationship("StudentGroup")

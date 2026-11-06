import enum
from datetime import datetime

from sqlalchemy import JSON, Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditMixin, Base, TimestampMixin
from app.models.enum_utils import mysql_enum


class ProblemLanguage(str, enum.Enum):
    PYTHON = "Python"
    CPP = "C++"


class ProblemDifficulty(str, enum.Enum):
    BEGINNER = "入门"
    EASY = "简单"
    MEDIUM = "中等"
    HARD = "困难"


class GespLevel(str, enum.Enum):
    GESP1 = "GESP1"
    GESP2 = "GESP2"
    GESP3 = "GESP3"
    GESP4 = "GESP4"


class ProblemScope(str, enum.Enum):
    PRIVATE = "private"
    PUBLIC = "public"


class PublicPublishStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Problem(Base, TimestampMixin, AuditMixin):
    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    image_urls: Mapped[list | None] = mapped_column(JSON, nullable=True)
    language: Mapped[ProblemLanguage] = mapped_column(Enum(ProblemLanguage))
    languages: Mapped[list | None] = mapped_column(JSON, nullable=True)
    difficulty: Mapped[ProblemDifficulty] = mapped_column(Enum(ProblemDifficulty))
    gesp_level: Mapped[GespLevel] = mapped_column(Enum(GespLevel), index=True)
    knowledge_point: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    knowledge_points: Mapped[list | None] = mapped_column(JSON, nullable=True)
    input_format: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_format: Mapped[str | None] = mapped_column(Text, nullable=True)
    sample_input: Mapped[str | None] = mapped_column(Text, nullable=True)
    sample_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    time_limit_ms: Mapped[int] = mapped_column(Integer, default=1000)
    memory_limit_mb: Mapped[int] = mapped_column(Integer, default=256)
    scope: Mapped[ProblemScope] = mapped_column(
        mysql_enum(ProblemScope), default=ProblemScope.PRIVATE, index=True
    )
    publish_status: Mapped[PublicPublishStatus] = mapped_column(
        mysql_enum(PublicPublishStatus), default=PublicPublishStatus.PUBLISHED, index=True
    )
    public_group_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    # 教师自有题库独立编号（与公共题库全局 id 无关），仅 private 题目使用
    private_no: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    arena_enabled: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    arena_opened_at: Mapped[datetime | None] = mapped_column(nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)

    test_cases: Mapped[list["TestCase"]] = relationship("TestCase", back_populates="problem")


class TestCase(Base, TimestampMixin):
    __tablename__ = "test_cases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    input_data: Mapped[str] = mapped_column(Text)
    expected_output: Mapped[str] = mapped_column(Text)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)

    problem: Mapped["Problem"] = relationship("Problem", back_populates="test_cases")

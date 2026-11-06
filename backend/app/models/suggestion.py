import enum
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.models.enum_utils import mysql_enum


class SuggestionContextType(str, enum.Enum):
    GENERAL = "general"
    PROBLEM = "problem"


class SuggestionStatus(str, enum.Enum):
    PENDING = "pending"
    READ = "read"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Suggestion(Base, TimestampMixin):
    __tablename__ = "suggestions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    to_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    context_type: Mapped[SuggestionContextType] = mapped_column(
        mysql_enum(SuggestionContextType), default=SuggestionContextType.GENERAL
    )
    context_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200), default="", server_default="")
    content: Mapped[str] = mapped_column(Text)
    image_urls: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[SuggestionStatus] = mapped_column(
        mysql_enum(SuggestionStatus), default=SuggestionStatus.PENDING, index=True
    )
    satisfaction_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)

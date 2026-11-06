from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class SuggestionReply(Base, TimestampMixin):
    __tablename__ = "suggestion_replies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    suggestion_id: Mapped[int] = mapped_column(ForeignKey("suggestions.id"), index=True)
    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    content: Mapped[str] = mapped_column(Text, default="")
    image_urls: Mapped[str | None] = mapped_column(Text, nullable=True)

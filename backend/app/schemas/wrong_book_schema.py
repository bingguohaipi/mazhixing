from datetime import datetime
from typing import Literal

from pydantic import BaseModel

WrongReviewStatus = Literal["pending", "reviewing", "mastered"]
WrongSortBy = Literal["error_count", "last_error", "difficulty"]


class WrongBookSummary(BaseModel):
    pending_count: int
    reviewing_count: int
    mastered_count: int


class WrongBookItem(BaseModel):
    problem_id: int
    title: str
    difficulty: str
    knowledge_point: str | None
    review_status: WrongReviewStatus
    error_count: int
    last_error_at: datetime
    last_submission_id: int
    last_status: str
    last_code: str
    ai_analysis: str | None
    error_reason: str | None


class WrongBookListResponse(BaseModel):
    summary: WrongBookSummary
    items: list[WrongBookItem]


class WrongBookClearRequest(BaseModel):
    problem_id: int | None = None

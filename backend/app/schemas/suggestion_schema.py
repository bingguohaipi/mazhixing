from datetime import datetime

from pydantic import BaseModel, Field


class SuggestionRecipient(BaseModel):
    id: int
    role: str
    display_name: str
    account: str


class SuggestionCreateRequest(BaseModel):
    to_user_id: int = Field(..., ge=1)
    title: str = Field(default="", max_length=200)
    content: str = Field(..., min_length=1, max_length=2000)
    context_type: str = Field(default="general", pattern="^(general|problem)$")
    context_id: int | None = None
    image_urls: list[str] = Field(default_factory=list, max_length=3)


class SuggestionStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(pending|read|resolved|closed)$")


class SuggestionRatingRequest(BaseModel):
    score: int = Field(..., ge=1, le=5)


class SuggestionReplyCreateRequest(BaseModel):
    content: str = Field(default="", max_length=2000)
    image_urls: list[str] = Field(default_factory=list, max_length=3)


class SuggestionProblemContext(BaseModel):
    id: int
    title: str
    scope: str
    private_no: int | None = None


class SuggestionReplyItem(BaseModel):
    id: int
    suggestion_id: int
    from_user_id: int
    from_user_name: str
    from_user_role: str
    content: str
    image_urls: list[str]
    created_at: datetime


class SuggestionItem(BaseModel):
    id: int
    title: str
    from_user_id: int
    from_user_name: str
    from_user_role: str
    to_user_id: int
    to_user_name: str
    to_user_role: str
    context_type: str
    context_id: int | None
    context_problem: SuggestionProblemContext | None = None
    content: str
    image_urls: list[str]
    status: str
    satisfaction_rating: int | None = None
    created_at: datetime
    replies: list[SuggestionReplyItem] = Field(default_factory=list)


class SuggestionListResponse(BaseModel):
    items: list[SuggestionItem]
    total: int
    page: int
    page_size: int

from pydantic import BaseModel, Field


class AdminKnowledgePointListItem(BaseModel):
    id: int
    name: str
    summary: str
    content_markdown: str
    sort_order: int
    problem_count: int = 0


class AdminKnowledgePointListResponse(BaseModel):
    items: list[AdminKnowledgePointListItem]


class AdminKnowledgePointCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    summary: str = Field(default="", max_length=512)
    content_markdown: str = Field(default="")
    sort_order: int = Field(default=100, ge=0, le=9999)


class AdminKnowledgePointUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=64)
    summary: str | None = Field(None, max_length=512)
    content_markdown: str | None = None
    sort_order: int | None = Field(None, ge=0, le=9999)

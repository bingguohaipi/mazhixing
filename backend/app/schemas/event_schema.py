from pydantic import BaseModel, Field


class EventTrackItem(BaseModel):
    event_name: str = Field(..., min_length=1, max_length=64)
    page: str | None = Field(None, max_length=128)
    module: str | None = Field(None, max_length=64)
    detail: str | None = Field(None, max_length=500)


class EventTrackRequest(BaseModel):
    events: list[EventTrackItem] = Field(..., min_length=1, max_length=20)


class EventSummaryItem(BaseModel):
    event_name: str
    count: int


class EventSummaryResponse(BaseModel):
    period_days: int
    total_events: int
    error_events: int
    judge_success_rate: float | None
    top_events: list[EventSummaryItem]

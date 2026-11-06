from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class LeaderboardScoreBreakdown(BaseModel):
    accuracy_rate: float
    accuracy_score: float
    avg_runtime_ms: float | None
    time_score: float
    total_score: float


class LeaderboardEntry(BaseModel):
    rank: int
    student_id: int
    display_name: str
    nickname: str | None = None
    real_name: str | None = None
    completed_problems: int
    accuracy_rate: float
    total_score: float
    is_me: bool = False


class LeaderboardResponse(BaseModel):
    class_id: int
    class_name: str
    my_rank: int | None
    my_score: LeaderboardScoreBreakdown | None
    entries: list[LeaderboardEntry]
    snapshot_date: date | None = None
    refreshed_at: datetime | None = None
    source: Literal["snapshot", "live"] = "live"

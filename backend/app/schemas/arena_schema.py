from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ArenaSessionStatusLiteral = Literal["in_progress", "submitted", "exited", "expired", "cancelled"]
ArenaReviewStatusLiteral = Literal["none", "pending", "approved", "rejected"]
ArenaMyStatusLiteral = Literal["none", "in_progress", "pending_review", "rejected", "on_board"]
ArenaLanguageLiteral = Literal["Python", "C++"]


class ArenaSessionCreateRequest(BaseModel):
    problem_id: int
    language: ArenaLanguageLiteral


class ArenaSessionMetricsPatch(BaseModel):
    paste_count: int = Field(0, ge=0)
    paste_char_count: int = Field(0, ge=0)
    first_keystroke_at: datetime | None = None


class ArenaSubmitRequest(BaseModel):
    code: str = Field(..., min_length=1)


class ArenaSessionBrief(BaseModel):
    id: int
    problem_id: int
    language: str
    status: ArenaSessionStatusLiteral
    started_at: datetime
    expires_at: datetime
    submitted_at: datetime | None = None


class ArenaSessionDetail(ArenaSessionBrief):
    submission_id: int | None = None


class ArenaProblemListItem(BaseModel):
    id: int
    title: str
    language: str
    languages: list[str] = []
    difficulty: str
    gesp_level: str
    knowledge_point: str | None
    champion_name: str | None = None
    champion_score: float | None = None
    participant_count: int = 0


class ArenaProblemListResponse(BaseModel):
    items: list[ArenaProblemListItem]
    total: int
    page: int
    page_size: int


class ArenaBoardEntry(BaseModel):
    rank: int
    user_id: int
    display_name: str
    student_no_suffix: str | None = None
    arena_score: float
    duration_ms: int
    achieved_at: datetime
    is_me: bool = False


class ArenaBoardResponse(BaseModel):
    problem_id: int
    language: str
    entries: list[ArenaBoardEntry]
    my_entry: ArenaBoardEntry | None = None
    my_status: ArenaMyStatusLiteral
    total_participants: int


class ArenaGlobalLeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    display_name: str
    student_no_suffix: str | None = None
    problems_passed: int
    attempt_count: int
    ac_count: int
    accuracy_rate: float
    total_duration_ms: int
    composite_score: float
    is_me: bool = False


class ArenaGlobalLeaderboardResponse(BaseModel):
    language: str
    entries: list[ArenaGlobalLeaderboardEntry]
    my_entry: ArenaGlobalLeaderboardEntry | None = None
    total_participants: int


class ArenaOverviewResponse(BaseModel):
    active_session: ArenaSessionBrief | None
    unread_notifications: int
    hot_problems: list[ArenaProblemListItem]


class ArenaResultBrief(BaseModel):
    review_status: ArenaReviewStatusLiteral
    arena_score: float | None = None
    duration_ms: int | None = None
    judge_status: str


class ArenaSubmitResponse(BaseModel):
    submission_id: int
    status: str
    arena_result: ArenaResultBrief | None = None
    points_awarded: int | None = None
    points_balance: int | None = None


class ArenaNotificationItem(BaseModel):
    id: int
    event_key: str
    title: str
    body: str
    is_read: bool
    created_at: datetime
    payload_json: str | None = None


class ArenaNotificationListResponse(BaseModel):
    items: list[ArenaNotificationItem]
    total: int
    page: int
    page_size: int


class ArenaNotificationsReadRequest(BaseModel):
    ids: list[int] | None = None
    all: bool = False


class AdminArenaEnabledPatch(BaseModel):
    arena_enabled: bool

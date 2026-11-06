from datetime import datetime

from pydantic import BaseModel
from typing import Literal

from app.schemas.wrong_book_schema import WrongBookSummary, WrongReviewStatus, WrongSortBy

ParentPeriod = Literal["7", "30"]


class ParentChildBrief(BaseModel):
    student_id: int
    display_name: str
    student_no: str | None
    class_names: list[str]


class ParentKnowledgePointStat(BaseModel):
    name: str
    mastery_rate: float


class ParentTrendItem(BaseModel):
    date: str
    label: str
    count: int


class ParentWrongProblemItem(BaseModel):
    problem_id: int
    title: str
    knowledge_point: str | None
    wrong_count: int


class ParentHomeworkItem(BaseModel):
    homework_id: int
    title: str
    status: str
    progress: str
    end_time: datetime
    is_late_only: bool = False


class ParentStudentOverview(BaseModel):
    student_id: int
    display_name: str
    student_no: str | None
    class_names: list[str]
    period_days: int
    total_submissions: int
    accuracy: float
    completed_problems: int
    wrong_count: int
    knowledge_points: list[ParentKnowledgePointStat]
    learning_trend: list[ParentTrendItem]
    top_wrong_problems: list[ParentWrongProblemItem]
    recent_homeworks: list[ParentHomeworkItem]


class ParentWrongBookItem(BaseModel):
    problem_id: int
    title: str
    difficulty: str
    knowledge_point: str | None
    review_status: WrongReviewStatus
    error_count: int
    last_error_at: datetime
    last_status: str
    ai_analysis: str | None
    error_reason: str | None


class ParentWrongBookListResponse(BaseModel):
    summary: WrongBookSummary
    items: list[ParentWrongBookItem]

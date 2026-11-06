from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SubmissionStatusLiteral = Literal["AC", "WA", "CE", "TLE", "RE", "PENDING"]


class SubmissionCreateRequest(BaseModel):
    problem_id: int
    homework_id: int | None = None
    code: str = Field(..., min_length=1)
    language: Literal["Python", "C++"]


class SubmissionCaseResultItem(BaseModel):
    case_index: int
    status: SubmissionStatusLiteral
    is_sample: bool = False
    actual_output: str | None = None
    runtime_ms: int | None = None


class SubmissionDetail(BaseModel):
    id: int
    problem_id: int
    homework_id: int | None
    language: str
    status: SubmissionStatusLiteral
    runtime_ms: int | None
    memory_kb: int | None
    is_late: bool
    error_message: str | None
    compile_output: str | None
    ai_analysis: str | None = None
    ai_highlight_lines: list[int] = Field(default_factory=list)
    case_results: list[SubmissionCaseResultItem]
    created_at: datetime
    points_awarded: int | None = None
    points_balance: int | None = None


class TeacherSubmissionDetail(SubmissionDetail):
    code: str
    student_display_name: str
    student_account: str


class SubmissionListItem(BaseModel):
    id: int
    problem_id: int
    homework_id: int | None
    language: str
    status: SubmissionStatusLiteral
    runtime_ms: int | None
    is_late: bool
    created_at: datetime

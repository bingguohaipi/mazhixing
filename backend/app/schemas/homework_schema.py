from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

HomeworkStatusLiteral = Literal["未开始", "进行中", "已截止", "已撤回"]


class HomeworkCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    start_time: datetime
    end_time: datetime
    allow_late_submission: bool = False
    class_ids: list[int] = Field(..., min_length=1)
    problem_ids: list[int] = Field(..., min_length=1)
    student_ids: list[int] | None = None

    @model_validator(mode="after")
    def validate_time_range(self) -> "HomeworkCreateRequest":
        if self.end_time <= self.start_time:
            raise ValueError("截止时间必须晚于开始时间")
        return self


class HomeworkUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    start_time: datetime | None = None
    end_time: datetime | None = None
    allow_late_submission: bool | None = None
    class_ids: list[int] | None = None
    problem_ids: list[int] | None = None
    student_ids: list[int] | None = None


class HomeworkAllowLateRequest(BaseModel):
    allow_late_submission: bool


class HomeworkClassBrief(BaseModel):
    id: int
    name: str


class HomeworkProblemBrief(BaseModel):
    id: int
    title: str
    language: str
    difficulty: str


class HomeworkListItem(BaseModel):
    id: int
    title: str
    status: HomeworkStatusLiteral
    class_ids: list[int]
    class_names: list[str]
    problem_count: int
    total_students: int
    submitted_count: int
    correct_count: int
    wrong_count: int
    progress_done: int = 0
    progress_total: int = 0
    late_submission_count: int = 0
    start_time: datetime
    end_time: datetime
    allow_late_submission: bool
    created_at: datetime


class HomeworkDetail(HomeworkListItem):
    description: str | None
    classes: list[HomeworkClassBrief]
    problems: list[HomeworkProblemBrief]
    student_ids: list[int]


class HomeworkStudentProblemAttempt(BaseModel):
    problem_id: int
    problem_title: str
    status: str | None = None
    submission_id: int | None = None
    error_message: str | None = None
    is_late: bool = False


class HomeworkStudentProgressRow(BaseModel):
    student_id: int
    display_name: str
    account: str
    student_no: str | None
    ac_count: int
    problem_count: int
    all_ac: bool
    problems: list[HomeworkStudentProblemAttempt]


class HomeworkSubmissionReport(BaseModel):
    homework_id: int
    homework_title: str
    problem_count: int
    problems: list[HomeworkProblemBrief]
    all_ac_students: list[str]
    students: list[HomeworkStudentProgressRow]


class StudentHomeworkItem(BaseModel):
    id: int
    title: str
    status: HomeworkStatusLiteral
    class_name: str
    problem_count: int
    start_time: datetime
    end_time: datetime
    allow_late_submission: bool
    progress: str | None = None
    has_unread_update: bool = False
    content_updated_at: datetime | None = None

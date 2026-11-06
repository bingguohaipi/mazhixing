from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.problem_schema import (
    GespLevelLiteral,
    ProblemDifficultyLiteral,
    ProblemLanguageLiteral,
)
from app.schemas.homework_schema import HomeworkStatusLiteral

ProblemStatusLiteral = Literal["passed", "failed", "untried"]


class PracticeProblemListItem(BaseModel):
    id: int
    title: str
    language: ProblemLanguageLiteral
    languages: list[ProblemLanguageLiteral]
    difficulty: ProblemDifficultyLiteral
    gesp_level: GespLevelLiteral
    knowledge_point: str | None
    pass_rate: float
    submission_count: int
    my_status: ProblemStatusLiteral
    my_submission_count: int
    best_status: str | None


class StudentTestCaseItem(BaseModel):
    id: int
    input_data: str | None = None
    expected_output: str | None = None
    is_sample: bool
    sort_order: int


class PracticeProblemDetail(BaseModel):
    id: int
    title: str
    description: str
    image_urls: list[str] = Field(default_factory=list)
    language: ProblemLanguageLiteral
    languages: list[ProblemLanguageLiteral]
    difficulty: ProblemDifficultyLiteral
    gesp_level: GespLevelLiteral
    knowledge_point: str | None
    input_format: str | None
    output_format: str | None
    sample_input: str | None
    sample_output: str | None
    hint: str | None
    time_limit_ms: int
    memory_limit_mb: int
    test_cases: list[StudentTestCaseItem]
    pass_rate: float
    submission_count: int
    my_best_status: str | None
    is_public_catalog: bool = False


class PracticeProblemListResponse(BaseModel):
    items: list[PracticeProblemListItem]
    total: int
    page: int
    page_size: int


class KnowledgePointTagItem(BaseModel):
    name: str
    problem_count: int


class KnowledgePointListResponse(BaseModel):
    items: list[KnowledgePointTagItem]
    total_problems: int
    solved_count: int


class KnowledgePointDifficultyProgress(BaseModel):
    label: str
    total: int
    solved: int
    attempting: int


class KnowledgePointDetailResponse(BaseModel):
    name: str
    problem_count: int
    solved_count: int
    attempting_count: int
    description: str | None
    content_markdown: str | None = None
    difficulty_progress: list[KnowledgePointDifficultyProgress]
    first_untried_problem_id: int | None
    first_problem_id: int | None = None


class KnowledgePointOptionItem(BaseModel):
    name: str
    summary: str


class StudentHomeworkProblemItem(BaseModel):
    id: int
    title: str
    language: str
    difficulty: str
    best_status: str | None
    submission_count: int


class StudentHomeworkDetail(BaseModel):
    id: int
    title: str
    description: str | None
    status: HomeworkStatusLiteral
    class_name: str
    start_time: datetime
    end_time: datetime
    allow_late_submission: bool
    progress: str
    problems: list[StudentHomeworkProblemItem]
    has_unread_update: bool = False
    update_notice: str | None = None

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.utils.problem_knowledge import normalize_knowledge_point_names
from app.utils.problem_languages import normalize_languages

ProblemLanguageLiteral = Literal["Python", "C++"]
ProblemDifficultyLiteral = Literal["入门", "简单", "中等", "困难"]
GespLevelLiteral = Literal["GESP1", "GESP2", "GESP3", "GESP4"]


class TestCaseInput(BaseModel):
    input_data: str = ""
    expected_output: str = Field(..., min_length=1)
    is_sample: bool = False
    sort_order: int = 0


class TestCaseItem(TestCaseInput):
    id: int


class ProblemCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    languages: list[ProblemLanguageLiteral] = Field(..., min_length=1, max_length=2)
    difficulty: ProblemDifficultyLiteral
    gesp_level: GespLevelLiteral = "GESP1"
    knowledge_points: list[str] = Field(..., min_length=1, max_length=16)
    input_format: str | None = None
    output_format: str | None = None
    sample_input: str | None = None
    sample_output: str | None = None
    reference_answer: str | None = None
    hint: str | None = None
    time_limit_ms: int = Field(1000, ge=100, le=10000)
    memory_limit_mb: int = Field(256, ge=1, le=256)
    test_cases: list[TestCaseInput] = Field(..., min_length=1)
    image_urls: list[str] = Field(default_factory=list, max_length=5)

    @field_validator("image_urls")
    @classmethod
    def validate_image_urls(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item and item.strip()]
        if len(cleaned) > 5:
            raise ValueError("题目插图最多 5 张")
        return cleaned[:5]

    @field_validator("knowledge_points")
    @classmethod
    def validate_knowledge_points(cls, value: list[str]) -> list[str]:
        return normalize_knowledge_point_names(value)

    @field_validator("languages")
    @classmethod
    def validate_languages(cls, value: list[str]) -> list[str]:
        return normalize_languages(value)

    @model_validator(mode="after")
    def validate_test_cases(self) -> "ProblemCreateRequest":
        valid_cases = [tc for tc in self.test_cases if tc.expected_output.strip()]
        if not valid_cases:
            raise ValueError("至少配置一组有效测试用例（期望输出不能为空；无输入题可将输入留空）")
        self.test_cases = valid_cases
        return self


class ProblemUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, min_length=1)
    languages: list[ProblemLanguageLiteral] | None = Field(None, min_length=1, max_length=2)
    difficulty: ProblemDifficultyLiteral | None = None
    gesp_level: GespLevelLiteral | None = None
    knowledge_points: list[str] | None = Field(None, min_length=1, max_length=16)
    input_format: str | None = None
    output_format: str | None = None
    sample_input: str | None = None
    sample_output: str | None = None
    reference_answer: str | None = None
    hint: str | None = None
    time_limit_ms: int | None = Field(None, ge=100, le=10000)
    memory_limit_mb: int | None = Field(None, ge=1, le=256)
    test_cases: list[TestCaseInput] | None = None
    image_urls: list[str] | None = Field(None, max_length=5)

    @field_validator("knowledge_points")
    @classmethod
    def validate_knowledge_points(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return normalize_knowledge_point_names(value)

    @field_validator("languages")
    @classmethod
    def validate_languages(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return normalize_languages(value)

    @field_validator("image_urls")
    @classmethod
    def validate_image_urls(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned = [item.strip() for item in value if item and item.strip()]
        if len(cleaned) > 5:
            raise ValueError("题目插图最多 5 张")
        return cleaned[:5]

    @field_validator("test_cases")
    @classmethod
    def validate_test_cases(cls, value: list[TestCaseInput] | None) -> list[TestCaseInput] | None:
        if value is None:
            return None
        valid_cases = [tc for tc in value if tc.expected_output.strip()]
        if not valid_cases:
            raise ValueError("至少配置一组有效测试用例（期望输出不能为空）")
        return valid_cases


class ProblemListItem(BaseModel):
    id: int
    private_no: int | None = None
    title: str
    language: ProblemLanguageLiteral
    languages: list[ProblemLanguageLiteral]
    difficulty: ProblemDifficultyLiteral
    gesp_level: GespLevelLiteral
    knowledge_point: str | None
    knowledge_points: list[str]
    test_case_count: int
    is_publishable: bool
    pass_rate: float
    submission_count: int
    created_at: datetime


class ProblemDetail(BaseModel):
    id: int
    private_no: int | None = None
    title: str
    description: str
    image_urls: list[str] = Field(default_factory=list)
    language: ProblemLanguageLiteral
    languages: list[ProblemLanguageLiteral]
    difficulty: ProblemDifficultyLiteral
    gesp_level: GespLevelLiteral
    knowledge_point: str | None
    knowledge_points: list[str]
    input_format: str | None
    output_format: str | None
    sample_input: str | None
    sample_output: str | None
    reference_answer: str | None
    hint: str | None
    time_limit_ms: int
    memory_limit_mb: int
    test_cases: list[TestCaseItem]
    is_publishable: bool
    pass_rate: float
    submission_count: int
    created_at: datetime
    updated_at: datetime


class ProblemAcSolverItem(BaseModel):
    user_id: int
    display_name: str
    account: str
    student_no: str | None
    first_ac_at: datetime


class ProblemAcSolverListResponse(BaseModel):
    items: list[ProblemAcSolverItem]
    total: int


class ProblemListResponse(BaseModel):
    items: list[ProblemListItem]
    total: int
    page: int
    page_size: int


class ProblemImportRequest(BaseModel):
    problems: list[dict[str, Any]] = Field(..., min_length=1, max_length=50)


class ProblemImportFailedRow(BaseModel):
    row: int
    title: str | None
    reason: str


class ProblemImportResult(BaseModel):
    success_count: int
    failed: list[ProblemImportFailedRow]
    created_ids: list[int]

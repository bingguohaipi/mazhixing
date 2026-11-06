from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.utils.class_course_type import validate_class_course_type


class ClassCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    course_type: str = Field(..., min_length=1, max_length=64)

    @field_validator("course_type")
    @classmethod
    def check_course_type(cls, value: str) -> str:
        return validate_class_course_type(value)
    schedule: str = Field(..., min_length=1, max_length=128)
    expected_student_count: int = Field(30, ge=1, le=200)
    lesson_count: int = Field(16, ge=1, le=500)
    description: str | None = Field(None, max_length=2000)


class ClassUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=128)
    course_type: str | None = Field(None, min_length=1, max_length=64)

    @field_validator("course_type")
    @classmethod
    def check_course_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_class_course_type(value)
    schedule: str | None = Field(None, min_length=1, max_length=128)
    expected_student_count: int | None = Field(None, ge=1, le=200)
    lesson_count: int | None = Field(None, ge=1, le=500)
    description: str | None = Field(None, max_length=2000)


class StudentBrief(BaseModel):
    id: int
    account: str
    real_name: str | None = None
    nickname: str | None = None
    display_name: str


class ClassListItem(BaseModel):
    id: int
    name: str
    course_type: str
    schedule: str
    expected_student_count: int
    lesson_count: int
    description: str | None
    student_count: int
    students_preview: list[StudentBrief]


class ClassDetail(ClassListItem):
    created_at: datetime
    updated_at: datetime


class StudentCreateRequest(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=64)
    account: str | None = Field(None, min_length=3, max_length=64)
    student_no: str | None = Field(None, min_length=1, max_length=32)

    @field_validator("account")
    @classmethod
    def normalize_account(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip().lower()


class StudentUpdateRequest(BaseModel):
    """Deprecated: teachers cannot change real name or nickname."""

    display_name: str | None = Field(None, min_length=1, max_length=64)
    student_no: str | None = Field(None, min_length=1, max_length=32)


class StudentGroupItem(BaseModel):
    id: int
    name: str
    student_count: int


class StudentGroupCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)


class StudentGroupUpdateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)


class AssignStudentGroupRequest(BaseModel):
    group_id: int | None = None


class ClassStudentItem(BaseModel):
    id: int
    account: str
    real_name: str | None = None
    nickname: str | None = None
    display_name: str
    completed_problems: int = 0
    accuracy: float = 0.0
    last_active: str | None = None
    is_active: bool = True
    group_id: int | None = None
    group_name: str | None = None


class StudentCreateResponse(BaseModel):
    student: ClassStudentItem
    default_password: str


class BindParentRequest(BaseModel):
    parent_phone: str = Field(..., min_length=11, max_length=20)
    parent_name: str | None = Field(None, min_length=1, max_length=64)


class ParentBindingItem(BaseModel):
    id: int
    parent_id: int
    parent_phone: str
    parent_name: str
    student_id: int
    created_at: datetime


class BindParentResponse(BaseModel):
    binding: ParentBindingItem
    default_password: str | None = None

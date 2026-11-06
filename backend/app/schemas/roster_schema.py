from pydantic import BaseModel, Field


class RosterStudentItem(BaseModel):
    id: int
    account: str
    real_name: str | None = None
    nickname: str | None = None
    display_name: str
    class_names: list[str]


class RosterListResponse(BaseModel):
    items: list[RosterStudentItem]
    total: int


class RosterBatchCreateRequest(BaseModel):
    names: list[str] = Field(..., min_length=1, max_length=100)
    year: int = Field(..., ge=2000, le=2100)


class RosterBatchCreateResultItem(BaseModel):
    display_name: str
    account: str
    student_id: int


class RosterBatchCreateResponse(BaseModel):
    created: list[RosterBatchCreateResultItem]
    default_password: str


class EnrollStudentsRequest(BaseModel):
    student_ids: list[int] = Field(..., min_length=1, max_length=100)


class RosterStudentUpdateRequest(BaseModel):
    """Deprecated: teachers cannot change real name or nickname."""

    display_name: str | None = Field(None, min_length=1, max_length=64)
    student_no: str | None = Field(None, min_length=1, max_length=32)

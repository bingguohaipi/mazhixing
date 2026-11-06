from pydantic import BaseModel, Field, field_validator

from app.utils.profanity import validate_student_nickname


class StudentProfileTeacherItem(BaseModel):
    id: int
    display_name: str
    class_names: list[str] = Field(default_factory=list)


class StudentProfileParentItem(BaseModel):
    id: int
    display_name: str


class StudentProfileResponse(BaseModel):
    account: str
    real_name: str | None = Field(None, description="真实姓名（由老师/管理员维护）")
    display_name: str | None = Field(None, description="同 real_name，兼容旧字段")
    nickname: str | None
    class_names: list[str] = Field(default_factory=list)
    avatar_url: str | None
    student_no: str | None
    teachers: list[StudentProfileTeacherItem]
    parents: list[StudentProfileParentItem]


class StudentNicknameUpdateRequest(BaseModel):
    nickname: str = Field(..., min_length=1, max_length=32)

    @field_validator("nickname")
    @classmethod
    def check_nickname(cls, value: str) -> str:
        return validate_student_nickname(value)

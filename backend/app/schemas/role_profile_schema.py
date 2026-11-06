from pydantic import BaseModel, Field, field_validator

from app.utils.profanity import validate_student_nickname


class NicknameUpdateRequest(BaseModel):
    nickname: str = Field(..., min_length=1, max_length=32)

    @field_validator("nickname")
    @classmethod
    def check_nickname(cls, value: str) -> str:
        return validate_student_nickname(value)


class TeacherProfileResponse(BaseModel):
    account: str
    real_name: str | None
    nickname: str | None
    class_names: list[str] = Field(default_factory=list)
    phone: str | None


class ParentProfileChildItem(BaseModel):
    id: int
    real_name: str | None
    account: str
    class_names: list[str] = Field(default_factory=list)


class ParentProfileResponse(BaseModel):
    account: str
    real_name: str | None
    nickname: str | None
    class_names: list[str] = Field(default_factory=list)
    children: list[ParentProfileChildItem] = Field(default_factory=list)

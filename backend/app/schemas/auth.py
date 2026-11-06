import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

UserRoleLiteral = Literal["admin", "teacher", "student", "parent"]
VerificationPurposeLiteral = Literal["register", "reset_password"]

PASSWORD_PATTERN = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{6,20}$")
PHONE_PATTERN = re.compile(r"^1[3-9]\d{9}$")


def validate_strong_password(value: str) -> str:
    if not PASSWORD_PATTERN.match(value):
        raise ValueError("密码长度为6-20位，需同时包含字母和数字")
    return value


def validate_phone(value: str) -> str:
    if not PHONE_PATTERN.match(value):
        raise ValueError("请输入正确的11位手机号码")
    return value


class SendCodeRequest(BaseModel):
    phone: str = Field(..., description="手机号")
    purpose: VerificationPurposeLiteral
    role: UserRoleLiteral | None = None

    @field_validator("phone")
    @classmethod
    def check_phone(cls, value: str) -> str:
        return validate_phone(value)


class RegisterRequest(BaseModel):
    phone: str
    code: str = Field(..., min_length=6, max_length=6)
    password: str = Field(..., min_length=6, max_length=20)
    role: Literal["teacher", "parent"]
    display_name: str | None = Field(None, max_length=64)

    @field_validator("phone")
    @classmethod
    def check_phone(cls, value: str) -> str:
        return validate_phone(value)

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return validate_strong_password(value)


class LoginRequest(BaseModel):
    account: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=64)
    role: UserRoleLiteral

    @model_validator(mode="after")
    def validate_account_by_role(self) -> "LoginRequest":
        if self.role in ("teacher", "parent"):
            validate_phone(self.account)
        else:
            self.account = self.account.strip()
        return self


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1, max_length=64)
    new_password: str = Field(..., min_length=6, max_length=20)

    @field_validator("new_password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return validate_strong_password(value)


class ResetPasswordRequest(BaseModel):
    phone: str
    code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=6, max_length=20)
    role: Literal["teacher", "parent"]

    @field_validator("phone")
    @classmethod
    def check_phone(cls, value: str) -> str:
        return validate_phone(value)

    @field_validator("new_password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return validate_strong_password(value)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    id: int
    account: str
    role: UserRoleLiteral
    display_name: str | None = Field(None, description="对外展示名（昵称优先）")
    real_name: str | None = Field(None, description="真实姓名")
    nickname: str | None = Field(None, description="用户自设昵称")
    phone: str | None
    avatar_url: str | None = None
    default_coding_language: str | None = Field(
        None,
        description="学生端默认编程语言（Python/C++），由所在班级课程类型决定",
    )


class LoginResponse(BaseModel):
    tokens: TokenPair
    user: UserInfo

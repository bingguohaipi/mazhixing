from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class AdminUserListItem(BaseModel):
    id: int
    account: str
    role: str
    display_name: str | None = Field(None, description="真实姓名")
    real_name: str | None = Field(None, description="同 display_name")
    nickname: str | None = None
    class_names: list[str] = Field(default_factory=list)
    phone: str | None
    is_active: bool
    student_no: str | None
    created_at: datetime
    relation_summary: list[str] = Field(
        default_factory=list,
        description="学生→老师，家长→孩子，教师→班级",
    )


class AdminUserListResponse(BaseModel):
    items: list[AdminUserListItem]
    total: int
    page: int
    page_size: int


class AdminUserCreateRequest(BaseModel):
    account: str | None = Field(None, min_length=1, max_length=64)
    password: str | None = Field(None, min_length=6, max_length=64)
    role: str = Field(..., pattern="^(teacher|student|parent)$")
    display_name: str | None = Field(None, max_length=64)
    phone: str | None = Field(None, max_length=20)
    student_no: str | None = Field(None, max_length=32)
    created_by_teacher_id: int | None = None

    @model_validator(mode="after")
    def validate_by_role(self):
        if self.role == "student":
            if not (self.display_name or "").strip():
                raise ValueError("请填写学生真实姓名")
        elif self.role == "parent":
            phone = (self.phone or self.account or "").strip()
            if not phone:
                raise ValueError("请填写家长手机号")
            pwd = self.password or ""
            if len(pwd) < 6:
                raise ValueError("请填写至少 6 位密码")
        else:
            if not (self.account or "").strip():
                raise ValueError("请填写账号")
            pwd = self.password or ""
            if len(pwd) < 6:
                raise ValueError("请填写至少 6 位密码")
        return self


class AdminUserUpdateRequest(BaseModel):
    account: str | None = Field(None, min_length=1, max_length=64)
    display_name: str | None = Field(None, max_length=64, description="真实姓名")
    nickname: str | None = Field(None, max_length=32)
    phone: str | None = Field(None, max_length=20)
    student_no: str | None = Field(None, max_length=32)
    is_active: bool | None = None
    password: str | None = Field(None, min_length=6, max_length=64)
    created_by_teacher_id: int | None = None


class AdminParentBindingItem(BaseModel):
    id: int
    parent_id: int
    parent_account: str
    parent_name: str | None
    student_id: int
    student_name: str | None


class AdminTeacherBrief(BaseModel):
    id: int
    display_name: str | None
    account: str


class AdminUserRelationsResponse(BaseModel):
    user_id: int
    role: str
    parent_bindings: list[AdminParentBindingItem]
    bound_children: list[AdminParentBindingItem]
    teacher: AdminTeacherBrief | None
    teaching_classes: list[str] = Field(default_factory=list)
    student_teacher_lines: list[str] = Field(
        default_factory=list,
        description="学生所在班级对应的教师（含班级名）",
    )


class AdminParentStudentBindRequest(BaseModel):
    parent_id: int
    student_id: int


class AdminParentRebindRequest(BaseModel):
    new_parent_id: int


class AdminStudentTeacherBindRequest(BaseModel):
    teacher_id: int | None = None


class PublicProblemListItem(BaseModel):
    id: int
    public_group_id: int
    version: int
    title: str
    language: str
    difficulty: str
    publish_status: str
    test_case_count: int
    arena_enabled: bool = False
    created_at: datetime


class PublicProblemListResponse(BaseModel):
    items: list[PublicProblemListItem]
    total: int
    page: int
    page_size: int

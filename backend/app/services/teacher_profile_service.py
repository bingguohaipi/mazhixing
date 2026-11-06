"""Teacher personal center."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.user import User, UserRole
from app.schemas.role_profile_schema import NicknameUpdateRequest, TeacherProfileResponse
from app.utils.nickname_unique import assert_nickname_unique
from app.utils.user_class_names import teacher_class_names


class TeacherProfileService:
    def __init__(self, db: Session):
        self.db = db

    def get_profile(self, teacher_id: int) -> TeacherProfileResponse:
        teacher = self._get_teacher(teacher_id)
        return self._build(teacher)

    def update_nickname(self, teacher_id: int, payload: NicknameUpdateRequest) -> TeacherProfileResponse:
        teacher = self._get_teacher(teacher_id)
        teacher.nickname = assert_nickname_unique(self.db, payload.nickname, exclude_user_id=teacher_id)
        teacher.updated_by = teacher_id
        self.db.commit()
        self.db.refresh(teacher)
        return self._build(teacher)

    def _get_teacher(self, teacher_id: int) -> User:
        user = self.db.get(User, teacher_id)
        if user is None or user.deleted_at is not None or user.role != UserRole.TEACHER:
            raise AppException(403, "仅教师可访问个人中心")
        return user

    def _build(self, teacher: User) -> TeacherProfileResponse:
        return TeacherProfileResponse(
            account=teacher.account,
            real_name=teacher.display_name,
            nickname=teacher.nickname,
            class_names=teacher_class_names(self.db, teacher.id),
            phone=teacher.phone,
        )

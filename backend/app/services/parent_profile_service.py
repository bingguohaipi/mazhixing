"""Parent personal center."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.audit import ParentStudentBinding
from app.models.user import User, UserRole
from app.schemas.role_profile_schema import NicknameUpdateRequest, ParentProfileChildItem, ParentProfileResponse
from app.utils.nickname_unique import assert_nickname_unique
from app.utils.user_class_names import parent_class_names, student_class_names


class ParentProfileService:
    def __init__(self, db: Session):
        self.db = db

    def get_profile(self, parent_id: int) -> ParentProfileResponse:
        parent = self._get_parent(parent_id)
        return self._build(parent)

    def update_nickname(self, parent_id: int, payload: NicknameUpdateRequest) -> ParentProfileResponse:
        parent = self._get_parent(parent_id)
        parent.nickname = assert_nickname_unique(self.db, payload.nickname, exclude_user_id=parent_id)
        parent.updated_by = parent_id
        self.db.commit()
        self.db.refresh(parent)
        return self._build(parent)

    def _get_parent(self, parent_id: int) -> User:
        user = self.db.get(User, parent_id)
        if user is None or user.deleted_at is not None or user.role != UserRole.PARENT:
            raise AppException(403, "仅家长可访问个人中心")
        return user

    def _build(self, parent: User) -> ParentProfileResponse:
        children = self._list_children(parent.id)
        return ParentProfileResponse(
            account=parent.account,
            real_name=parent.display_name,
            nickname=parent.nickname,
            class_names=parent_class_names(self.db, parent.id),
            children=children,
        )

    def _list_children(self, parent_id: int) -> list[ParentProfileChildItem]:
        rows = (
            self.db.query(User)
            .join(ParentStudentBinding, ParentStudentBinding.student_id == User.id)
            .filter(
                ParentStudentBinding.parent_id == parent_id,
                User.deleted_at.is_(None),
                User.role == UserRole.STUDENT,
            )
            .order_by(User.display_name.asc(), User.account.asc())
            .all()
        )
        return [
            ParentProfileChildItem(
                id=student.id,
                real_name=student.display_name,
                account=student.account,
                class_names=student_class_names(self.db, student.id),
            )
            for student in rows
        ]

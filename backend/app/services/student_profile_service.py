"""Student personal center."""

from __future__ import annotations

import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.audit import ParentStudentBinding
from app.models.class_model import ClassEnrollment, TeachingClass
from app.models.user import User, UserRole
from app.schemas.student_profile_schema import (
    StudentNicknameUpdateRequest,
    StudentProfileParentItem,
    StudentProfileResponse,
    StudentProfileTeacherItem,
)
from app.utils.user_class_names import student_class_names
from app.utils.user_display import public_display_name
from app.utils.nickname_unique import assert_nickname_unique
from app.utils.user_media import avatar_public_url

UPLOAD_ROOT = Path(__file__).resolve().parent.parent.parent / "uploads"
AVATAR_DIR = UPLOAD_ROOT / "avatars"
ALLOWED_AVATAR_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_AVATAR_BYTES = 2 * 1024 * 1024


class StudentProfileService:
    def __init__(self, db: Session):
        self.db = db

    def get_profile(self, student_id: int) -> StudentProfileResponse:
        student = self._get_student(student_id)
        return self._build_profile(student)

    def update_nickname(self, student_id: int, payload: StudentNicknameUpdateRequest) -> StudentProfileResponse:
        student = self._get_student(student_id)
        student.nickname = assert_nickname_unique(self.db, payload.nickname, exclude_user_id=student_id)
        student.updated_by = student_id
        self.db.commit()
        self.db.refresh(student)
        return self._build_profile(student)

    async def update_avatar(self, student_id: int, content_type: str, content: bytes) -> StudentProfileResponse:
        if content_type not in ALLOWED_AVATAR_TYPES:
            raise AppException(400, "仅支持 JPG/PNG/WebP 头像")
        if len(content) > MAX_AVATAR_BYTES:
            raise AppException(400, "头像不能超过 2MB")

        student = self._get_student(student_id)
        AVATAR_DIR.mkdir(parents=True, exist_ok=True)
        suffix = ALLOWED_AVATAR_TYPES[content_type]
        filename = f"{student_id}_{uuid.uuid4().hex}{suffix}"
        target = AVATAR_DIR / filename
        target.write_bytes(content)

        if student.avatar_path:
            old = UPLOAD_ROOT / student.avatar_path
            if old.is_file() and old.parent == AVATAR_DIR:
                old.unlink(missing_ok=True)

        student.avatar_path = f"avatars/{filename}"
        student.updated_by = student_id
        self.db.commit()
        self.db.refresh(student)
        return self._build_profile(student)

    def _get_student(self, student_id: int) -> User:
        user = self.db.get(User, student_id)
        if user is None or user.deleted_at is not None or user.role != UserRole.STUDENT:
            raise AppException(403, "仅学生可访问个人中心")
        return user

    def _build_profile(self, student: User) -> StudentProfileResponse:
        real_name = student.display_name
        return StudentProfileResponse(
            account=student.account,
            real_name=real_name,
            display_name=real_name,
            nickname=student.nickname,
            class_names=student_class_names(self.db, student.id),
            avatar_url=avatar_public_url(student.avatar_path),
            student_no=student.student_no,
            teachers=self._list_teachers(student),
            parents=self._list_parents(student.id),
        )

    def _list_teachers(self, student: User) -> list[StudentProfileTeacherItem]:
        teacher_classes: dict[int, set[str]] = {}

        if student.created_by_teacher_id:
            teacher = self.db.get(User, student.created_by_teacher_id)
            if teacher and teacher.deleted_at is None and teacher.role == UserRole.TEACHER:
                teacher_classes.setdefault(teacher.id, set())

        rows = (
            self.db.query(TeachingClass)
            .join(ClassEnrollment, ClassEnrollment.class_id == TeachingClass.id)
            .filter(
                ClassEnrollment.student_id == student.id,
                ClassEnrollment.deleted_at.is_(None),
                TeachingClass.deleted_at.is_(None),
            )
            .all()
        )
        for teaching_class in rows:
            teacher_classes.setdefault(teaching_class.teacher_id, set()).add(teaching_class.name)

        items: list[StudentProfileTeacherItem] = []
        for teacher_id, class_names in teacher_classes.items():
            teacher = self.db.get(User, teacher_id)
            if teacher is None or teacher.deleted_at is not None:
                continue
            name = public_display_name(teacher)
            items.append(
                StudentProfileTeacherItem(
                    id=teacher.id,
                    display_name=name,
                    class_names=sorted(class_names),
                )
            )
        items.sort(key=lambda row: row.display_name)
        return items

    def _list_parents(self, student_id: int) -> list[StudentProfileParentItem]:
        rows = (
            self.db.query(User)
            .join(ParentStudentBinding, ParentStudentBinding.parent_id == User.id)
            .filter(
                ParentStudentBinding.student_id == student_id,
                User.deleted_at.is_(None),
                User.role == UserRole.PARENT,
            )
            .order_by(User.display_name.asc(), User.account.asc())
            .all()
        )
        return [
            StudentProfileParentItem(
                id=parent.id,
                display_name=public_display_name(parent),
            )
            for parent in rows
        ]

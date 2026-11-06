import re
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.forbidden import raise_forbidden
from app.core.masking import mask_phone
from app.core.security import hash_password
from app.models.audit import OperationLog, ParentStudentBinding
from app.models.class_model import ClassEnrollment, StudentGroup, TeachingClass
from app.models.user import User, UserRole
from app.schemas.class_schema import (
    AssignStudentGroupRequest,
    BindParentRequest,
    BindParentResponse,
    ClassCreateRequest,
    ClassDetail,
    ClassListItem,
    ClassStudentItem,
    ClassUpdateRequest,
    ParentBindingItem,
    StudentBrief,
    StudentCreateRequest,
    StudentCreateResponse,
    StudentGroupCreateRequest,
    StudentGroupItem,
    StudentGroupUpdateRequest,
    StudentUpdateRequest,
)

from app.services.stats_utils import count_student_completed_problems, student_regular_accuracy
from app.utils.class_schedule_filter import CLASS_WEEKDAYS
from app.utils.class_course_type import validate_class_course_type
from app.utils.student_identity import student_identity_fields

DEFAULT_STUDENT_PASSWORD = "123456"
DEFAULT_PARENT_PASSWORD = "123456"
ACCOUNT_PATTERN = re.compile(r"^[a-zA-Z0-9_]{3,64}$")


class ClassService:
    def __init__(self, db: Session):
        self.db = db

    def _log(self, user_id: int, action: str, detail: str | None = None) -> None:
        self.db.add(OperationLog(user_id=user_id, action=action, resource="class", detail=detail))

    def _get_owned_class(self, class_id: int, teacher_id: int) -> TeachingClass:
        teaching_class = (
            self.db.query(TeachingClass)
            .filter(
                TeachingClass.id == class_id,
                TeachingClass.teacher_id == teacher_id,
                TeachingClass.deleted_at.is_(None),
            )
            .first()
        )
        if teaching_class is None:
            raise_forbidden(self.db, teacher_id, "class", f"class_id={class_id}")
        return teaching_class

    def list_classes(
        self,
        teacher_id: int,
        keyword: str | None = None,
        weekday: str | None = None,
        course_type: str | None = None,
    ) -> list[ClassListItem]:
        query = self.db.query(TeachingClass).filter(
            TeachingClass.teacher_id == teacher_id,
            TeachingClass.deleted_at.is_(None),
        )
        if keyword:
            like = f"%{keyword.strip()}%"
            query = query.filter(TeachingClass.name.ilike(like))
        if weekday:
            if weekday not in CLASS_WEEKDAYS:
                raise AppException(400, "周几仅可选周一至周日")
            query = query.filter(TeachingClass.schedule.contains(weekday))
        if course_type:
            normalized = validate_class_course_type(course_type)
            query = query.filter(TeachingClass.course_type == normalized)

        classes = query.order_by(TeachingClass.id.desc()).all()
        return [self._to_list_item(item) for item in classes]

    def get_class(self, class_id: int, teacher_id: int) -> ClassDetail:
        teaching_class = self._get_owned_class(class_id, teacher_id)
        item = self._to_list_item(teaching_class)
        return ClassDetail(
            **item.model_dump(),
            created_at=teaching_class.created_at,
            updated_at=teaching_class.updated_at,
        )

    def _assert_unique_class_name(
        self,
        teacher_id: int,
        name: str,
        *,
        exclude_class_id: int | None = None,
    ) -> None:
        query = self.db.query(TeachingClass).filter(
            TeachingClass.teacher_id == teacher_id,
            TeachingClass.name == name,
            TeachingClass.deleted_at.is_(None),
        )
        if exclude_class_id is not None:
            query = query.filter(TeachingClass.id != exclude_class_id)
        if query.first() is not None:
            raise AppException(400, "班级名称已存在")

    def create_class(self, teacher_id: int, payload: ClassCreateRequest) -> ClassDetail:
        name = payload.name.strip()
        self._assert_unique_class_name(teacher_id, name)
        teaching_class = TeachingClass(
            teacher_id=teacher_id,
            name=name,
            course_type=payload.course_type.strip(),
            schedule=payload.schedule.strip(),
            expected_student_count=payload.expected_student_count,
            lesson_count=payload.lesson_count,
            description=payload.description.strip() if payload.description else None,
            created_by=teacher_id,
            updated_by=teacher_id,
        )
        self.db.add(teaching_class)
        self.db.flush()
        self._log(teacher_id, "create_class", f"class_id={teaching_class.id}, name={teaching_class.name}")
        self.db.commit()
        self.db.refresh(teaching_class)
        return self.get_class(teaching_class.id, teacher_id)

    def update_class(self, class_id: int, teacher_id: int, payload: ClassUpdateRequest) -> ClassDetail:
        teaching_class = self._get_owned_class(class_id, teacher_id)
        updates = payload.model_dump(exclude_unset=True)
        if "name" in updates:
            name = updates["name"].strip() if isinstance(updates["name"], str) else updates["name"]
            self._assert_unique_class_name(teacher_id, name, exclude_class_id=class_id)
            updates["name"] = name
        for field, value in updates.items():
            if isinstance(value, str):
                value = value.strip()
            setattr(teaching_class, field, value)
        teaching_class.updated_by = teacher_id
        self._log(teacher_id, "update_class", f"class_id={class_id}")
        self.db.commit()
        self.db.refresh(teaching_class)
        return self.get_class(class_id, teacher_id)

    def delete_class(self, class_id: int, teacher_id: int) -> None:
        teaching_class = self._get_owned_class(class_id, teacher_id)
        teaching_class.deleted_at = datetime.now(timezone.utc)
        teaching_class.updated_by = teacher_id
        self._log(teacher_id, "delete_class", f"class_id={class_id}")
        self.db.commit()

    def list_students(self, class_id: int, teacher_id: int, keyword: str | None = None) -> list[ClassStudentItem]:
        self._get_owned_class(class_id, teacher_id)
        query = (
            self.db.query(User, ClassEnrollment)
            .join(ClassEnrollment, ClassEnrollment.student_id == User.id)
            .filter(
                ClassEnrollment.class_id == class_id,
                ClassEnrollment.deleted_at.is_(None),
                User.role == UserRole.STUDENT,
                User.deleted_at.is_(None),
            )
        )
        if keyword:
            like = f"%{keyword.strip()}%"
            query = query.filter(
                (User.display_name.ilike(like))
                | (User.nickname.ilike(like))
                | (User.account.ilike(like))
            )

        rows = query.order_by(User.id.asc()).all()
        group_map = {g.id: g.name for g in self._list_groups(class_id)}
        return [self._to_student_item(user, enrollment, group_map) for user, enrollment in rows]

    def add_student(
        self,
        class_id: int,
        teacher_id: int,
        payload: StudentCreateRequest,
    ) -> StudentCreateResponse:
        teaching_class = self._get_owned_class(class_id, teacher_id)
        account = payload.account or self._generate_account()
        if not ACCOUNT_PATTERN.match(account):
            raise AppException(400, "账号仅支持字母、数字和下划线")

        existing = (
            self.db.query(User)
            .filter(User.account == account, User.role == UserRole.STUDENT, User.deleted_at.is_(None))
            .first()
        )
        is_new_student = existing is None

        if existing:
            student = existing
            if self._active_enrollment(class_id, student.id) is not None:
                raise AppException(400, "该学生已在班级中")
        else:
            student = User(
                account=account,
                password_hash=hash_password(DEFAULT_STUDENT_PASSWORD),
                role=UserRole.STUDENT,
                display_name=payload.display_name.strip(),
                student_no=payload.student_no.strip() if payload.student_no else None,
                created_by_teacher_id=teacher_id,
                created_by=teacher_id,
                updated_by=teacher_id,
            )
            self.db.add(student)
            self.db.flush()

        enrollment = self._enroll_or_reactivate(class_id, student.id)
        self._log(teacher_id, "add_student", f"class_id={class_id}, student_id={student.id}")
        self.db.commit()
        self.db.refresh(student)

        self.db.refresh(enrollment)
        group_map = {g.id: g.name for g in self._list_groups(class_id)}
        return StudentCreateResponse(
            student=self._to_student_item(student, enrollment, group_map),
            default_password=DEFAULT_STUDENT_PASSWORD if is_new_student else "",
        )

    def update_student(
        self,
        class_id: int,
        student_id: int,
        teacher_id: int,
        payload: StudentUpdateRequest,
    ) -> ClassStudentItem:
        self._ensure_student_in_class(class_id, student_id, teacher_id)
        raise AppException(
            403,
            "真实姓名请由管理员在用户管理中修改；昵称由学生在个人中心修改",
            status_code=403,
        )

    def enroll_students(
        self,
        class_id: int,
        teacher_id: int,
        student_ids: list[int],
    ) -> list[ClassStudentItem]:
        teaching_class = self._get_owned_class(class_id, teacher_id)
        group_map = {g.id: g.name for g in self._list_groups(class_id)}
        enrolled_items: list[ClassStudentItem] = []

        for student_id in student_ids:
            student = self._get_student_user(student_id)
            if student.created_by_teacher_id != teacher_id:
                raise AppException(403, f"学生 {student.display_name} 不在您的学生名单中", status_code=403)

            if self._active_enrollment(class_id, student_id) is not None:
                continue

            enrollment = self._enroll_or_reactivate(class_id, student_id)
            enrolled_items.append(self._to_student_item(student, enrollment, group_map))

        self._log(teacher_id, "enroll_students", f"class_id={class_id}, count={len(enrolled_items)}")
        self.db.commit()
        return enrolled_items

    def remove_student(self, class_id: int, student_id: int, teacher_id: int) -> None:
        enrollment = self._ensure_student_in_class(class_id, student_id, teacher_id)
        enrollment.deleted_at = datetime.now(timezone.utc)
        self._log(teacher_id, "remove_student", f"class_id={class_id}, student_id={student_id}")
        self.db.commit()

    def reset_student_password(self, class_id: int, student_id: int, teacher_id: int) -> str:
        self._ensure_student_in_class(class_id, student_id, teacher_id)
        student = self._get_student_user(student_id)
        student.password_hash = hash_password(DEFAULT_STUDENT_PASSWORD)
        student.updated_by = teacher_id
        self._log(teacher_id, "reset_student_password", f"class_id={class_id}, student_id={student_id}")
        self.db.commit()
        return DEFAULT_STUDENT_PASSWORD

    def bind_parent(
        self,
        class_id: int,
        student_id: int,
        teacher_id: int,
        payload: BindParentRequest,
    ) -> BindParentResponse:
        self._ensure_student_in_class(class_id, student_id, teacher_id)
        phone = payload.parent_phone.strip()
        parent = (
            self.db.query(User)
            .filter(User.account == phone, User.role == UserRole.PARENT, User.deleted_at.is_(None))
            .first()
        )
        default_password: str | None = None
        if parent is None:
            parent = User(
                account=phone,
                phone=phone,
                password_hash=hash_password(DEFAULT_PARENT_PASSWORD),
                role=UserRole.PARENT,
                display_name=payload.parent_name.strip() if payload.parent_name else "家长用户",
                created_by=teacher_id,
                updated_by=teacher_id,
            )
            self.db.add(parent)
            self.db.flush()
            default_password = DEFAULT_PARENT_PASSWORD

        existing = (
            self.db.query(ParentStudentBinding)
            .filter(
                ParentStudentBinding.parent_id == parent.id,
                ParentStudentBinding.student_id == student_id,
            )
            .first()
        )
        if existing:
            raise AppException(400, "该家长已绑定此学生")

        binding = ParentStudentBinding(parent_id=parent.id, student_id=student_id)
        self.db.add(binding)
        self._log(
            teacher_id,
            "bind_parent",
            f"class_id={class_id}, student_id={student_id}, parent_id={parent.id}",
        )
        self.db.commit()
        self.db.refresh(binding)
        self.db.refresh(parent)

        return BindParentResponse(
            binding=ParentBindingItem(
                id=binding.id,
                parent_id=parent.id,
                parent_phone=mask_phone(parent.phone or parent.account) or "",
                parent_name=parent.display_name or parent.account,
                student_id=student_id,
                created_at=binding.created_at,
            ),
            default_password=default_password,
        )

    def list_parent_bindings(
        self,
        class_id: int,
        student_id: int,
        teacher_id: int,
    ) -> list[ParentBindingItem]:
        self._ensure_student_in_class(class_id, student_id, teacher_id)
        rows = (
            self.db.query(ParentStudentBinding, User)
            .join(User, User.id == ParentStudentBinding.parent_id)
            .filter(ParentStudentBinding.student_id == student_id)
            .order_by(ParentStudentBinding.id.desc())
            .all()
        )
        return [
            ParentBindingItem(
                id=binding.id,
                parent_id=parent.id,
                parent_phone=mask_phone(parent.phone or parent.account) or "",
                parent_name=parent.display_name or parent.account,
                student_id=student_id,
                created_at=binding.created_at,
            )
            for binding, parent in rows
        ]

    def list_groups(self, class_id: int, teacher_id: int) -> list[StudentGroupItem]:
        self._get_owned_class(class_id, teacher_id)
        return self._groups_with_counts(class_id)

    def create_group(self, class_id: int, teacher_id: int, payload: StudentGroupCreateRequest) -> StudentGroupItem:
        self._get_owned_class(class_id, teacher_id)
        name = payload.name.strip()
        exists = (
            self.db.query(StudentGroup)
            .filter(
                StudentGroup.class_id == class_id,
                StudentGroup.name == name,
                StudentGroup.deleted_at.is_(None),
            )
            .first()
        )
        if exists:
            raise AppException(400, "分组名称已存在")

        group = StudentGroup(class_id=class_id, name=name)
        self.db.add(group)
        self._log(teacher_id, "create_group", f"class_id={class_id}, name={name}")
        self.db.commit()
        self.db.refresh(group)
        return StudentGroupItem(id=group.id, name=group.name, student_count=0)

    def update_group(
        self,
        class_id: int,
        group_id: int,
        teacher_id: int,
        payload: StudentGroupUpdateRequest,
    ) -> StudentGroupItem:
        group = self._get_owned_group(class_id, group_id, teacher_id)
        name = payload.name.strip()
        duplicate = (
            self.db.query(StudentGroup)
            .filter(
                StudentGroup.class_id == class_id,
                StudentGroup.name == name,
                StudentGroup.id != group_id,
                StudentGroup.deleted_at.is_(None),
            )
            .first()
        )
        if duplicate:
            raise AppException(400, "分组名称已存在")
        group.name = name
        self._log(teacher_id, "update_group", f"class_id={class_id}, group_id={group_id}")
        self.db.commit()
        self.db.refresh(group)
        count = self._group_student_count(group.id)
        return StudentGroupItem(id=group.id, name=group.name, student_count=count)

    def delete_group(self, class_id: int, group_id: int, teacher_id: int) -> None:
        group = self._get_owned_group(class_id, group_id, teacher_id)
        group.deleted_at = datetime.now(timezone.utc)
        (
            self.db.query(ClassEnrollment)
            .filter(ClassEnrollment.group_id == group_id, ClassEnrollment.deleted_at.is_(None))
            .update({ClassEnrollment.group_id: None}, synchronize_session=False)
        )
        self._log(teacher_id, "delete_group", f"class_id={class_id}, group_id={group_id}")
        self.db.commit()

    def assign_student_group(
        self,
        class_id: int,
        student_id: int,
        teacher_id: int,
        payload: AssignStudentGroupRequest,
    ) -> ClassStudentItem:
        enrollment = self._ensure_student_in_class(class_id, student_id, teacher_id)
        if payload.group_id is not None:
            self._get_owned_group(class_id, payload.group_id, teacher_id)
        enrollment.group_id = payload.group_id
        self._log(
            teacher_id,
            "assign_student_group",
            f"class_id={class_id}, student_id={student_id}, group_id={payload.group_id}",
        )
        self.db.commit()
        student = self._get_student_user(student_id)
        group_map = {g.id: g.name for g in self._list_groups(class_id)}
        return self._to_student_item(student, enrollment, group_map)

    def unbind_parent(
        self,
        class_id: int,
        student_id: int,
        parent_id: int,
        teacher_id: int,
    ) -> None:
        self._ensure_student_in_class(class_id, student_id, teacher_id)
        binding = (
            self.db.query(ParentStudentBinding)
            .filter(
                ParentStudentBinding.student_id == student_id,
                ParentStudentBinding.parent_id == parent_id,
            )
            .first()
        )
        if binding is None:
            raise AppException(404, "绑定关系不存在", status_code=404)
        self.db.delete(binding)
        self._log(
            teacher_id,
            "unbind_parent",
            f"class_id={class_id}, student_id={student_id}, parent_id={parent_id}",
        )
        self.db.commit()

    def _active_enrollment(self, class_id: int, student_id: int) -> ClassEnrollment | None:
        return (
            self.db.query(ClassEnrollment)
            .filter(
                ClassEnrollment.class_id == class_id,
                ClassEnrollment.student_id == student_id,
                ClassEnrollment.deleted_at.is_(None),
            )
            .first()
        )

    def _enroll_or_reactivate(self, class_id: int, student_id: int) -> ClassEnrollment:
        """加入班级；若曾软删除移除则恢复原记录，避免唯一约束冲突。"""
        removed = (
            self.db.query(ClassEnrollment)
            .filter(
                ClassEnrollment.class_id == class_id,
                ClassEnrollment.student_id == student_id,
                ClassEnrollment.deleted_at.isnot(None),
            )
            .first()
        )
        if removed is not None:
            removed.deleted_at = None
            removed.group_id = None
            self.db.flush()
            return removed

        enrollment = ClassEnrollment(class_id=class_id, student_id=student_id)
        self.db.add(enrollment)
        self.db.flush()
        return enrollment

    def _ensure_student_in_class(self, class_id: int, student_id: int, teacher_id: int) -> ClassEnrollment:
        self._get_owned_class(class_id, teacher_id)
        enrollment = self._active_enrollment(class_id, student_id)
        if enrollment is None:
            raise AppException(404, "学生不在该班级中", status_code=404)
        return enrollment

    def _get_student_user(self, student_id: int) -> User:
        student = (
            self.db.query(User)
            .filter(
                User.id == student_id,
                User.role == UserRole.STUDENT,
                User.deleted_at.is_(None),
            )
            .first()
        )
        if student is None:
            raise AppException(404, "学生不存在", status_code=404)
        return student

    def _list_groups(self, class_id: int) -> list[StudentGroup]:
        return (
            self.db.query(StudentGroup)
            .filter(StudentGroup.class_id == class_id, StudentGroup.deleted_at.is_(None))
            .order_by(StudentGroup.id.asc())
            .all()
        )

    def _group_student_count(self, group_id: int) -> int:
        return (
            self.db.query(ClassEnrollment)
            .filter(ClassEnrollment.group_id == group_id, ClassEnrollment.deleted_at.is_(None))
            .count()
        )

    def _groups_with_counts(self, class_id: int) -> list[StudentGroupItem]:
        groups = self._list_groups(class_id)
        return [
            StudentGroupItem(id=group.id, name=group.name, student_count=self._group_student_count(group.id))
            for group in groups
        ]

    def _get_owned_group(self, class_id: int, group_id: int, teacher_id: int) -> StudentGroup:
        self._get_owned_class(class_id, teacher_id)
        group = (
            self.db.query(StudentGroup)
            .filter(
                StudentGroup.id == group_id,
                StudentGroup.class_id == class_id,
                StudentGroup.deleted_at.is_(None),
            )
            .first()
        )
        if group is None:
            raise AppException(404, "分组不存在", status_code=404)
        return group

    def _generate_account(self) -> str:
        count = self.db.query(func.count(User.id)).filter(User.role == UserRole.STUDENT).scalar() or 0
        year = datetime.now().year
        return f"stu{year}{count + 1:04d}"

    def _to_list_item(self, teaching_class: TeachingClass) -> ClassListItem:
        enrollments = (
            self.db.query(ClassEnrollment, User)
            .join(User, User.id == ClassEnrollment.student_id)
            .filter(
                ClassEnrollment.class_id == teaching_class.id,
                ClassEnrollment.deleted_at.is_(None),
                User.deleted_at.is_(None),
            )
            .order_by(User.id.asc())
            .all()
        )
        students = []
        for _, user in enrollments:
            identity = student_identity_fields(user)
            students.append(
                StudentBrief(
                    id=user.id,
                    account=identity["account"] or user.account,
                    real_name=identity["real_name"],
                    nickname=identity["nickname"],
                    display_name=identity["display_name"] or user.account,
                )
            )
        return ClassListItem(
            id=teaching_class.id,
            name=teaching_class.name,
            course_type=teaching_class.course_type,
            schedule=teaching_class.schedule,
            expected_student_count=teaching_class.expected_student_count,
            lesson_count=teaching_class.lesson_count,
            description=teaching_class.description,
            student_count=len(students),
            students_preview=students[:5],
        )

    def _to_student_item(
        self,
        user: User,
        enrollment: ClassEnrollment | None = None,
        group_map: dict[int, str] | None = None,
    ) -> ClassStudentItem:
        group_id = enrollment.group_id if enrollment else None
        group_name = group_map.get(group_id) if group_id and group_map else None
        identity = student_identity_fields(user)
        return ClassStudentItem(
            id=user.id,
            account=identity["account"] or user.account,
            real_name=identity["real_name"],
            nickname=identity["nickname"],
            display_name=identity["display_name"] or user.account,
            completed_problems=count_student_completed_problems(self.db, user.id),
            accuracy=student_regular_accuracy(self.db, user.id),
            last_active=None,
            is_active=user.is_active,
            group_id=group_id,
            group_name=group_name,
        )

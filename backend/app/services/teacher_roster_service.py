from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.security import hash_password
from app.models.audit import OperationLog
from app.models.class_model import ClassEnrollment, TeachingClass
from app.models.user import User, UserRole
from app.schemas.roster_schema import (
    RosterBatchCreateResponse,
    RosterBatchCreateResultItem,
    RosterListResponse,
    RosterStudentItem,
    RosterStudentUpdateRequest,
)

from app.utils.student_account import DEFAULT_STUDENT_PASSWORD
from app.utils.student_identity import student_identity_fields


class TeacherRosterService:
    def __init__(self, db: Session):
        self.db = db

    def _log(self, user_id: int, action: str, detail: str | None = None) -> None:
        self.db.add(OperationLog(user_id=user_id, action=action, resource="teacher_roster", detail=detail))

    def list_roster(
        self,
        teacher_id: int,
        keyword: str | None = None,
        class_id: int | None = None,
    ) -> RosterListResponse:
        if class_id is not None:
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
                raise AppException(404, "班级不存在", status_code=404)
            query = (
                self.db.query(User)
                .join(ClassEnrollment, ClassEnrollment.student_id == User.id)
                .filter(
                    ClassEnrollment.class_id == class_id,
                    ClassEnrollment.deleted_at.is_(None),
                    User.role == UserRole.STUDENT,
                    User.deleted_at.is_(None),
                )
            )
        else:
            query = self.db.query(User).filter(
                User.role == UserRole.STUDENT,
                User.created_by_teacher_id == teacher_id,
                User.deleted_at.is_(None),
            )
        if keyword:
            like = f"%{keyword.strip()}%"
            query = query.filter(
                (User.display_name.ilike(like))
                | (User.nickname.ilike(like))
                | (User.account.ilike(like))
            )
        students = query.order_by(User.account.asc()).all()
        items: list[RosterStudentItem] = []
        for student in students:
            class_names = self._student_class_names(student.id, teacher_id)
            identity = student_identity_fields(student)
            items.append(
                RosterStudentItem(
                    id=student.id,
                    account=identity["account"] or student.account,
                    real_name=identity["real_name"],
                    nickname=identity["nickname"],
                    display_name=identity["display_name"] or student.account,
                    class_names=class_names,
                )
            )
        return RosterListResponse(items=items, total=len(items))

    def update_student(
        self,
        teacher_id: int,
        student_id: int,
        payload: RosterStudentUpdateRequest,
    ) -> RosterStudentItem:
        self._get_manageable_roster_student(student_id, teacher_id)
        raise AppException(
            403,
            "真实姓名请由管理员在用户管理中修改；昵称由学生在个人中心修改",
            status_code=403,
        )

    def batch_create(self, teacher_id: int, names: list[str], year: int) -> RosterBatchCreateResponse:
        cleaned = [n.strip() for n in names if n.strip()]
        if not cleaned:
            raise AppException(400, "请至少填写一个有效姓名")
        if len(cleaned) > 100:
            raise AppException(400, "单次最多添加 100 名学生")

        prefix = f"stu{year}"
        seq = self._next_sequence(prefix)
        created: list[RosterBatchCreateResultItem] = []

        for name in cleaned:
            account = f"{prefix}{seq:03d}"
            seq += 1
            while self._account_taken(account):
                account = f"{prefix}{seq:03d}"
                seq += 1

            student = User(
                account=account,
                password_hash=hash_password(DEFAULT_STUDENT_PASSWORD),
                role=UserRole.STUDENT,
                display_name=name,
                student_no=str(year) + account[-3:],
                created_by_teacher_id=teacher_id,
                created_by=teacher_id,
                updated_by=teacher_id,
            )
            self.db.add(student)
            self.db.flush()
            created.append(
                RosterBatchCreateResultItem(
                    display_name=name,
                    account=account,
                    student_id=student.id,
                )
            )

        self._log(teacher_id, "roster_batch_create", f"count={len(created)}, year={year}")
        self.db.commit()
        return RosterBatchCreateResponse(created=created, default_password=DEFAULT_STUDENT_PASSWORD)

    def _get_manageable_roster_student(self, student_id: int, teacher_id: int) -> User:
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
        if student.created_by_teacher_id == teacher_id:
            return student
        if self._student_in_teacher_class(student_id, teacher_id):
            return student
        raise AppException(403, "无权修改该学生信息", status_code=403)

    def _student_in_teacher_class(self, student_id: int, teacher_id: int) -> bool:
        row = (
            self.db.query(ClassEnrollment.id)
            .join(TeachingClass, TeachingClass.id == ClassEnrollment.class_id)
            .filter(
                ClassEnrollment.student_id == student_id,
                ClassEnrollment.deleted_at.is_(None),
                TeachingClass.teacher_id == teacher_id,
                TeachingClass.deleted_at.is_(None),
            )
            .first()
        )
        return row is not None

    def _next_sequence(self, prefix: str) -> int:
        rows = (
            self.db.query(User.account)
            .filter(
                User.role == UserRole.STUDENT,
                User.account.like(f"{prefix}%"),
                User.deleted_at.is_(None),
            )
            .all()
        )
        max_seq = 0
        for (account,) in rows:
            suffix = account[len(prefix) :]
            if suffix.isdigit() and len(suffix) == 3:
                max_seq = max(max_seq, int(suffix))
        return max_seq + 1

    def _account_taken(self, account: str) -> bool:
        return (
            self.db.query(User.id)
            .filter(User.account == account, User.role == UserRole.STUDENT, User.deleted_at.is_(None))
            .first()
            is not None
        )

    def _student_class_names(self, student_id: int, teacher_id: int) -> list[str]:
        rows = (
            self.db.query(TeachingClass.name)
            .join(ClassEnrollment, ClassEnrollment.class_id == TeachingClass.id)
            .filter(
                ClassEnrollment.student_id == student_id,
                ClassEnrollment.deleted_at.is_(None),
                TeachingClass.teacher_id == teacher_id,
                TeachingClass.deleted_at.is_(None),
            )
            .all()
        )
        return [name for (name,) in rows]

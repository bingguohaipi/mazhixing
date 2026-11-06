"""Shared rules for who may view or submit on a problem."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.class_model import ClassEnrollment, TeachingClass
from app.models.homework import Homework, HomeworkClass, HomeworkProblem
from app.models.problem import Problem, ProblemScope, PublicPublishStatus
from app.models.submission import Submission
from app.models.user import User, UserRole
from app.services.homework_service import HomeworkService


class ProblemAccessHelper:
    def __init__(self, db: Session):
        self.db = db

    def student_teacher_ids(self, student_id: int) -> list[int]:
        class_ids = [
            row.class_id
            for row in self.db.query(ClassEnrollment)
            .filter(ClassEnrollment.student_id == student_id, ClassEnrollment.deleted_at.is_(None))
            .all()
        ]
        if not class_ids:
            return []
        teachers = (
            self.db.query(TeachingClass.teacher_id)
            .filter(TeachingClass.id.in_(class_ids), TeachingClass.deleted_at.is_(None))
            .distinct()
            .all()
        )
        return [row.teacher_id for row in teachers]

    def student_has_submission(self, student_id: int, problem_id: int) -> bool:
        row = (
            self.db.query(Submission.id)
            .filter(Submission.user_id == student_id, Submission.problem_id == problem_id)
            .first()
        )
        return row is not None

    def student_homework_has_problem(self, student_id: int, problem_id: int) -> bool:
        return self._student_in_homework_with_problem(student_id, problem_id)

    def student_can_access_problem(self, student_id: int, problem: Problem) -> bool:
        if problem.deleted_at is not None:
            return False
        if problem.scope == ProblemScope.PUBLIC:
            if problem.publish_status == PublicPublishStatus.PUBLISHED:
                return True
            if problem.publish_status == PublicPublishStatus.ARCHIVED:
                return self.student_has_submission(student_id, problem.id) or self._student_in_homework_with_problem(
                    student_id, problem.id
                )
            return False
        teacher_ids = self.student_teacher_ids(student_id)
        if problem.teacher_id not in teacher_ids:
            return False
        return self._student_in_homework_with_problem(student_id, problem.id) or self.student_has_submission(
            student_id, problem.id
        )

    def _student_in_homework_with_problem(self, student_id: int, problem_id: int) -> bool:
        class_ids = [
            row.class_id
            for row in self.db.query(ClassEnrollment)
            .filter(ClassEnrollment.student_id == student_id, ClassEnrollment.deleted_at.is_(None))
            .all()
        ]
        if not class_ids:
            return False
        hw_service = HomeworkService(self.db)
        homeworks = (
            self.db.query(Homework)
            .join(HomeworkClass, HomeworkClass.homework_id == Homework.id)
            .filter(
                HomeworkClass.class_id.in_(class_ids),
                Homework.deleted_at.is_(None),
            )
            .all()
        )
        for hw in homeworks:
            if not hw_service._is_visible_to_student(hw, student_id, class_ids):
                continue
            link = (
                self.db.query(HomeworkProblem)
                .filter(HomeworkProblem.homework_id == hw.id, HomeworkProblem.problem_id == problem_id)
                .first()
            )
            if link is not None:
                return True
        return False

    def teacher_can_preview_public_problem(self, problem: Problem) -> bool:
        if problem.deleted_at is not None:
            return False
        return self.is_public_catalog_problem(problem)

    def teacher_can_preview_problem(self, teacher_id: int, problem: Problem) -> bool:
        """题库当前上架版 + 本班作业/提交曾用过的题目（含已归档旧版）均可预览。"""
        if problem.deleted_at is not None:
            return False
        if self.teacher_can_preview_public_problem(problem):
            return True
        if problem.scope == ProblemScope.PRIVATE and problem.teacher_id == teacher_id:
            return True
        return self._teacher_class_used_problem(teacher_id, problem.id)

    def _teacher_class_used_problem(self, teacher_id: int, problem_id: int) -> bool:
        class_ids = [
            row.id
            for row in self.db.query(TeachingClass.id)
            .filter(TeachingClass.teacher_id == teacher_id, TeachingClass.deleted_at.is_(None))
            .all()
        ]
        if not class_ids:
            return False
        student_ids = [
            row.student_id
            for row in self.db.query(ClassEnrollment.student_id)
            .filter(ClassEnrollment.class_id.in_(class_ids), ClassEnrollment.deleted_at.is_(None))
            .all()
        ]
        if student_ids:
            submitted = (
                self.db.query(Submission.id)
                .filter(Submission.user_id.in_(student_ids), Submission.problem_id == problem_id)
                .first()
            )
            if submitted is not None:
                return True
        assigned = (
            self.db.query(HomeworkProblem.id)
            .join(Homework, Homework.id == HomeworkProblem.homework_id)
            .filter(
                Homework.teacher_id == teacher_id,
                Homework.deleted_at.is_(None),
                HomeworkProblem.problem_id == problem_id,
            )
            .first()
        )
        return assigned is not None

    def teacher_can_use_in_homework(self, teacher_id: int, problem: Problem) -> bool:
        if problem.deleted_at is not None:
            return False
        if self.is_public_catalog_problem(problem):
            return True
        return problem.scope == ProblemScope.PRIVATE and problem.teacher_id == teacher_id

    def _published_catalog_version_subquery(self):
        """Each group exposes the highest *published* version (draft newer versions do not hide the group)."""
        return (
            self.db.query(
                Problem.public_group_id.label("group_id"),
                func.max(Problem.version).label("visible_version"),
            )
            .filter(
                Problem.scope == ProblemScope.PUBLIC,
                Problem.deleted_at.is_(None),
                Problem.public_group_id.isnot(None),
                Problem.publish_status == PublicPublishStatus.PUBLISHED,
            )
            .group_by(Problem.public_group_id)
            .subquery()
        )

    def visible_published_version(self, public_group_id: int) -> int | None:
        version = (
            self.db.query(func.max(Problem.version))
            .filter(
                Problem.public_group_id == public_group_id,
                Problem.deleted_at.is_(None),
                Problem.scope == ProblemScope.PUBLIC,
                Problem.publish_status == PublicPublishStatus.PUBLISHED,
            )
            .scalar()
        )
        return int(version) if version is not None else None

    def list_public_catalog_query(self):
        visible = self._published_catalog_version_subquery()
        return (
            self.db.query(Problem)
            .join(
                visible,
                (Problem.public_group_id == visible.c.group_id)
                & (Problem.version == visible.c.visible_version),
            )
            .filter(
                Problem.scope == ProblemScope.PUBLIC,
                Problem.publish_status == PublicPublishStatus.PUBLISHED,
                Problem.deleted_at.is_(None),
            )
        )

    def is_public_catalog_problem(self, problem: Problem) -> bool:
        if (
            problem.deleted_at is not None
            or problem.scope != ProblemScope.PUBLIC
            or problem.publish_status != PublicPublishStatus.PUBLISHED
            or problem.public_group_id is None
        ):
            return False
        visible = self.visible_published_version(problem.public_group_id)
        return visible is not None and problem.version == visible

    def default_suggestion_recipient_for_problem(self, viewer: User, problem: Problem) -> int | None:
        if problem.scope == ProblemScope.PUBLIC:
            admin = (
                self.db.query(User)
                .filter(User.role == UserRole.ADMIN, User.is_active.is_(True), User.deleted_at.is_(None))
                .order_by(User.id.asc())
                .first()
            )
            return admin.id if admin else None
        if viewer.role == UserRole.STUDENT:
            return problem.teacher_id
        return problem.teacher_id

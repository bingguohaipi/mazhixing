"""Parent-facing learning analytics for bound children."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.forbidden import raise_forbidden
from app.models.audit import ParentStudentBinding
from app.models.class_model import ClassEnrollment, TeachingClass
from app.models.homework import Homework, HomeworkClass
from app.models.problem import Problem
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User, UserRole
from app.schemas.parent_schema import (
    ParentChildBrief,
    ParentHomeworkItem,
    ParentKnowledgePointStat,
    ParentPeriod,
    ParentStudentOverview,
    ParentTrendItem,
    ParentWrongBookItem,
    ParentWrongBookListResponse,
    ParentWrongProblemItem,
)
from app.schemas.wrong_book_schema import WrongReviewStatus, WrongSortBy
from app.services.wrong_book_service import WrongBookService
from app.services.homework_service import HomeworkService
from app.services.stats_utils import (
    VALID_SUBMISSION_STATUSES,
    WRONG_SUBMISSION_STATUSES,
    apply_regular_submission_filters,
    count_student_completed_problems,
    student_regular_accuracy,
)


class ParentService:
    def __init__(self, db: Session):
        self.db = db
        self.homework_service = HomeworkService(db)

    def list_children(self, parent_id: int) -> list[ParentChildBrief]:
        bindings = (
            self.db.query(ParentStudentBinding, User)
            .join(User, User.id == ParentStudentBinding.student_id)
            .filter(
                ParentStudentBinding.parent_id == parent_id,
                User.deleted_at.is_(None),
                User.role == UserRole.STUDENT,
            )
            .order_by(User.id.asc())
            .all()
        )
        return [
            ParentChildBrief(
                student_id=student.id,
                display_name=student.display_name or student.account,
                student_no=student.student_no,
                class_names=self._student_class_names(student.id),
            )
            for _, student in bindings
        ]

    def get_student_overview(
        self,
        parent_id: int,
        student_id: int,
        period: ParentPeriod = "7",
    ) -> ParentStudentOverview:
        self._ensure_bound(parent_id, student_id)
        student = self._get_student(student_id)
        period_days = int(period)
        period_start = datetime.now(timezone.utc) - timedelta(days=period_days)

        submissions = (
            apply_regular_submission_filters(
                self.db.query(Submission, Problem).join(Problem, Problem.id == Submission.problem_id)
            )
            .filter(Submission.user_id == student_id, Submission.created_at >= period_start)
            .order_by(Submission.created_at.desc())
            .all()
        )

        total_submissions = len(submissions)
        ac_count = sum(1 for submission, _ in submissions if submission.status == SubmissionStatus.AC)
        wrong_count = sum(
            1 for submission, _ in submissions if submission.status in WRONG_SUBMISSION_STATUSES
        )
        accuracy = round(ac_count / total_submissions * 100, 1) if total_submissions else 0.0

        knowledge_points = self._knowledge_stats(submissions)
        learning_trend = self._learning_trend(student_id, period_days)
        top_wrong = self._top_wrong_problems(student_id, period_start)
        recent_homeworks = self._recent_homeworks(student_id)

        return ParentStudentOverview(
            student_id=student.id,
            display_name=student.display_name or student.account,
            student_no=student.student_no,
            class_names=self._student_class_names(student.id),
            period_days=period_days,
            total_submissions=total_submissions,
            accuracy=accuracy,
            completed_problems=count_student_completed_problems(self.db, student_id),
            wrong_count=wrong_count,
            knowledge_points=knowledge_points,
            learning_trend=learning_trend,
            top_wrong_problems=top_wrong[:3],
            recent_homeworks=recent_homeworks,
        )

    def get_student_wrong_book(
        self,
        parent_id: int,
        student_id: int,
        review_status: WrongReviewStatus | None = None,
        knowledge_point: str | None = None,
        sort_by: WrongSortBy = "error_count",
    ) -> ParentWrongBookListResponse:
        self._ensure_bound(parent_id, student_id)
        result = WrongBookService(self.db).list_wrong_book(
            student_id,
            review_status=review_status,
            knowledge_point=knowledge_point,
            sort_by=sort_by,
        )
        items = [
            ParentWrongBookItem(
                problem_id=item.problem_id,
                title=item.title,
                difficulty=item.difficulty,
                knowledge_point=item.knowledge_point,
                review_status=item.review_status,
                error_count=item.error_count,
                last_error_at=item.last_error_at,
                last_status=item.last_status,
                ai_analysis=item.ai_analysis,
                error_reason=item.error_reason,
            )
            for item in result.items
        ]
        return ParentWrongBookListResponse(summary=result.summary, items=items)

    def _ensure_bound(self, parent_id: int, student_id: int) -> None:
        binding = (
            self.db.query(ParentStudentBinding)
            .filter(
                ParentStudentBinding.parent_id == parent_id,
                ParentStudentBinding.student_id == student_id,
            )
            .first()
        )
        if binding is None:
            raise_forbidden(self.db, parent_id, "parent", f"student_id={student_id}")

    def _get_student(self, student_id: int) -> User:
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

    def _student_class_names(self, student_id: int) -> list[str]:
        rows = (
            self.db.query(TeachingClass)
            .join(ClassEnrollment, ClassEnrollment.class_id == TeachingClass.id)
            .filter(
                ClassEnrollment.student_id == student_id,
                ClassEnrollment.deleted_at.is_(None),
                TeachingClass.deleted_at.is_(None),
            )
            .all()
        )
        return [item.name for item in rows]

    @staticmethod
    def _knowledge_stats(
        rows: list[tuple[Submission, Problem]],
    ) -> list[ParentKnowledgePointStat]:
        grouped: dict[str, dict[str, int]] = defaultdict(lambda: {"attempted": 0, "ac": 0})
        seen: set[tuple[int, int | None]] = set()
        for submission, problem in rows:
            name = problem.knowledge_point or "未分类"
            dedupe_key = (problem.id, submission.homework_id)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            grouped[name]["attempted"] += 1
            if submission.status == SubmissionStatus.AC:
                grouped[name]["ac"] += 1

        stats = [
            ParentKnowledgePointStat(
                name=name,
                mastery_rate=round(values["ac"] / values["attempted"] * 100, 1)
                if values["attempted"]
                else 0.0,
            )
            for name, values in grouped.items()
        ]
        stats.sort(key=lambda item: item.mastery_rate)
        return stats[:8]

    def _learning_trend(self, student_id: int, period_days: int) -> list[ParentTrendItem]:
        period_start = datetime.now(timezone.utc) - timedelta(days=period_days)
        rows = (
            apply_regular_submission_filters(self.db.query(Submission))
            .filter(Submission.user_id == student_id, Submission.created_at >= period_start)
            .all()
        )
        counts: dict[str, int] = defaultdict(int)
        for submission in rows:
            counts[submission.created_at.strftime("%Y-%m-%d")] += 1

        labels = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        items: list[ParentTrendItem] = []
        today = datetime.now(timezone.utc).date()
        span = min(period_days, 30)
        for offset in range(span - 1, -1, -1):
            day = today - timedelta(days=offset)
            key = day.strftime("%Y-%m-%d")
            label = f"{day.month}/{day.day}" if span > 7 else labels[day.weekday()]
            items.append(ParentTrendItem(date=key, label=label, count=counts.get(key, 0)))
        return items

    def _top_wrong_problems(
        self,
        student_id: int,
        period_start: datetime,
    ) -> list[ParentWrongProblemItem]:
        rows = (
            apply_regular_submission_filters(
                self.db.query(Submission, Problem).join(Problem, Problem.id == Submission.problem_id)
            )
            .filter(
                Submission.user_id == student_id,
                Submission.created_at >= period_start,
                Submission.status.in_(WRONG_SUBMISSION_STATUSES),
            )
            .all()
        )
        wrong_counts: dict[int, dict[str, object]] = {}
        for _, problem in rows:
            bucket = wrong_counts.setdefault(
                problem.id,
                {"title": problem.title, "knowledge_point": problem.knowledge_point, "count": 0},
            )
            bucket["count"] = int(bucket["count"]) + 1

        result = [
            ParentWrongProblemItem(
                problem_id=problem_id,
                title=str(data["title"]),
                knowledge_point=data["knowledge_point"],  # type: ignore[arg-type]
                wrong_count=int(data["count"]),
            )
            for problem_id, data in wrong_counts.items()
        ]
        result.sort(key=lambda item: item.wrong_count, reverse=True)
        return result

    def _recent_homeworks(self, student_id: int) -> list[ParentHomeworkItem]:
        class_ids = [
            row.class_id
            for row in self.db.query(ClassEnrollment.class_id)
            .filter(ClassEnrollment.student_id == student_id, ClassEnrollment.deleted_at.is_(None))
            .all()
        ]
        if not class_ids:
            return []

        homeworks = (
            self.db.query(Homework)
            .join(HomeworkClass, HomeworkClass.homework_id == Homework.id)
            .filter(
                HomeworkClass.class_id.in_(class_ids),
                Homework.deleted_at.is_(None),
                Homework.withdrawn_at.is_(None),
            )
            .order_by(Homework.end_time.desc())
            .limit(5)
            .all()
        )

        items: list[ParentHomeworkItem] = []
        for homework in homeworks:
            if homework.student_links and not any(
                link.student_id == student_id for link in homework.student_links
            ):
                continue
            progress = self.homework_service._student_progress(student_id, homework)
            has_regular = (
                apply_regular_submission_filters(self.db.query(Submission))
                .filter(Submission.user_id == student_id, Submission.homework_id == homework.id)
                .count()
                > 0
            )
            has_late_only = (
                not has_regular
                and self.db.query(Submission)
                .filter(
                    Submission.user_id == student_id,
                    Submission.homework_id == homework.id,
                    Submission.is_late.is_(True),
                    Submission.status.in_(VALID_SUBMISSION_STATUSES),
                )
                .count()
                > 0
            )
            items.append(
                ParentHomeworkItem(
                    homework_id=homework.id,
                    title=homework.title,
                    status=self.homework_service.compute_status(homework),
                    progress=progress,
                    end_time=homework.end_time,
                    is_late_only=has_late_only,
                )
            )
        return items

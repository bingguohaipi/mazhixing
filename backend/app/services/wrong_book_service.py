"""Student wrong-question notebook aggregation."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.class_model import ClassEnrollment
from app.models.problem import Problem
from app.models.submission import Submission, SubmissionStatus
from app.models.wrong_book import WrongBookDismissal
from app.schemas.wrong_book_schema import (
    WrongBookItem,
    WrongBookListResponse,
    WrongBookSummary,
    WrongReviewStatus,
    WrongSortBy,
)
from app.services.ai_analysis_format import unpack_ai_analysis
from app.services.stats_utils import WRONG_SUBMISSION_STATUSES, apply_regular_submission_filters

WRONG_STATUSES = WRONG_SUBMISSION_STATUSES


class WrongBookService:
    def __init__(self, db: Session):
        self.db = db

    def list_wrong_book(
        self,
        student_id: int,
        review_status: WrongReviewStatus | None = None,
        knowledge_point: str | None = None,
        sort_by: WrongSortBy = "error_count",
    ) -> WrongBookListResponse:
        all_items = self._build_items(student_id)
        summary = WrongBookSummary(
            pending_count=sum(1 for item in all_items if item.review_status == "pending"),
            reviewing_count=sum(1 for item in all_items if item.review_status == "reviewing"),
            mastered_count=sum(1 for item in all_items if item.review_status == "mastered"),
        )

        items = all_items
        if review_status:
            items = [item for item in items if item.review_status == review_status]
        if knowledge_point:
            key = knowledge_point.strip()
            items = [item for item in items if (item.knowledge_point or "") == key]

        items = self._sort_items(items, sort_by)
        return WrongBookListResponse(summary=summary, items=items)

    def _build_items(self, student_id: int) -> list[WrongBookItem]:
        dismissed_ids = self._dismissed_problem_ids(student_id)
        problem_ids = self._wrong_problem_ids(student_id, dismissed_ids)
        if not problem_ids:
            return []

        problems = {
            row.id: row
            for row in self.db.query(Problem)
            .filter(Problem.id.in_(problem_ids), Problem.deleted_at.is_(None))
            .all()
        }

        items: list[WrongBookItem] = []
        for problem_id in problem_ids:
            problem = problems.get(problem_id)
            if problem is None:
                continue

            submissions = self._problem_submissions(student_id, problem_id)
            if not submissions:
                continue

            status = self._compute_review_status(submissions)
            wrong_subs = [sub for sub in submissions if sub.status in WRONG_STATUSES]
            if not wrong_subs:
                continue

            latest_wrong = max(wrong_subs, key=lambda item: item.created_at)
            ai_text, _ = unpack_ai_analysis(latest_wrong.ai_analysis)
            items.append(
                WrongBookItem(
                    problem_id=problem.id,
                    title=problem.title,
                    difficulty=problem.difficulty.value,
                    knowledge_point=problem.knowledge_point,
                    review_status=status,
                    error_count=len(wrong_subs),
                    last_error_at=latest_wrong.created_at,
                    last_submission_id=latest_wrong.id,
                    last_status=latest_wrong.status.value,
                    last_code=latest_wrong.code,
                    ai_analysis=ai_text or None,
                    error_reason=self._error_reason(latest_wrong),
                )
            )
        return items

    def clear_wrong_book(self, student_id: int, problem_id: int | None = None) -> int:
        if problem_id is not None:
            if problem_id in self._dismissed_problem_ids(student_id):
                return 0
            self.db.add(
                WrongBookDismissal(
                    student_id=student_id,
                    problem_id=problem_id,
                    dismissed_at=datetime.now(timezone.utc),
                )
            )
            self.db.commit()
            return 1

        problem_ids = self._wrong_problem_ids(student_id, self._dismissed_problem_ids(student_id))
        now = datetime.now(timezone.utc)
        count = 0
        for pid in problem_ids:
            self.db.add(
                WrongBookDismissal(
                    student_id=student_id,
                    problem_id=pid,
                    dismissed_at=now,
                )
            )
            count += 1
        self.db.commit()
        return count

    def pending_count(self, student_id: int) -> int:
        dismissed_ids = self._dismissed_problem_ids(student_id)
        count = 0
        for problem_id in self._wrong_problem_ids(student_id, dismissed_ids):
            submissions = self._problem_submissions(student_id, problem_id)
            if self._compute_review_status(submissions) == "pending":
                count += 1
        return count

    def _dismissed_problem_ids(self, student_id: int) -> set[int]:
        rows = (
            self.db.query(WrongBookDismissal.problem_id)
            .filter(WrongBookDismissal.student_id == student_id)
            .all()
        )
        return {row.problem_id for row in rows}

    def _wrong_problem_ids(self, student_id: int, dismissed_ids: set[int]) -> list[int]:
        query = (
            apply_regular_submission_filters(self.db.query(Submission.problem_id))
            .filter(Submission.user_id == student_id, Submission.status.in_(WRONG_STATUSES))
            .distinct()
        )
        if dismissed_ids:
            query = query.filter(~Submission.problem_id.in_(dismissed_ids))
        rows = query.all()
        return [row.problem_id for row in rows]

    def _problem_submissions(self, student_id: int, problem_id: int) -> list[Submission]:
        return (
            apply_regular_submission_filters(
                self.db.query(Submission).filter(
                    Submission.user_id == student_id,
                    Submission.problem_id == problem_id,
                )
            )
            .order_by(Submission.created_at.asc(), Submission.id.asc())
            .all()
        )

    @staticmethod
    def _compute_review_status(submissions: list[Submission]) -> WrongReviewStatus:
        if not submissions:
            return "pending"

        last_wrong_index = -1
        for index, submission in enumerate(submissions):
            if submission.status in WRONG_STATUSES:
                last_wrong_index = index

        if last_wrong_index < 0:
            return "mastered"

        after_wrong = submissions[last_wrong_index + 1 :]
        consecutive_ac = 0
        for submission in after_wrong:
            if submission.status == SubmissionStatus.AC:
                consecutive_ac += 1
            else:
                break

        if consecutive_ac >= 2:
            return "mastered"
        if consecutive_ac == 1:
            return "reviewing"
        return "pending"

    @staticmethod
    def _error_reason(submission: Submission) -> str | None:
        if submission.status == SubmissionStatus.WA:
            return "答案错误，输出与预期不符"
        if submission.status == SubmissionStatus.TLE:
            return "代码运行超时，请优化逻辑后重试"
        if submission.status == SubmissionStatus.RE:
            return submission.error_message or "运行异常"
        return None

    @staticmethod
    def _sort_items(items: list[WrongBookItem], sort_by: WrongSortBy) -> list[WrongBookItem]:
        difficulty_order = {"入门": 0, "简单": 1, "中等": 2, "困难": 3}
        if sort_by == "last_error":
            return sorted(items, key=lambda item: item.last_error_at, reverse=True)
        if sort_by == "difficulty":
            return sorted(
                items,
                key=lambda item: difficulty_order.get(item.difficulty, 99),
            )
        return sorted(items, key=lambda item: item.error_count, reverse=True)

    def assert_student_in_class(self, student_id: int) -> None:
        enrolled = (
            self.db.query(ClassEnrollment)
            .filter(ClassEnrollment.student_id == student_id, ClassEnrollment.deleted_at.is_(None))
            .first()
        )
        if enrolled is None:
            raise AppException(400, "尚未加入班级，无法使用错题本")

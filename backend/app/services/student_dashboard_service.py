"""Student dashboard overview statistics."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.class_model import ClassEnrollment
from app.models.problem import Problem
from app.models.submission import Submission, SubmissionStatus
from app.schemas.student_dashboard_schema import KnowledgeProgressItem, StudentDashboardOverview
from app.services.leaderboard_service import LeaderboardService
from app.services.stats_utils import apply_regular_submission_filters, student_regular_accuracy
from app.services.wrong_book_service import WrongBookService


class StudentDashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_overview(self, student_id: int) -> StudentDashboardOverview:
        now = datetime.now(timezone.utc)
        week_start = now - timedelta(days=7)

        completed = self._completed_problems(student_id)
        week_new = self._week_new_problems(student_id, week_start)
        accuracy = student_regular_accuracy(self.db, student_id)

        class_id = LeaderboardService(self.db).get_student_primary_class_id(student_id)
        class_rank: int | None = None
        class_student_count = 0
        class_avg_accuracy = 0.0
        leaderboard_preview = []

        if class_id is not None:
            leaderboard = LeaderboardService(self.db).get_class_leaderboard(
                class_id, student_id, "student"
            )
            class_rank = leaderboard.my_rank
            class_student_count = len(leaderboard.entries)
            leaderboard_preview = leaderboard.entries[:5]
            if leaderboard.entries:
                class_avg_accuracy = round(
                    sum(item.accuracy_rate for item in leaderboard.entries) / len(leaderboard.entries),
                    1,
                )

        wrong_pending = WrongBookService(self.db).pending_count(student_id)
        knowledge_progress = self._knowledge_progress(student_id)
        streak_days = self._streak_days(student_id, now)

        return StudentDashboardOverview(
            completed_problems=completed,
            week_new_problems=week_new,
            accuracy=accuracy,
            class_avg_accuracy=class_avg_accuracy,
            wrong_pending_count=wrong_pending,
            class_rank=class_rank,
            class_student_count=class_student_count,
            streak_days=streak_days,
            knowledge_progress=knowledge_progress,
            leaderboard_preview=leaderboard_preview,
        )

    def _completed_problems(self, student_id: int) -> int:
        rows = (
            apply_regular_submission_filters(self.db.query(Submission.problem_id))
            .filter(Submission.user_id == student_id, Submission.status == SubmissionStatus.AC)
            .distinct()
            .all()
        )
        return len(rows)

    def _week_new_problems(self, student_id: int, week_start: datetime) -> int:
        rows = (
            apply_regular_submission_filters(self.db.query(Submission.problem_id))
            .filter(
                Submission.user_id == student_id,
                Submission.status == SubmissionStatus.AC,
                Submission.created_at >= week_start,
            )
            .distinct()
            .all()
        )
        return len(rows)

    def _knowledge_progress(self, student_id: int) -> list[KnowledgeProgressItem]:
        submissions = (
            apply_regular_submission_filters(
                self.db.query(Submission).filter(Submission.user_id == student_id)
            )
            .all()
        )
        if not submissions:
            return []

        problem_ids = {sub.problem_id for sub in submissions}
        problems = {
            row.id: row
            for row in self.db.query(Problem).filter(Problem.id.in_(problem_ids)).all()
        }

        grouped: dict[str, dict[str, int]] = defaultdict(lambda: {"attempted": 0, "ac": 0})
        for submission in submissions:
            problem = problems.get(submission.problem_id)
            name = problem.knowledge_point if problem and problem.knowledge_point else "未分类"
            grouped[name]["attempted"] += 1
            if submission.status == SubmissionStatus.AC:
                grouped[name]["ac"] += 1

        items: list[KnowledgeProgressItem] = []
        for name, values in grouped.items():
            rate = round(values["ac"] / values["attempted"] * 100, 1) if values["attempted"] else 0.0
            if rate >= 80:
                status = "已掌握"
            elif rate >= 40:
                status = "学习中"
            else:
                status = "未开始"
            items.append(
                KnowledgeProgressItem(name=name, mastery_rate=rate, status=status)
            )

        return sorted(items, key=lambda item: -item.mastery_rate)[:8]

    def _streak_days(self, student_id: int, now: datetime) -> int:
        rows = (
            apply_regular_submission_filters(self.db.query(Submission.created_at))
            .filter(Submission.user_id == student_id)
            .order_by(Submission.created_at.desc())
            .all()
        )
        if not rows:
            return 0

        active_days = {row.created_at.date() for row in rows}
        streak = 0
        cursor = now.date()
        while cursor in active_days:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

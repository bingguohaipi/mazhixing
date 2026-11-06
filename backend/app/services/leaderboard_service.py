"""Class leaderboard: accuracy 70% + relative time 30%, excludes late submissions."""

from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.forbidden import raise_forbidden
from app.models.class_model import ClassEnrollment, TeachingClass
from app.models.leaderboard_snapshot import LeaderboardSnapshot
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User
from app.schemas.leaderboard_schema import (
    LeaderboardEntry,
    LeaderboardResponse,
    LeaderboardScoreBreakdown,
)
from app.services.stats_utils import VALID_SUBMISSION_STATUSES, apply_regular_submission_filters
from app.utils.user_display import public_display_name

BEIJING_TZ = ZoneInfo("Asia/Shanghai")


class LeaderboardService:
    ACCURACY_WEIGHT = 0.70
    TIME_WEIGHT = 0.30

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _student_name_fields(user: User | None) -> dict[str, str | None]:
        if user is None:
            return {"nickname": None, "real_name": None, "display_name": "未知"}
        nickname = (user.nickname or "").strip() or None
        real_name = (user.display_name or "").strip() or None
        return {
            "nickname": nickname,
            "real_name": real_name,
            "display_name": public_display_name(user),
        }

    @staticmethod
    def _today_beijing() -> date:
        return datetime.now(BEIJING_TZ).date()

    def has_any_snapshot(self) -> bool:
        return self.db.query(LeaderboardSnapshot.id).limit(1).first() is not None

    def refresh_all_snapshots(self) -> dict:
        class_ids = [
            row.id
            for row in self.db.query(TeachingClass.id)
            .filter(TeachingClass.deleted_at.is_(None))
            .all()
        ]
        snapshot_date = self._today_beijing()
        refreshed = 0
        for class_id in class_ids:
            self.refresh_class_snapshot(class_id, snapshot_date)
            refreshed += 1
        return {"class_count": refreshed, "snapshot_date": snapshot_date.isoformat()}

    def refresh_class_snapshot(self, class_id: int, snapshot_date: date | None = None) -> int:
        snapshot_date = snapshot_date or self._today_beijing()
        refreshed_at = datetime.now(timezone.utc)
        teaching_class = self._get_class_or_404(class_id)

        student_ids = [
            row.student_id
            for row in self.db.query(ClassEnrollment.student_id)
            .filter(ClassEnrollment.class_id == class_id, ClassEnrollment.deleted_at.is_(None))
            .all()
        ]

        self.db.query(LeaderboardSnapshot).filter(
            LeaderboardSnapshot.class_id == class_id,
            LeaderboardSnapshot.snapshot_date == snapshot_date,
        ).delete(synchronize_session=False)

        if not student_ids:
            self.db.commit()
            return 0

        students = {
            user.id: user
            for user in self.db.query(User).filter(User.id.in_(student_ids), User.deleted_at.is_(None)).all()
        }

        metrics = []
        for student_id in student_ids:
            score = self._compute_score(student_id)
            user = students.get(student_id)
            names = self._student_name_fields(user)
            metrics.append(
                {
                    "student_id": student_id,
                    "display_name": names["display_name"],
                    "nickname": names["nickname"],
                    "real_name": names["real_name"],
                    **score,
                }
            )

        metrics = [item for item in metrics if item["completed_problems"] > 0]
        self._apply_time_scores(metrics)
        metrics.sort(key=lambda item: (-item["total_score"], -item["accuracy_rate"], item["student_id"]))

        for rank, item in enumerate(metrics, start=1):
            breakdown: LeaderboardScoreBreakdown = item["breakdown"]
            self.db.add(
                LeaderboardSnapshot(
                    class_id=class_id,
                    snapshot_date=snapshot_date,
                    student_id=item["student_id"],
                    rank=rank,
                    display_name=item["display_name"],
                    completed_problems=item["completed_problems"],
                    accuracy_rate=item["accuracy_rate"],
                    accuracy_score=breakdown.accuracy_score,
                    time_score=breakdown.time_score,
                    total_score=breakdown.total_score,
                    avg_runtime_ms=breakdown.avg_runtime_ms,
                    refreshed_at=refreshed_at,
                )
            )

        self.db.commit()
        return len(metrics)

    def get_class_leaderboard(
        self,
        class_id: int,
        viewer_id: int,
        viewer_role: str,
        teacher_id: int | None = None,
    ) -> LeaderboardResponse:
        teaching_class = self._get_class_or_404(class_id)
        self._assert_viewer_access(class_id, viewer_id, viewer_role, teacher_id, teaching_class)

        latest = self._latest_snapshot_meta(class_id)
        if latest is None and not self.has_any_snapshot():
            self.refresh_class_snapshot(class_id)

        latest = self._latest_snapshot_meta(class_id)
        if latest is not None:
            return self._build_from_snapshot(
                class_id=class_id,
                class_name=teaching_class.name,
                snapshot_date=latest["snapshot_date"],
                refreshed_at=latest["refreshed_at"],
                viewer_id=viewer_id,
                viewer_role=viewer_role,
            )

        return self._build_live(
            class_id=class_id,
            class_name=teaching_class.name,
            viewer_id=viewer_id,
            viewer_role=viewer_role,
        )

    def get_student_primary_class_id(self, student_id: int) -> int | None:
        row = (
            self.db.query(ClassEnrollment.class_id)
            .filter(ClassEnrollment.student_id == student_id, ClassEnrollment.deleted_at.is_(None))
            .order_by(ClassEnrollment.id.asc())
            .first()
        )
        return row.class_id if row else None

    def _latest_snapshot_meta(self, class_id: int) -> dict | None:
        row = (
            self.db.query(
                LeaderboardSnapshot.snapshot_date,
                func.max(LeaderboardSnapshot.refreshed_at).label("refreshed_at"),
            )
            .filter(LeaderboardSnapshot.class_id == class_id)
            .group_by(LeaderboardSnapshot.snapshot_date)
            .order_by(LeaderboardSnapshot.snapshot_date.desc())
            .first()
        )
        if row is None:
            return None
        return {"snapshot_date": row.snapshot_date, "refreshed_at": row.refreshed_at}

    def _build_from_snapshot(
        self,
        class_id: int,
        class_name: str,
        snapshot_date: date,
        refreshed_at: datetime,
        viewer_id: int,
        viewer_role: str,
    ) -> LeaderboardResponse:
        rows = (
            self.db.query(LeaderboardSnapshot)
            .filter(
                LeaderboardSnapshot.class_id == class_id,
                LeaderboardSnapshot.snapshot_date == snapshot_date,
            )
            .order_by(LeaderboardSnapshot.rank.asc())
            .all()
        )

        ranked_rows = [row for row in rows if row.completed_problems > 0]
        student_ids = [row.student_id for row in ranked_rows]
        students = (
            {
                user.id: user
                for user in self.db.query(User)
                .filter(User.id.in_(student_ids), User.deleted_at.is_(None))
                .all()
            }
            if student_ids
            else {}
        )
        entries: list[LeaderboardEntry] = []
        my_rank: int | None = None
        my_score: LeaderboardScoreBreakdown | None = None

        for rank, row in enumerate(ranked_rows, start=1):
            is_me = viewer_role == "student" and row.student_id == viewer_id
            if is_me:
                my_rank = rank
                my_score = LeaderboardScoreBreakdown(
                    accuracy_rate=row.accuracy_rate,
                    accuracy_score=row.accuracy_score,
                    avg_runtime_ms=row.avg_runtime_ms,
                    time_score=row.time_score,
                    total_score=row.total_score,
                )
            names = self._student_name_fields(students.get(row.student_id))
            entries.append(
                LeaderboardEntry(
                    rank=rank,
                    student_id=row.student_id,
                    display_name=names["display_name"] or row.display_name,
                    nickname=names["nickname"],
                    real_name=names["real_name"],
                    completed_problems=row.completed_problems,
                    accuracy_rate=row.accuracy_rate,
                    total_score=row.total_score,
                    is_me=is_me,
                )
            )

        return LeaderboardResponse(
            class_id=class_id,
            class_name=class_name,
            my_rank=my_rank,
            my_score=my_score,
            entries=entries,
            snapshot_date=snapshot_date,
            refreshed_at=refreshed_at,
            source="snapshot",
        )

    def _build_live(
        self,
        class_id: int,
        class_name: str,
        viewer_id: int,
        viewer_role: str,
    ) -> LeaderboardResponse:
        student_ids = [
            row.student_id
            for row in self.db.query(ClassEnrollment.student_id)
            .filter(ClassEnrollment.class_id == class_id, ClassEnrollment.deleted_at.is_(None))
            .all()
        ]
        if not student_ids:
            return LeaderboardResponse(
                class_id=class_id,
                class_name=class_name,
                my_rank=None,
                my_score=None,
                entries=[],
                source="live",
            )

        students = {
            user.id: user
            for user in self.db.query(User).filter(User.id.in_(student_ids), User.deleted_at.is_(None)).all()
        }

        metrics = []
        for student_id in student_ids:
            score = self._compute_score(student_id)
            user = students.get(student_id)
            names = self._student_name_fields(user)
            metrics.append(
                {
                    "student_id": student_id,
                    "display_name": names["display_name"],
                    "nickname": names["nickname"],
                    "real_name": names["real_name"],
                    **score,
                }
            )

        metrics = [item for item in metrics if item["completed_problems"] > 0]
        self._apply_time_scores(metrics)
        metrics.sort(key=lambda item: (-item["total_score"], -item["accuracy_rate"], item["student_id"]))

        entries: list[LeaderboardEntry] = []
        my_rank: int | None = None
        my_score: LeaderboardScoreBreakdown | None = None

        for rank, item in enumerate(metrics, start=1):
            is_me = viewer_role == "student" and item["student_id"] == viewer_id
            if is_me:
                my_rank = rank
                my_score = item["breakdown"]
            entries.append(
                LeaderboardEntry(
                    rank=rank,
                    student_id=item["student_id"],
                    display_name=item["display_name"],
                    nickname=item.get("nickname"),
                    real_name=item.get("real_name"),
                    completed_problems=item["completed_problems"],
                    accuracy_rate=item["accuracy_rate"],
                    total_score=round(item["total_score"], 1),
                    is_me=is_me,
                )
            )

        return LeaderboardResponse(
            class_id=class_id,
            class_name=class_name,
            my_rank=my_rank,
            my_score=my_score,
            entries=entries,
            source="live",
        )

    def _get_class_or_404(self, class_id: int) -> TeachingClass:
        teaching_class = (
            self.db.query(TeachingClass)
            .filter(TeachingClass.id == class_id, TeachingClass.deleted_at.is_(None))
            .first()
        )
        if teaching_class is None:
            raise AppException(404, "班级不存在")
        return teaching_class

    def _assert_viewer_access(
        self,
        class_id: int,
        viewer_id: int,
        viewer_role: str,
        teacher_id: int | None,
        teaching_class: TeachingClass,
    ) -> None:
        if viewer_role == "teacher":
            if teacher_id is None or teaching_class.teacher_id != teacher_id:
                raise_forbidden(self.db, teacher_id, "leaderboard", f"class_id={class_id}")
            return
        if viewer_role == "student":
            enrolled = (
                self.db.query(ClassEnrollment)
                .filter(
                    ClassEnrollment.class_id == class_id,
                    ClassEnrollment.student_id == viewer_id,
                    ClassEnrollment.deleted_at.is_(None),
                )
                .first()
            )
            if enrolled is None:
                raise_forbidden(self.db, viewer_id, "leaderboard", f"class_id={class_id}")
            return
        raise_forbidden(self.db, viewer_id, "leaderboard", f"class_id={class_id},role={viewer_role}")

    def _compute_score(self, student_id: int) -> dict:
        submissions = (
            apply_regular_submission_filters(
                self.db.query(Submission).filter(Submission.user_id == student_id)
            )
            .all()
        )

        valid = [sub for sub in submissions if sub.status in VALID_SUBMISSION_STATUSES]
        ac_subs = [sub for sub in valid if sub.status == SubmissionStatus.AC]

        completed_problems = len({sub.problem_id for sub in ac_subs})
        accuracy_rate = round(len(ac_subs) / len(valid) * 100, 1) if valid else 0.0
        accuracy_score = accuracy_rate * self.ACCURACY_WEIGHT

        runtimes = [sub.runtime_ms for sub in ac_subs if sub.runtime_ms and sub.runtime_ms > 0]
        avg_runtime = sum(runtimes) / len(runtimes) if runtimes else None

        breakdown = LeaderboardScoreBreakdown(
            accuracy_rate=accuracy_rate,
            accuracy_score=round(accuracy_score, 1),
            avg_runtime_ms=round(avg_runtime, 1) if avg_runtime else None,
            time_score=0.0,
            total_score=round(accuracy_score, 1),
        )

        return {
            "completed_problems": completed_problems,
            "accuracy_rate": accuracy_rate,
            "avg_runtime_ms": avg_runtime,
            "total_score": breakdown.total_score,
            "breakdown": breakdown,
        }

    def _apply_time_scores(self, metrics: list[dict]) -> None:
        avg_times = [item["avg_runtime_ms"] for item in metrics if item.get("avg_runtime_ms")]
        max_avg = max(avg_times) if avg_times else None

        for item in metrics:
            avg_runtime = item.get("avg_runtime_ms")
            breakdown: LeaderboardScoreBreakdown = item["breakdown"]
            if max_avg and avg_runtime:
                relative = min(avg_runtime / max_avg, 1.0)
                time_score = (1 - relative) * 100 * self.TIME_WEIGHT
            else:
                time_score = 0.0

            breakdown.time_score = round(time_score, 1)
            breakdown.total_score = round(breakdown.accuracy_score + breakdown.time_score, 1)
            item["total_score"] = breakdown.total_score

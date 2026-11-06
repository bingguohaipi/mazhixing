"""Teacher analytics and dashboard statistics."""

from __future__ import annotations

import csv
import io
from datetime import date, datetime, timedelta, timezone
from collections import defaultdict
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.forbidden import raise_forbidden
from app.models.class_model import ClassEnrollment, TeachingClass
from app.models.homework import Homework, HomeworkClass, HomeworkProblem
from app.models.problem import Problem
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User
from app.schemas.analytics_schema import (
    AnalyticsPeriod,
    AttentionStudent,
    ClassAnalytics,
    ClassProblemWrongCodeItem,
    ClassProblemWrongCodesResponse,
    ClassWrongProblemDetail,
    ClassWrongSummary,
    DailyTrendItem,
    SubmissionTrendRange,
    SubmissionTrendResponse,
    TrendChartType,
    TrendGranularity,
    KnowledgePointStat,
    RecentHomeworkBrief,
    StudentSubmissionRow,
    StudentSubmissionStatItem,
    TeacherDashboardOverview,
    TopWrongProblem,
    WrongSummaryStudentBrief,
)
from app.services.homework_service import HomeworkService
from app.utils.user_display import public_display_name

VALID_STATUSES = {
    SubmissionStatus.AC,
    SubmissionStatus.WA,
    SubmissionStatus.TLE,
    SubmissionStatus.RE,
}
WRONG_STATUSES = {SubmissionStatus.WA, SubmissionStatus.TLE, SubmissionStatus.RE}
_ANALYTICS_TZ = ZoneInfo("Asia/Shanghai")


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        self.homework_service = HomeworkService(db)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _period_start(period: AnalyticsPeriod, now: datetime | None = None) -> datetime | None:
        now = now or datetime.now(timezone.utc)
        if period == "week":
            return now - timedelta(days=7)
        if period == "month":
            return now - timedelta(days=30)
        if period == "semester":
            return now - timedelta(days=180)
        return None

    def get_dashboard(self, teacher_id: int) -> TeacherDashboardOverview:
        classes = (
            self.db.query(TeachingClass)
            .filter(TeachingClass.teacher_id == teacher_id, TeachingClass.deleted_at.is_(None))
            .all()
        )
        class_ids = [item.id for item in classes]
        student_count = 0
        if class_ids:
            student_count = (
                self.db.query(ClassEnrollment.student_id)
                .filter(ClassEnrollment.class_id.in_(class_ids), ClassEnrollment.deleted_at.is_(None))
                .distinct()
                .count()
            )

        from app.models.problem import ProblemScope, PublicPublishStatus

        problem_count = (
            self.db.query(Problem)
            .filter(
                Problem.scope == ProblemScope.PUBLIC,
                Problem.publish_status == PublicPublishStatus.PUBLISHED,
                Problem.deleted_at.is_(None),
            )
            .count()
        )

        homeworks = (
            self.db.query(Homework)
            .filter(Homework.teacher_id == teacher_id, Homework.deleted_at.is_(None))
            .order_by(Homework.end_time.desc())
            .all()
        )
        now = self._now()
        active_homework_count = sum(
            1 for hw in homeworks if self.homework_service.compute_status(hw, now) == "进行中"
        )

        week_start = self._period_start("week", now)
        week_query = self.db.query(Submission).filter(
            Submission.status.in_(VALID_STATUSES),
            Submission.is_late.is_(False),
        )
        week_query = week_query.join(User, User.id == Submission.user_id).filter(
            User.created_by_teacher_id == teacher_id
        )
        if week_start:
            week_query = week_query.filter(Submission.created_at >= week_start)
        week_submissions = week_query.all()
        week_submission_count = len(week_submissions)
        week_ac = sum(1 for item in week_submissions if item.status == SubmissionStatus.AC)
        week_pass_rate = round(week_ac / week_submission_count * 100, 1) if week_submission_count else 0.0

        recent: list[RecentHomeworkBrief] = []
        for homework in homeworks[:5]:
            if homework.withdrawn_at is not None:
                continue
            class_names = []
            for link in homework.class_links:
                teaching_class = self.db.get(TeachingClass, link.class_id)
                if teaching_class:
                    class_names.append(teaching_class.name)
            total_students = self.homework_service._count_target_students(homework)
            submitted, _, _, _, _, _ = self.homework_service._homework_stats(homework.id)
            completion_rate = round(submitted / total_students * 100, 1) if total_students else 0.0
            recent.append(
                RecentHomeworkBrief(
                    id=homework.id,
                    title=homework.title,
                    class_names=class_names,
                    end_time=homework.end_time,
                    status=self.homework_service.compute_status(homework, now),
                    completion_rate=completion_rate,
                    submitted_count=submitted,
                    total_students=total_students,
                )
            )

        return TeacherDashboardOverview(
            class_count=len(classes),
            student_count=student_count,
            problem_count=problem_count,
            active_homework_count=active_homework_count,
            week_submission_count=week_submission_count,
            week_pass_rate=week_pass_rate,
            recent_homeworks=recent,
        )

    def get_class_analytics(
        self,
        teacher_id: int,
        class_id: int,
        period: AnalyticsPeriod = "week",
        homework_id: int | None = None,
    ) -> ClassAnalytics:
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
            raise_forbidden(self.db, teacher_id, "analytics", f"class_id={class_id}")

        student_ids = self._class_student_ids(class_id)
        period_start = self._period_start(period)

        submission_query = (
            self.db.query(Submission, Problem, User, Homework)
            .join(Problem, Problem.id == Submission.problem_id)
            .join(User, User.id == Submission.user_id)
            .outerjoin(Homework, Homework.id == Submission.homework_id)
            .filter(
                Submission.user_id.in_(student_ids),
                Submission.status.in_(VALID_STATUSES),
            )
        )
        if homework_id is not None:
            submission_query = submission_query.filter(Submission.homework_id == homework_id)
        if period_start:
            submission_query = submission_query.filter(Submission.created_at >= period_start)

        rows = submission_query.order_by(Submission.created_at.desc()).all()

        regular_rows = [(s, p, u, h) for s, p, u, h in rows if not s.is_late]
        late_rows = [(s, p, u, h) for s, p, u, h in rows if s.is_late]

        total_submissions = len(regular_rows)
        ac_count = sum(1 for s, _, _, _ in regular_rows if s.status == SubmissionStatus.AC)
        average_accuracy = round(ac_count / total_submissions * 100, 1) if total_submissions else 0.0

        completion_rate = self._compute_completion_rate(class_id, student_ids, homework_id, period_start)

        knowledge_points = self._knowledge_stats(regular_rows)
        daily_trend = self._daily_trend(
            regular_rows + [(s, p, u, h) for s, p, u, h in late_rows],
            period,
        )
        ac_pairs = self._ac_solved_pairs(student_ids, period_start, homework_id)
        top_wrong = self._top_wrong_problems(regular_rows + late_rows, ac_pairs)
        student_submissions = self._to_submission_rows(regular_rows[:100])
        late_submissions = self._to_submission_rows(late_rows[:100])
        student_submission_stats = self._student_submission_stats(regular_rows)
        late_submission_stats = self._student_submission_stats(late_rows)
        attention = self._attention_students(student_ids, class_id, homework_id)

        return ClassAnalytics(
            class_id=class_id,
            class_name=teaching_class.name,
            period=period,
            completion_rate=completion_rate,
            average_accuracy=average_accuracy,
            total_submissions=total_submissions,
            late_submission_count=len(late_rows),
            student_count=len(student_ids),
            knowledge_points=knowledge_points,
            daily_trend=daily_trend,
            top_wrong_problems=top_wrong,
            student_submissions=student_submissions,
            late_submissions=late_submissions,
            student_submission_stats=student_submission_stats,
            late_submission_stats=late_submission_stats,
            attention_students=attention,
        )

    def get_submission_trend(
        self,
        teacher_id: int,
        class_id: int,
        trend_range: SubmissionTrendRange = "7d",
        homework_id: int | None = None,
    ) -> SubmissionTrendResponse:
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
            raise_forbidden(self.db, teacher_id, "analytics", f"class_id={class_id}")

        student_ids = self._class_student_ids(class_id)
        granularity, chart_type = self._submission_trend_view(trend_range)
        start_date = self._submission_trend_start_date(trend_range)
        start_local = datetime.combine(start_date, datetime.min.time(), tzinfo=_ANALYTICS_TZ)
        start_dt = start_local.astimezone(timezone.utc)

        submission_query = (
            self.db.query(Submission)
            .filter(
                Submission.user_id.in_(student_ids),
                Submission.status.in_(VALID_STATUSES),
                Submission.created_at >= start_dt,
            )
        )
        if homework_id is not None:
            submission_query = submission_query.filter(Submission.homework_id == homework_id)

        submissions = submission_query.all()
        items = self._build_submission_trend_items(
            submissions,
            start_date=start_date,
            granularity=granularity,
            trend_range=trend_range,
        )
        return SubmissionTrendResponse(
            range=trend_range,
            granularity=granularity,
            chart_type=chart_type,
            items=items,
        )

    def export_csv(
        self,
        teacher_id: int,
        class_id: int | None,
        period: AnalyticsPeriod,
        homework_id: int | None = None,
    ) -> str:
        if class_id is None:
            classes = (
                self.db.query(TeachingClass)
                .filter(TeachingClass.teacher_id == teacher_id, TeachingClass.deleted_at.is_(None))
                .all()
            )
            if not classes:
                raise AppException(400, "暂无班级数据可导出")
            class_id = classes[0].id

        analytics = self.get_class_analytics(teacher_id, class_id, period, homework_id)
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["班级", analytics.class_name, "周期", analytics.period])
        writer.writerow(["作业完成率", f"{analytics.completion_rate}%"])
        writer.writerow(["平均正确率", f"{analytics.average_accuracy}%"])
        writer.writerow(["有效提交次数", analytics.total_submissions])
        writer.writerow(["补交次数", analytics.late_submission_count])
        writer.writerow([])
        writer.writerow(["知识点", "掌握率", "已做题数", "AC题数"])
        for item in analytics.knowledge_points:
            writer.writerow([item.name, f"{item.mastery_rate}%", item.attempted_count, item.ac_count])
        writer.writerow([])
        writer.writerow(["高频错题", "错误次数", "知识点"])
        for item in analytics.top_wrong_problems:
            writer.writerow([item.title, item.wrong_count, item.knowledge_point or ""])
        writer.writerow([])
        writer.writerow(["学生", "有效提交", "AC次数", "正确率", "涉及题数", "最近提交(UTC)"])
        for item in analytics.student_submission_stats:
            writer.writerow([
                item.student_name,
                item.submission_count,
                item.ac_count,
                f"{item.accuracy_rate}%",
                item.problems_attempted,
                item.last_submitted_at.isoformat() if item.last_submitted_at else "",
            ])
        if analytics.late_submission_stats:
            writer.writerow([])
            writer.writerow(["补交统计", "提交次数", "AC次数", "正确率", "涉及题数", "最近提交(UTC)"])
            for item in analytics.late_submission_stats:
                writer.writerow([
                    item.student_name,
                    item.submission_count,
                    item.ac_count,
                    f"{item.accuracy_rate}%",
                    item.problems_attempted,
                    item.last_submitted_at.isoformat() if item.last_submitted_at else "",
                ])
        return "\ufeff" + buffer.getvalue()

    def get_class_wrong_summary(
        self,
        teacher_id: int,
        class_id: int,
        period: AnalyticsPeriod = "week",
        homework_id: int | None = None,
        knowledge_point: str | None = None,
    ) -> ClassWrongSummary:
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
            raise_forbidden(self.db, teacher_id, "analytics", f"class_id={class_id}")

        student_ids = self._class_student_ids(class_id)
        period_start = self._period_start(period)
        rows = self._fetch_submission_rows(student_ids, period_start, homework_id)
        ac_pairs = self._ac_solved_pairs(student_ids, period_start, homework_id)

        problem_buckets: dict[int, dict[str, object]] = {}
        total_wrong = 0
        for submission, problem, user, _ in rows:
            if submission.status not in WRONG_STATUSES:
                continue
            if (user.id, problem.id) in ac_pairs:
                continue
            total_wrong += 1
            bucket = problem_buckets.setdefault(
                problem.id,
                {
                    "title": problem.title,
                    "knowledge_point": problem.knowledge_point,
                    "wrong_count": 0,
                    "students": {},
                },
            )
            bucket["wrong_count"] = int(bucket["wrong_count"]) + 1
            students: dict[int, dict[str, object]] = bucket["students"]  # type: ignore[assignment]
            real_name = (user.display_name or "").strip() or None
            student_bucket = students.setdefault(
                user.id,
                {
                    "student_name": public_display_name(user),
                    "real_name": real_name,
                    "wrong_count": 0,
                    "last_status": submission.status.value,
                    "last_error_at": submission.created_at,
                },
            )
            student_bucket["wrong_count"] = int(student_bucket["wrong_count"]) + 1
            if submission.created_at >= student_bucket["last_error_at"]:  # type: ignore[operator]
                student_bucket["last_status"] = submission.status.value
                student_bucket["last_error_at"] = submission.created_at

        problems: list[ClassWrongProblemDetail] = []
        for problem_id, data in problem_buckets.items():
            kp = data["knowledge_point"]  # type: ignore[index]
            if knowledge_point and (kp or "未分类") != knowledge_point.strip():
                continue
            students_map: dict[int, dict[str, object]] = data["students"]  # type: ignore[assignment]
            student_briefs = [
                WrongSummaryStudentBrief(
                    student_id=student_id,
                    student_name=str(info["student_name"]),
                    real_name=info.get("real_name"),  # type: ignore[arg-type]
                    wrong_count=int(info["wrong_count"]),
                    last_status=str(info["last_status"]),
                    last_error_at=info["last_error_at"],  # type: ignore[arg-type]
                )
                for student_id, info in students_map.items()
            ]
            student_briefs.sort(key=lambda item: item.wrong_count, reverse=True)
            problems.append(
                ClassWrongProblemDetail(
                    problem_id=problem_id,
                    title=str(data["title"]),
                    knowledge_point=kp,  # type: ignore[arg-type]
                    wrong_count=int(data["wrong_count"]),
                    affected_student_count=len(student_briefs),
                    students=student_briefs,
                )
            )

        problems.sort(key=lambda item: item.wrong_count, reverse=True)
        return ClassWrongSummary(
            class_id=class_id,
            class_name=teaching_class.name,
            period=period,
            total_wrong_submissions=total_wrong,
            problem_count=len(problems),
            student_count=len(student_ids),
            problems=problems,
        )

    def get_class_problem_wrong_codes(
        self,
        teacher_id: int,
        class_id: int,
        problem_id: int,
        period: AnalyticsPeriod = "week",
        homework_id: int | None = None,
    ) -> ClassProblemWrongCodesResponse:
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
            raise_forbidden(self.db, teacher_id, "analytics", f"class_id={class_id}")

        problem = self.db.get(Problem, problem_id)
        if problem is None or problem.deleted_at is not None:
            raise AppException(404, "题目不存在", status_code=404)

        student_ids = self._class_student_ids(class_id)
        period_start = self._period_start(period)
        ac_pairs = self._ac_solved_pairs(student_ids, period_start, homework_id)

        rows = self._fetch_submission_rows(student_ids, period_start, homework_id)
        latest_wrong: dict[int, tuple[Submission, User]] = {}
        for submission, prob, user, _ in rows:
            if prob.id != problem_id:
                continue
            if submission.status not in WRONG_STATUSES:
                continue
            if (user.id, problem_id) in ac_pairs:
                continue
            existing = latest_wrong.get(user.id)
            if existing is None or submission.created_at > existing[0].created_at:
                latest_wrong[user.id] = (submission, user)

        items = [
            ClassProblemWrongCodeItem(
                student_id=user.id,
                student_name=public_display_name(user),
                submission_id=submission.id,
                status=submission.status.value,
                language=submission.language,
                code=submission.code,
                submitted_at=submission.created_at,
            )
            for submission, user in latest_wrong.values()
        ]
        items.sort(key=lambda row: row.student_name)
        return ClassProblemWrongCodesResponse(
            class_id=class_id,
            problem_id=problem_id,
            problem_title=problem.title,
            items=items,
        )

    def export_wrong_summary_csv(
        self,
        teacher_id: int,
        class_id: int,
        period: AnalyticsPeriod = "week",
        homework_id: int | None = None,
        knowledge_point: str | None = None,
    ) -> str:
        summary = self.get_class_wrong_summary(
            teacher_id,
            class_id,
            period,
            homework_id,
            knowledge_point,
        )
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["班级", summary.class_name, "周期", summary.period])
        writer.writerow(["错题提交总数", summary.total_wrong_submissions])
        writer.writerow(["涉及题目数", summary.problem_count])
        writer.writerow(["班级人数", summary.student_count])
        writer.writerow([])
        writer.writerow(["题目ID", "题目", "知识点", "错误次数", "涉及学生数"])
        for item in summary.problems:
            writer.writerow([
                item.problem_id,
                item.title,
                item.knowledge_point or "",
                item.wrong_count,
                item.affected_student_count,
            ])
        writer.writerow([])
        writer.writerow(["题目", "真实姓名", "展示名", "错误次数", "最近状态", "最近错误时间"])
        for item in summary.problems:
            for student in item.students:
                writer.writerow([
                    item.title,
                    student.real_name or "",
                    student.student_name,
                    student.wrong_count,
                    student.last_status,
                    student.last_error_at.isoformat(),
                ])
        return "\ufeff" + buffer.getvalue()

    def _fetch_submission_rows(
        self,
        student_ids: list[int],
        period_start: datetime | None,
        homework_id: int | None,
    ) -> list[tuple[Submission, Problem, User, Homework | None]]:
        if not student_ids:
            return []
        submission_query = (
            self.db.query(Submission, Problem, User, Homework)
            .join(Problem, Problem.id == Submission.problem_id)
            .join(User, User.id == Submission.user_id)
            .outerjoin(Homework, Homework.id == Submission.homework_id)
            .filter(
                Submission.user_id.in_(student_ids),
                Submission.status.in_(VALID_STATUSES),
            )
        )
        if homework_id is not None:
            submission_query = submission_query.filter(Submission.homework_id == homework_id)
        if period_start:
            submission_query = submission_query.filter(Submission.created_at >= period_start)
        return submission_query.order_by(Submission.created_at.desc()).all()

    def _ac_solved_pairs(
        self,
        student_ids: list[int],
        period_start: datetime | None,
        homework_id: int | None,
    ) -> set[tuple[int, int]]:
        """Student-problem pairs with at least one AC in the current filter scope."""
        if not student_ids:
            return set()
        query = (
            self.db.query(Submission.user_id, Submission.problem_id)
            .filter(
                Submission.user_id.in_(student_ids),
                Submission.status == SubmissionStatus.AC,
            )
        )
        if homework_id is not None:
            query = query.filter(Submission.homework_id == homework_id)
        if period_start:
            query = query.filter(Submission.created_at >= period_start)
        return {(user_id, problem_id) for user_id, problem_id in query.all()}

    def _class_student_ids(self, class_id: int) -> list[int]:
        return [
            row.student_id
            for row in self.db.query(ClassEnrollment.student_id)
            .filter(ClassEnrollment.class_id == class_id, ClassEnrollment.deleted_at.is_(None))
            .all()
        ]

    def _compute_completion_rate(
        self,
        class_id: int,
        student_ids: list[int],
        homework_id: int | None,
        period_start: datetime | None,
    ) -> float:
        if not student_ids:
            return 0.0

        homeworks = self._target_homeworks(class_id, homework_id, period_start)
        if not homeworks:
            return 0.0

        total_slots = 0
        completed_slots = 0
        for homework in homeworks:
            targets = self._homework_target_student_ids(homework, student_ids)
            for student_id in targets:
                total_slots += 1
                if self._student_finished_homework(student_id, homework):
                    completed_slots += 1
        return round(completed_slots / total_slots * 100, 1) if total_slots else 0.0

    @staticmethod
    def _homework_target_student_ids(homework: Homework, class_student_ids: list[int]) -> list[int]:
        if homework.student_links:
            linked = {link.student_id for link in homework.student_links}
            return [student_id for student_id in class_student_ids if student_id in linked]
        return class_student_ids

    def _student_finished_homework(self, student_id: int, homework: Homework) -> bool:
        problem_ids = [link.problem_id for link in homework.problem_links]
        if not problem_ids:
            return False
        for problem_id in problem_ids:
            has_submission = (
                self.db.query(Submission)
                .filter(
                    Submission.user_id == student_id,
                    Submission.homework_id == homework.id,
                    Submission.problem_id == problem_id,
                    Submission.status.in_(VALID_STATUSES),
                    Submission.is_late.is_(False),
                )
                .first()
            )
            if not has_submission:
                return False
        return True

    def _target_homeworks(
        self,
        class_id: int,
        homework_id: int | None,
        period_start: datetime | None,
    ) -> list[Homework]:
        query = (
            self.db.query(Homework)
            .join(HomeworkClass, HomeworkClass.homework_id == Homework.id)
            .filter(
                HomeworkClass.class_id == class_id,
                Homework.deleted_at.is_(None),
                Homework.withdrawn_at.is_(None),
            )
        )
        if homework_id is not None:
            query = query.filter(Homework.id == homework_id)
        if period_start:
            query = query.filter(Homework.end_time >= period_start)
        return query.all()

    @staticmethod
    def _knowledge_stats(rows: list[tuple[Submission, Problem, User, Homework | None]]) -> list[KnowledgePointStat]:
        grouped: dict[str, dict[str, int]] = defaultdict(lambda: {"attempted": 0, "ac": 0})
        seen: set[tuple[int, int, str | None]] = set()
        for submission, problem, _, _ in rows:
            key_name = problem.knowledge_point or "未分类"
            dedupe_key = (submission.user_id, problem.id, submission.homework_id)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            grouped[key_name]["attempted"] += 1
            if submission.status == SubmissionStatus.AC:
                grouped[key_name]["ac"] += 1

        stats: list[KnowledgePointStat] = []
        for name, values in grouped.items():
            attempted = values["attempted"]
            ac = values["ac"]
            stats.append(
                KnowledgePointStat(
                    name=name,
                    mastery_rate=round(ac / attempted * 100, 1) if attempted else 0.0,
                    attempted_count=attempted,
                    ac_count=ac,
                )
            )
        stats.sort(key=lambda item: item.mastery_rate)
        return stats[:10]

    @staticmethod
    def _submission_trend_days(trend_range: SubmissionTrendRange) -> int:
        mapping: dict[SubmissionTrendRange, int] = {
            "7d": 7,
            "1m": 30,
            "3m": 90,
            "6m": 180,
            "1y": 365,
            "2y": 730,
            "3y": 1095,
        }
        return mapping[trend_range]

    @staticmethod
    def _submission_trend_start_date(trend_range: SubmissionTrendRange) -> date:
        today = AnalyticsService._trend_today()
        days = AnalyticsService._submission_trend_days(trend_range)
        return today - timedelta(days=days - 1)

    @staticmethod
    def _trend_today() -> date:
        return datetime.now(_ANALYTICS_TZ).date()

    @staticmethod
    def _submission_trend_day(created: datetime) -> date:
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        return created.astimezone(_ANALYTICS_TZ).date()

    @staticmethod
    def _submission_trend_view(
        trend_range: SubmissionTrendRange,
    ) -> tuple[TrendGranularity, TrendChartType]:
        if trend_range in ("7d", "1m"):
            return "day", "bar"
        if trend_range in ("3m", "6m"):
            return "week", "bar"
        return "month", "bar"

    @staticmethod
    def _week_start(day: date) -> date:
        return day - timedelta(days=day.weekday())

    @staticmethod
    def _month_start(day: date) -> date:
        return day.replace(day=1)

    def _build_submission_trend_items(
        self,
        submissions: list[Submission],
        *,
        start_date: date,
        granularity: TrendGranularity,
        trend_range: SubmissionTrendRange,
    ) -> list[DailyTrendItem]:
        weekday_labels = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        today = self._trend_today()
        counts: dict[str, int] = defaultdict(int)

        for submission in submissions:
            day = self._submission_trend_day(submission.created_at)
            if granularity == "day":
                key = day.strftime("%Y-%m-%d")
            elif granularity == "week":
                key = self._week_start(day).strftime("%Y-%m-%d")
            else:
                key = self._month_start(day).strftime("%Y-%m")
            counts[key] += 1

        items: list[DailyTrendItem] = []
        if granularity == "day":
            days = self._submission_trend_days(trend_range)
            for offset in range(days):
                day = start_date + timedelta(days=offset)
                if day > today:
                    break
                key = day.strftime("%Y-%m-%d")
                if trend_range == "7d":
                    label = weekday_labels[day.weekday()]
                else:
                    label = f"{day.month}/{day.day}"
                items.append(DailyTrendItem(date=key, label=label, count=counts.get(key, 0)))
            return items

        if granularity == "week":
            cursor = self._week_start(start_date)
            last_week = self._week_start(today)
            while cursor <= last_week:
                key = cursor.strftime("%Y-%m-%d")
                week_end = min(cursor + timedelta(days=6), today)
                label = f"{cursor.month}/{cursor.day}-{week_end.month}/{week_end.day}"
                items.append(DailyTrendItem(date=key, label=label, count=counts.get(key, 0)))
                cursor += timedelta(days=7)
            return items

        cursor = self._month_start(start_date)
        last_month = self._month_start(today)
        while cursor <= last_month:
            key = cursor.strftime("%Y-%m")
            if trend_range == "1y":
                label = f"{cursor.month}月"
            else:
                label = f"{cursor.year}/{cursor.month}"
            items.append(DailyTrendItem(date=key, label=label, count=counts.get(key, 0)))
            if cursor.month == 12:
                cursor = date(cursor.year + 1, 1, 1)
            else:
                cursor = date(cursor.year, cursor.month + 1, 1)
        return items

    @staticmethod
    def _trend_span_days(period: AnalyticsPeriod) -> int:
        if period == "month":
            return 30
        if period == "semester":
            return 30
        if period == "all":
            return 30
        return 7

    @staticmethod
    def _daily_trend(
        rows: list[tuple[Submission, Problem, User, Homework | None]],
        period: AnalyticsPeriod = "week",
    ) -> list[DailyTrendItem]:
        counts: dict[str, int] = defaultdict(int)
        for submission, _, _, _ in rows:
            day = submission.created_at.strftime("%Y-%m-%d")
            counts[day] += 1

        labels = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        items: list[DailyTrendItem] = []
        today = datetime.now(timezone.utc).date()
        span = AnalyticsService._trend_span_days(period)
        for offset in range(span - 1, -1, -1):
            day = today - timedelta(days=offset)
            key = day.strftime("%Y-%m-%d")
            weekday = labels[day.weekday()]
            label = f"{day.month}/{day.day}" if span > 7 else weekday
            items.append(DailyTrendItem(date=key, label=label, count=counts.get(key, 0)))
        return items

    @staticmethod
    def _top_wrong_problems(
        rows: list[tuple[Submission, Problem, User, Homework | None]],
        ac_pairs: set[tuple[int, int]] | None = None,
    ) -> list[TopWrongProblem]:
        ac_pairs = ac_pairs or set()
        wrong_counts: dict[int, dict[str, object]] = {}
        for submission, problem, user, _ in rows:
            if submission.status not in WRONG_STATUSES:
                continue
            if (user.id, problem.id) in ac_pairs:
                continue
            bucket = wrong_counts.setdefault(
                problem.id,
                {"title": problem.title, "knowledge_point": problem.knowledge_point, "count": 0},
            )
            bucket["count"] = int(bucket["count"]) + 1

        result = [
            TopWrongProblem(
                problem_id=problem_id,
                title=str(data["title"]),
                knowledge_point=data["knowledge_point"],  # type: ignore[arg-type]
                wrong_count=int(data["count"]),
            )
            for problem_id, data in wrong_counts.items()
        ]
        result.sort(key=lambda item: item.wrong_count, reverse=True)
        return result[:10]

    @staticmethod
    def _to_submission_rows(
        rows: list[tuple[Submission, Problem, User, Homework | None]],
    ) -> list[StudentSubmissionRow]:
        return [
            StudentSubmissionRow(
                student_id=user.id,
                student_name=user.display_name or user.account,
                homework_id=homework.id if homework else None,
                homework_title=homework.title if homework else None,
                problem_id=problem.id,
                problem_title=problem.title,
                status=submission.status.value,
                submitted_at=submission.created_at,
                is_late=submission.is_late,
            )
            for submission, problem, user, homework in rows
        ]

    @staticmethod
    def _student_submission_stats(
        rows: list[tuple[Submission, Problem, User, Homework | None]],
    ) -> list[StudentSubmissionStatItem]:
        buckets: dict[int, dict] = {}
        for submission, problem, user, _homework in rows:
            name = (user.display_name or user.account or "").strip() or user.account
            bucket = buckets.setdefault(
                user.id,
                {
                    "student_name": name,
                    "total": 0,
                    "ac": 0,
                    "problems": set(),
                    "last_at": None,
                },
            )
            bucket["total"] += 1
            if submission.status == SubmissionStatus.AC:
                bucket["ac"] += 1
            bucket["problems"].add(problem.id)
            created = submission.created_at
            if bucket["last_at"] is None or created > bucket["last_at"]:
                bucket["last_at"] = created

        items: list[StudentSubmissionStatItem] = []
        for data in buckets.values():
            total = int(data["total"])
            ac = int(data["ac"])
            rate = round(ac / total * 100, 1) if total else 0.0
            items.append(
                StudentSubmissionStatItem(
                    student_name=str(data["student_name"]),
                    submission_count=total,
                    ac_count=ac,
                    accuracy_rate=rate,
                    problems_attempted=len(data["problems"]),
                    last_submitted_at=data["last_at"],
                )
            )
        items.sort(key=lambda row: (-row.submission_count, row.student_name))
        return items

    def _attention_students(
        self,
        student_ids: list[int],
        class_id: int,
        homework_id: int | None,
    ) -> list[AttentionStudent]:
        if not student_ids:
            return []

        homeworks = self._target_homeworks(class_id, homework_id, None)
        recent_homeworks = sorted(homeworks, key=lambda item: item.end_time, reverse=True)[:3]
        attention: list[AttentionStudent] = []

        for student_id in student_ids:
            user = self.db.get(User, student_id)
            if user is None:
                continue
            scores: list[int] = []
            weak_points: set[str] = set()
            for homework in recent_homeworks:
                total = len(homework.problem_links)
                if total == 0:
                    continue
                ac_count = 0
                for link in homework.problem_links:
                    submission = (
                        self.db.query(Submission)
                        .filter(
                            Submission.user_id == student_id,
                            Submission.homework_id == homework.id,
                            Submission.problem_id == link.problem_id,
                            Submission.status.in_(VALID_STATUSES),
                            Submission.is_late.is_(False),
                        )
                        .order_by(Submission.id.desc())
                        .first()
                    )
                    if submission and submission.status == SubmissionStatus.AC:
                        ac_count += 1
                    elif submission and submission.status in WRONG_STATUSES:
                        problem = self.db.get(Problem, link.problem_id)
                        if problem and problem.knowledge_point:
                            weak_points.add(problem.knowledge_point)
                scores.append(round(ac_count / total * 100))

            if len(scores) < 2:
                continue
            avg = sum(scores) / len(scores)
            if avg >= 60:
                continue
            score_text = " / ".join(str(item) for item in scores)
            weak_list = list(weak_points)[:3]
            suggestion = "建议加强相关知识点练习"
            if weak_list:
                suggestion = f"建议加强「{'、'.join(weak_list)}」相关练习"
            attention.append(
                AttentionStudent(
                    student_id=student_id,
                    student_name=user.display_name or user.account,
                    recent_scores=score_text,
                    weak_knowledge_points=weak_list or ["综合"],
                    suggestion=suggestion,
                )
            )
        return attention[:10]

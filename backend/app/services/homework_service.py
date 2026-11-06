from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.forbidden import raise_forbidden
from app.models.audit import OperationLog
from app.models.class_model import ClassEnrollment, TeachingClass
from app.models.homework import Homework, HomeworkClass, HomeworkProblem, HomeworkStudent, HomeworkStudentAck
from app.models.notice import Notice, NoticeClass
from app.models.problem import Problem, TestCase
from app.models.user import User, UserRole
from app.schemas.homework_schema import (
    HomeworkAllowLateRequest,
    HomeworkClassBrief,
    HomeworkCreateRequest,
    HomeworkDetail,
    HomeworkListItem,
    HomeworkProblemBrief,
    HomeworkStatusLiteral,
    HomeworkStudentProblemAttempt,
    HomeworkStudentProgressRow,
    HomeworkSubmissionReport,
    HomeworkUpdateRequest,
    StudentHomeworkItem,
)
from app.models.submission import Submission, SubmissionStatus


class HomeworkService:
    def __init__(self, db: Session):
        self.db = db

    def _log(self, user_id: int, action: str, detail: str | None = None) -> None:
        self.db.add(OperationLog(user_id=user_id, action=action, resource="homework", detail=detail))

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def compute_status(homework: Homework, now: datetime | None = None) -> HomeworkStatusLiteral:
        now = now or datetime.now(timezone.utc)
        if homework.withdrawn_at is not None:
            return "已撤回"
        start = homework.start_time
        end = homework.end_time
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        if now < start:
            return "未开始"
        if now <= end:
            return "进行中"
        return "已截止"

    def list_homework(self, teacher_id: int, status: str | None = None) -> list[HomeworkListItem]:
        homeworks = (
            self.db.query(Homework)
            .filter(Homework.teacher_id == teacher_id, Homework.deleted_at.is_(None))
            .order_by(Homework.id.desc())
            .all()
        )
        items = [self._to_list_item(hw) for hw in homeworks]
        if status and status != "all":
            items = [item for item in items if item.status == status]
        return items

    def get_homework(self, homework_id: int, teacher_id: int) -> HomeworkDetail:
        homework = self._get_owned_homework(homework_id, teacher_id)
        return self._to_detail(homework)

    def get_submission_report(self, homework_id: int, teacher_id: int) -> HomeworkSubmissionReport:
        homework = self._get_owned_homework(homework_id, teacher_id)
        valid_statuses = {
            SubmissionStatus.AC,
            SubmissionStatus.WA,
            SubmissionStatus.TLE,
            SubmissionStatus.RE,
        }
        problem_links = sorted(homework.problem_links, key=lambda link: (link.sort_order, link.problem_id))
        problem_count = len(problem_links)
        student_ids = self._target_student_ids(homework)
        users_by_id: dict[int, User] = {}
        if student_ids:
            users = (
                self.db.query(User)
                .filter(User.id.in_(student_ids), User.deleted_at.is_(None))
                .all()
            )
            users_by_id = {user.id: user for user in users}

        rows: list[HomeworkStudentProgressRow] = []
        all_ac_students: list[str] = []

        for student_id in student_ids:
            user = users_by_id.get(student_id)
            display_name = (user.display_name or user.account if user else None) or f"学生#{student_id}"
            account = user.account if user else ""
            student_no = user.student_no if user else None

            attempts: list[HomeworkStudentProblemAttempt] = []
            ac_count = 0
            for link in problem_links:
                problem = self.db.get(Problem, link.problem_id)
                title = problem.title if problem else f"题目#{link.problem_id}"
                best = (
                    self.db.query(Submission)
                    .filter(
                        Submission.user_id == student_id,
                        Submission.problem_id == link.problem_id,
                        Submission.homework_id == homework.id,
                        Submission.status.in_(valid_statuses),
                    )
                    .order_by(Submission.id.desc())
                    .first()
                )
                status_value = best.status.value if best else None
                if status_value == SubmissionStatus.AC.value:
                    ac_count += 1
                err = None
                if best and best.status != SubmissionStatus.AC:
                    err = best.error_message or best.compile_output
                    if err and len(err) > 200:
                        err = err[:200] + "…"
                attempts.append(
                    HomeworkStudentProblemAttempt(
                        problem_id=link.problem_id,
                        problem_title=title,
                        status=status_value,
                        submission_id=best.id if best else None,
                        error_message=err,
                        is_late=bool(best.is_late) if best else False,
                    )
                )

            all_ac = problem_count > 0 and ac_count == problem_count
            if all_ac:
                all_ac_students.append(display_name)

            rows.append(
                HomeworkStudentProgressRow(
                    student_id=student_id,
                    display_name=display_name,
                    account=account,
                    student_no=student_no,
                    ac_count=ac_count,
                    problem_count=problem_count,
                    all_ac=all_ac,
                    problems=attempts,
                )
            )

        rows.sort(key=lambda row: (-row.ac_count, row.display_name))

        problem_briefs: list[HomeworkProblemBrief] = []
        for link in problem_links:
            problem = self.db.get(Problem, link.problem_id)
            if problem is None:
                continue
            problem_briefs.append(
                HomeworkProblemBrief(
                    id=problem.id,
                    title=problem.title,
                    language=problem.language.value,
                    difficulty=problem.difficulty.value,
                )
            )

        return HomeworkSubmissionReport(
            homework_id=homework.id,
            homework_title=homework.title,
            problem_count=problem_count,
            problems=problem_briefs,
            all_ac_students=all_ac_students,
            students=rows,
        )

    def create_homework(self, teacher_id: int, payload: HomeworkCreateRequest) -> HomeworkDetail:
        self._validate_classes(teacher_id, payload.class_ids)
        self._validate_problems(teacher_id, payload.problem_ids)
        if payload.student_ids:
            self._validate_students_in_classes(payload.class_ids, payload.student_ids)

        homework = Homework(
            teacher_id=teacher_id,
            title=payload.title.strip(),
            description=payload.description.strip() if payload.description else None,
            start_time=self._ensure_aware(payload.start_time),
            end_time=self._ensure_aware(payload.end_time),
            allow_late_submission=payload.allow_late_submission,
            created_by=teacher_id,
            updated_by=teacher_id,
        )
        self.db.add(homework)
        self.db.flush()
        self._sync_classes(homework.id, payload.class_ids)
        self._sync_problems(homework.id, payload.problem_ids)
        if payload.student_ids:
            self._sync_students(homework.id, payload.student_ids)

        self.db.flush()
        self.db.refresh(homework)
        self._notify_homework_classes(
            homework,
            teacher_id,
            title=f"新作业「{homework.title}」已发布",
            content="老师布置了新作业，请进入作业中心查看并完成。",
        )
        self._log(teacher_id, "create_homework", f"homework_id={homework.id}")
        self.db.commit()
        self.db.refresh(homework)
        return self._to_detail(homework)

    def update_homework(
        self,
        homework_id: int,
        teacher_id: int,
        payload: HomeworkUpdateRequest,
    ) -> tuple[HomeworkDetail, bool]:
        homework = self._get_owned_homework(homework_id, teacher_id)
        status = self.compute_status(homework)
        if status in ("已截止", "已撤回"):
            raise AppException(400, "已截止或已撤回的作业不可编辑")
        if status not in ("未开始", "进行中"):
            raise AppException(400, "当前状态不可编辑")

        is_in_progress = status == "进行中"
        before = self._homework_change_snapshot(homework)

        if is_in_progress:
            if payload.class_ids is not None or payload.student_ids is not None:
                raise AppException(400, "进行中的作业不可修改班级或学生范围")
            if payload.start_time is not None:
                raise AppException(400, "进行中的作业不可修改开始时间")
        else:
            if payload.class_ids is not None:
                self._validate_classes(teacher_id, payload.class_ids)
                self._sync_classes(homework.id, payload.class_ids)
            if payload.student_ids is not None:
                class_ids = payload.class_ids or [link.class_id for link in homework.class_links]
                self._validate_students_in_classes(class_ids, payload.student_ids)
                self._sync_students(homework.id, payload.student_ids)

        if payload.problem_ids is not None:
            self._validate_problems(teacher_id, payload.problem_ids)
            self._sync_problems(homework.id, payload.problem_ids)

        updates = payload.model_dump(exclude_unset=True, exclude={"class_ids", "problem_ids", "student_ids"})
        for field, value in updates.items():
            if field in ("start_time", "end_time") and value is not None:
                value = self._ensure_aware(value)
            elif isinstance(value, str) and field == "title":
                value = value.strip()
            elif isinstance(value, str) and field == "description":
                value = value.strip() if value else None
            setattr(homework, field, value)

        homework.start_time = self._ensure_aware(homework.start_time)
        homework.end_time = self._ensure_aware(homework.end_time)
        if homework.end_time <= homework.start_time:
            raise AppException(400, "截止时间必须晚于开始时间")

        self.db.flush()
        self.db.refresh(homework)
        after = self._homework_change_snapshot(homework)
        students_notified = False
        if before != after:
            homework.content_updated_at = self._now()
            students_notified = self._notify_homework_classes(
                homework,
                teacher_id,
                title=f"作业「{homework.title}」已更新",
                content="老师已更新该作业，请进入作业详情查看最新要求与题目。",
            )

        homework.updated_by = teacher_id
        self._log(
            teacher_id,
            "update_homework",
            f"homework_id={homework_id}, notified={students_notified}",
        )
        self.db.commit()
        self.db.refresh(homework)
        return self._to_detail(homework), students_notified

    def acknowledge_homework_update(self, student_id: int, homework_id: int) -> None:
        homework = self.db.get(Homework, homework_id)
        if homework is None or homework.deleted_at is not None or homework.withdrawn_at is not None:
            raise AppException(404, "作业不存在", status_code=404)

        class_ids = [
            row.class_id
            for row in self.db.query(ClassEnrollment.class_id)
            .filter(ClassEnrollment.student_id == student_id, ClassEnrollment.deleted_at.is_(None))
            .all()
        ]
        if not self._is_visible_to_student(homework, student_id, class_ids):
            raise_forbidden(self.db, student_id, "homework", f"homework_id={homework_id}")

        now = self._now()
        ack = (
            self.db.query(HomeworkStudentAck)
            .filter(
                HomeworkStudentAck.homework_id == homework_id,
                HomeworkStudentAck.student_id == student_id,
            )
            .first()
        )
        if ack is None:
            self.db.add(
                HomeworkStudentAck(
                    homework_id=homework_id,
                    student_id=student_id,
                    acknowledged_at=now,
                )
            )
        else:
            ack.acknowledged_at = now
        self.db.commit()

    def _has_unread_update(self, homework: Homework, student_id: int) -> bool:
        if homework.content_updated_at is None:
            return False
        ack = (
            self.db.query(HomeworkStudentAck)
            .filter(
                HomeworkStudentAck.homework_id == homework.id,
                HomeworkStudentAck.student_id == student_id,
            )
            .first()
        )
        if ack is None:
            return True
        ack_time = ack.acknowledged_at
        updated_at = homework.content_updated_at
        if ack_time.tzinfo is None:
            ack_time = ack_time.replace(tzinfo=timezone.utc)
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        return ack_time < updated_at

    def _homework_change_snapshot(self, homework: Homework) -> dict:
        return {
            "title": homework.title.strip(),
            "description": (homework.description or "").strip(),
            "start_time": self._ensure_aware(homework.start_time).isoformat(),
            "end_time": self._ensure_aware(homework.end_time).isoformat(),
            "allow_late_submission": homework.allow_late_submission,
            "class_ids": sorted(link.class_id for link in homework.class_links),
            "problem_ids": sorted(link.problem_id for link in homework.problem_links),
            "student_ids": sorted(link.student_id for link in homework.student_links),
        }

    def _notify_homework_classes(
        self,
        homework: Homework,
        teacher_id: int,
        title: str,
        content: str,
    ) -> bool:
        class_ids = [link.class_id for link in homework.class_links]
        if not class_ids:
            return False

        notice = Notice(
            teacher_id=teacher_id,
            title=title,
            content=content,
            created_by=teacher_id,
            updated_by=teacher_id,
        )
        self.db.add(notice)
        self.db.flush()
        for class_id in class_ids:
            self.db.add(NoticeClass(notice_id=notice.id, class_id=class_id))
        self._log(
            teacher_id,
            "homework_class_notice",
            f"homework_id={homework.id}, notice_id={notice.id}, classes={class_ids}",
        )
        return True

    def withdraw_homework(self, homework_id: int, teacher_id: int) -> HomeworkDetail:
        homework = self._get_owned_homework(homework_id, teacher_id)
        status = self.compute_status(homework)
        if status == "已截止":
            raise AppException(400, "已截止的作业不可撤回")
        if homework.withdrawn_at is not None:
            raise AppException(400, "作业已撤回")

        homework.withdrawn_at = self._now()
        homework.updated_by = teacher_id
        self._notify_homework_classes(
            homework,
            teacher_id,
            title=f"作业「{homework.title}」已撤回",
            content="该作业已被老师撤回，无需再提交。",
        )
        self._log(teacher_id, "withdraw_homework", f"homework_id={homework_id}")
        self.db.commit()
        self.db.refresh(homework)
        return self._to_detail(homework)

    def delete_homework(self, homework_id: int, teacher_id: int) -> None:
        homework = self._get_owned_homework(homework_id, teacher_id)
        if homework.deleted_at is not None:
            raise AppException(400, "作业已删除")
        self._notify_homework_classes(
            homework,
            teacher_id,
            title=f"作业「{homework.title}」已删除",
            content="该作业已被老师删除，请以作业中心最新列表为准。",
        )
        homework.deleted_at = self._now()
        homework.updated_by = teacher_id
        self._log(teacher_id, "delete_homework", f"homework_id={homework_id}")
        self.db.commit()

    def set_allow_late(
        self,
        homework_id: int,
        teacher_id: int,
        payload: HomeworkAllowLateRequest,
    ) -> tuple[HomeworkDetail, bool]:
        homework = self._get_owned_homework(homework_id, teacher_id)
        previous = homework.allow_late_submission
        homework.allow_late_submission = payload.allow_late_submission
        homework.updated_by = teacher_id
        notified = False
        if previous != payload.allow_late_submission:
            homework.content_updated_at = self._now()
            label = "已开启" if payload.allow_late_submission else "已关闭"
            notified = self._notify_homework_classes(
                homework,
                teacher_id,
                title=f"作业「{homework.title}」补交权限{label}",
                content=f"老师{label}该作业的补交权限，请进入作业详情确认截止时间。",
            )
        self._log(
            teacher_id,
            "toggle_late_homework",
            f"homework_id={homework_id}, allow={payload.allow_late_submission}, notified={notified}",
        )
        self.db.commit()
        self.db.refresh(homework)
        return self._to_detail(homework), notified

    def list_student_homework(self, student_id: int) -> list[StudentHomeworkItem]:
        class_ids = [
            enrollment.class_id
            for enrollment in self.db.query(ClassEnrollment)
            .filter(
                ClassEnrollment.student_id == student_id,
                ClassEnrollment.deleted_at.is_(None),
            )
            .all()
        ]

        homeworks = (
            self.db.query(Homework)
            .filter(Homework.deleted_at.is_(None), Homework.withdrawn_at.is_(None))
            .order_by(Homework.end_time.asc())
            .all()
        )

        items: list[StudentHomeworkItem] = []
        for homework in homeworks:
            if not self._is_visible_to_student(homework, student_id, class_ids):
                continue
            status = self.compute_status(homework)
            if status == "已撤回":
                continue
            class_name = self._primary_class_name(homework, class_ids)
            progress = self._student_progress(student_id, homework)
            items.append(
                StudentHomeworkItem(
                    id=homework.id,
                    title=homework.title,
                    status=status,
                    class_name=class_name,
                    problem_count=len(homework.problem_links),
                    start_time=homework.start_time,
                    end_time=homework.end_time,
                    allow_late_submission=homework.allow_late_submission,
                    progress=progress,
                    has_unread_update=self._has_unread_update(homework, student_id),
                    content_updated_at=homework.content_updated_at,
                )
            )
        return items

    def _get_owned_homework(self, homework_id: int, teacher_id: int) -> Homework:
        homework = (
            self.db.query(Homework)
            .filter(
                Homework.id == homework_id,
                Homework.teacher_id == teacher_id,
                Homework.deleted_at.is_(None),
            )
            .first()
        )
        if homework is None:
            raise_forbidden(self.db, teacher_id, "homework", f"homework_id={homework_id}")
        return homework

    def _validate_classes(self, teacher_id: int, class_ids: list[int]) -> None:
        count = (
            self.db.query(TeachingClass)
            .filter(
                TeachingClass.id.in_(class_ids),
                TeachingClass.teacher_id == teacher_id,
                TeachingClass.deleted_at.is_(None),
            )
            .count()
        )
        if count != len(set(class_ids)):
            raise AppException(400, "包含无效或无权限的班级")

    def _validate_problems(self, teacher_id: int, problem_ids: list[int]) -> None:
        from app.services.problem_access import ProblemAccessHelper

        access = ProblemAccessHelper(self.db)
        problems = (
            self.db.query(Problem)
            .filter(
                Problem.id.in_(problem_ids),
                Problem.deleted_at.is_(None),
            )
            .all()
        )
        if len(problems) != len(set(problem_ids)):
            raise AppException(400, "包含无效或无权限的题目")

        for problem in problems:
            if not access.teacher_can_use_in_homework(teacher_id, problem):
                raise AppException(400, "包含无效或无权限的题目")
            case_count = (
                self.db.query(TestCase)
                .filter(TestCase.problem_id == problem.id, TestCase.deleted_at.is_(None))
                .count()
            )
            if case_count == 0:
                raise AppException(400, f"题目「{problem.title}」无有效测试用例，不可布置作业")

    def _validate_students_in_classes(self, class_ids: list[int], student_ids: list[int]) -> None:
        valid_count = (
            self.db.query(ClassEnrollment.student_id)
            .filter(
                ClassEnrollment.class_id.in_(class_ids),
                ClassEnrollment.student_id.in_(student_ids),
                ClassEnrollment.deleted_at.is_(None),
            )
            .distinct()
            .count()
        )
        if valid_count != len(set(student_ids)):
            raise AppException(400, "包含不在所选班级中的学生")

    def _sync_classes(self, homework_id: int, class_ids: list[int]) -> None:
        self.db.query(HomeworkClass).filter(HomeworkClass.homework_id == homework_id).delete()
        for class_id in set(class_ids):
            self.db.add(HomeworkClass(homework_id=homework_id, class_id=class_id))

    def _sync_problems(self, homework_id: int, problem_ids: list[int]) -> None:
        self.db.query(HomeworkProblem).filter(HomeworkProblem.homework_id == homework_id).delete()
        for index, problem_id in enumerate(problem_ids):
            self.db.add(HomeworkProblem(homework_id=homework_id, problem_id=problem_id, sort_order=index))

    def _sync_students(self, homework_id: int, student_ids: list[int]) -> None:
        self.db.query(HomeworkStudent).filter(HomeworkStudent.homework_id == homework_id).delete()
        for student_id in set(student_ids):
            self.db.add(HomeworkStudent(homework_id=homework_id, student_id=student_id))

    def _count_target_students(self, homework: Homework) -> int:
        return len(self._target_student_ids(homework))

    def _target_student_ids(self, homework: Homework) -> list[int]:
        if homework.student_links:
            return [link.student_id for link in homework.student_links]
        class_ids = [link.class_id for link in homework.class_links]
        if not class_ids:
            return []
        rows = (
            self.db.query(ClassEnrollment.student_id)
            .filter(ClassEnrollment.class_id.in_(class_ids), ClassEnrollment.deleted_at.is_(None))
            .distinct()
            .all()
        )
        return [int(row[0]) for row in rows]

    def _is_visible_to_student(self, homework: Homework, student_id: int, student_class_ids: list[int]) -> bool:
        if homework.student_links:
            return any(link.student_id == student_id for link in homework.student_links)
        homework_class_ids = [link.class_id for link in homework.class_links]
        return bool(set(homework_class_ids) & set(student_class_ids))

    def _primary_class_name(self, homework: Homework, student_class_ids: list[int]) -> str:
        for link in homework.class_links:
            if link.class_id in student_class_ids:
                teaching_class = self.db.get(TeachingClass, link.class_id)
                if teaching_class:
                    return teaching_class.name
        if homework.class_links:
            teaching_class = self.db.get(TeachingClass, homework.class_links[0].class_id)
            return teaching_class.name if teaching_class else "未知班级"
        return "未知班级"

    def _student_progress(self, student_id: int, homework: Homework) -> str:
        total = len(homework.problem_links)
        if total == 0:
            return "0/0 已完成"
        ac_count = 0
        valid_statuses = {SubmissionStatus.AC, SubmissionStatus.WA, SubmissionStatus.TLE, SubmissionStatus.RE}
        for link in homework.problem_links:
            best = (
                self.db.query(Submission)
                .filter(
                    Submission.user_id == student_id,
                    Submission.problem_id == link.problem_id,
                    Submission.homework_id == homework.id,
                    Submission.status.in_(valid_statuses),
                )
                .order_by(Submission.id.desc())
                .first()
            )
            if best and best.status == SubmissionStatus.AC:
                ac_count += 1
        return f"{ac_count}/{total} 已完成"

    def _homework_stats(self, homework_id: int) -> tuple[int, int, int, int, int, int]:
        homework = (
            self.db.query(Homework)
            .filter(Homework.id == homework_id, Homework.deleted_at.is_(None))
            .first()
        )
        if homework is None:
            return 0, 0, 0, 0
        problem_ids = [link.problem_id for link in homework.problem_links]
        valid_statuses = {
            SubmissionStatus.AC,
            SubmissionStatus.WA,
            SubmissionStatus.TLE,
            SubmissionStatus.RE,
        }
        submitted_count = 0
        correct_count = 0
        progress_done = 0
        student_ids = self._target_student_ids(homework)
        progress_total = len(problem_ids) * len(student_ids)
        if problem_ids and student_ids:
            for student_id in student_ids:
                best_per_problem: list[SubmissionStatus] = []
                for problem_id in problem_ids:
                    best = (
                        self.db.query(Submission)
                        .filter(
                            Submission.user_id == student_id,
                            Submission.problem_id == problem_id,
                            Submission.homework_id == homework_id,
                            Submission.is_late.is_(False),
                            Submission.status.in_(valid_statuses),
                        )
                        .order_by(Submission.id.desc())
                        .first()
                    )
                    if best is not None:
                        best_per_problem.append(best.status)
                        progress_done += 1
                if len(best_per_problem) == len(problem_ids):
                    submitted_count += 1
                    if all(status == SubmissionStatus.AC for status in best_per_problem):
                        correct_count += 1
        wrong_count = max(submitted_count - correct_count, 0)

        late_submission_count = (
            self.db.query(Submission.user_id)
            .filter(
                Submission.homework_id == homework_id,
                Submission.is_late.is_(True),
                Submission.status.in_(
                    {SubmissionStatus.AC, SubmissionStatus.WA, SubmissionStatus.TLE, SubmissionStatus.RE}
                ),
            )
            .distinct()
            .count()
        )
        return submitted_count, correct_count, wrong_count, late_submission_count, progress_done, progress_total

    def _to_list_item(self, homework: Homework) -> HomeworkListItem:
        class_ids: list[int] = []
        class_names = []
        for link in homework.class_links:
            teaching_class = self.db.get(TeachingClass, link.class_id)
            if teaching_class:
                class_ids.append(teaching_class.id)
                class_names.append(teaching_class.name)

        (
            submitted_count,
            correct_count,
            wrong_count,
            late_submission_count,
            progress_done,
            progress_total,
        ) = self._homework_stats(homework.id)

        return HomeworkListItem(
            id=homework.id,
            title=homework.title,
            status=self.compute_status(homework),
            class_ids=class_ids,
            class_names=class_names,
            problem_count=len(homework.problem_links),
            total_students=self._count_target_students(homework),
            submitted_count=submitted_count,
            correct_count=correct_count,
            wrong_count=wrong_count,
            progress_done=progress_done,
            progress_total=progress_total,
            late_submission_count=late_submission_count,
            start_time=homework.start_time,
            end_time=homework.end_time,
            allow_late_submission=homework.allow_late_submission,
            created_at=homework.created_at,
        )

    def _to_detail(self, homework: Homework) -> HomeworkDetail:
        base = self._to_list_item(homework)
        classes: list[HomeworkClassBrief] = []
        for link in homework.class_links:
            teaching_class = self.db.get(TeachingClass, link.class_id)
            if teaching_class:
                classes.append(HomeworkClassBrief(id=teaching_class.id, name=teaching_class.name))

        problems: list[HomeworkProblemBrief] = []
        sorted_links = sorted(homework.problem_links, key=lambda item: item.sort_order)
        for link in sorted_links:
            problem = self.db.get(Problem, link.problem_id)
            if problem:
                problems.append(
                    HomeworkProblemBrief(
                        id=problem.id,
                        title=problem.title,
                        language=problem.language.value,
                        difficulty=problem.difficulty.value,
                    )
                )

        return HomeworkDetail(
            **base.model_dump(),
            description=homework.description,
            classes=classes,
            problems=problems,
            student_ids=[link.student_id for link in homework.student_links],
        )

    @staticmethod
    def _ensure_aware(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

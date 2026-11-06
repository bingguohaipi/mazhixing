from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.forbidden import raise_forbidden
from app.models.audit import OperationLog
from app.models.class_model import ClassEnrollment, TeachingClass
from app.models.homework import Homework, HomeworkProblem
from app.models.problem import Problem, TestCase
from app.models.submission import Submission, SubmissionCaseResult, SubmissionStatus
from app.models.user import User, UserRole
from app.schemas.problem_schema import ProblemAcSolverItem
from app.schemas.submission_schema import (
    SubmissionCaseResultItem,
    SubmissionCreateRequest,
    SubmissionDetail,
    SubmissionListItem,
    TeacherSubmissionDetail,
)
from app.core.code_validation import validate_submission_code
from app.core.judge_lock import acquire_judge_lock
from app.services.ai_analysis_format import unpack_ai_analysis
from app.monitoring.metrics import SUBMISSIONS_TOTAL
from app.services.homework_service import HomeworkService
from app.services.judge_service import JudgeService


VALID_SUBMISSION_STATUSES = {
    SubmissionStatus.AC,
    SubmissionStatus.WA,
    SubmissionStatus.TLE,
    SubmissionStatus.RE,
}


class SubmissionService:
    def __init__(self, db: Session):
        self.db = db
        self.judge = JudgeService()

    def _log(self, user_id: int, action: str, detail: str | None = None) -> None:
        self.db.add(OperationLog(user_id=user_id, action=action, resource="submission", detail=detail))

    def _find_pending_submission(self, user_id: int, problem_id: int) -> Submission | None:
        return (
            self.db.query(Submission)
            .filter(
                Submission.user_id == user_id,
                Submission.problem_id == problem_id,
                Submission.status == SubmissionStatus.PENDING,
            )
            .order_by(Submission.id.desc())
            .first()
        )

    def _finish_pending_judge(self, submission: Submission, code: str | None = None) -> None:
        if code is not None:
            submission.code = code
            self.db.commit()
        self.run_judge(submission.id)
        self.db.refresh(submission)
        if submission.status == SubmissionStatus.PENDING:
            submission.status = SubmissionStatus.RE
            submission.error_message = "判题未完成，请重新提交"
            self.db.commit()

    def _ensure_no_pending_submission(self, user_id: int, problem_id: int) -> None:
        pending = self._find_pending_submission(user_id, problem_id)
        if pending is None:
            return
        self._finish_pending_judge(pending)
        self.db.refresh(pending)
        if pending.status == SubmissionStatus.PENDING:
            raise AppException(429, "上一提交仍在判题中，请稍后再试", status_code=429)

    def create_submission(self, user_id: int, payload: SubmissionCreateRequest) -> SubmissionDetail:
        code = payload.code.strip()
        validate_submission_code(code, payload.language)

        problem = (
            self.db.query(Problem)
            .filter(Problem.id == payload.problem_id, Problem.deleted_at.is_(None))
            .first()
        )
        if problem is None:
            raise AppException(404, "题目不存在")
        from app.utils.problem_languages import problem_supports_language

        if not problem_supports_language(problem, payload.language):
            raise AppException(400, "该题不支持所选编程语言")

        if not self._can_access_problem(user_id, problem.id):
            raise_forbidden(self.db, user_id, "submission", f"problem_id={problem.id}")

        self._ensure_no_pending_submission(user_id, problem.id)
        acquire_judge_lock(user_id, problem.id)

        is_late = False
        if payload.homework_id is not None:
            is_late = self._validate_homework_submission(user_id, payload.homework_id, payload.problem_id)

        submission = Submission(
            user_id=user_id,
            problem_id=problem.id,
            homework_id=payload.homework_id,
            code=code,
            language=payload.language,
            status=SubmissionStatus.PENDING,
            is_late=is_late,
        )
        self.db.add(submission)
        self._log(user_id, "submit_code", f"submission_id=pending, problem_id={problem.id}")
        self.db.commit()
        self.db.refresh(submission)

        settings = get_settings()
        if settings.use_async_judge:
            from app.tasks.judge_tasks import judge_submission_task

            judge_submission_task.delay(submission.id)
        else:
            self.run_judge(submission.id)
            self.db.refresh(submission)

        test_cases = self._load_test_cases(problem.id)
        return self._to_detail(submission, test_cases)

    def create_arena_submission(
        self,
        user_id: int,
        arena_session_id: int,
        problem_id: int,
        code: str,
        language: str,
    ) -> SubmissionDetail:
        from app.models.arena import ArenaSession, ArenaSessionStatus

        session = self.db.get(ArenaSession, arena_session_id)
        if session is None or session.user_id != user_id:
            raise AppException(404, "擂台会话不存在")
        if session.status != ArenaSessionStatus.IN_PROGRESS:
            raise AppException(410, "擂台已超时，请重新打擂台")
        if session.problem_id != problem_id:
            raise AppException(400, "题目与会话不匹配")

        payload = SubmissionCreateRequest(
            problem_id=problem_id,
            homework_id=None,
            code=code,
            language=language,  # type: ignore[arg-type]
        )
        code_stripped = payload.code.strip()
        validate_submission_code(code_stripped, payload.language)

        problem = (
            self.db.query(Problem)
            .filter(Problem.id == problem_id, Problem.deleted_at.is_(None))
            .first()
        )
        if problem is None:
            raise AppException(404, "题目不存在")
        from app.utils.problem_languages import problem_supports_language

        if not problem_supports_language(problem, payload.language):
            raise AppException(400, "该题不支持所选编程语言")
        if not self._can_access_problem(user_id, problem.id):
            raise_forbidden(self.db, user_id, "submission", f"problem_id={problem.id}")

        test_cases = self._load_test_cases(problem.id)

        stuck_arena = (
            self.db.query(Submission)
            .filter(
                Submission.user_id == user_id,
                Submission.arena_session_id == arena_session_id,
                Submission.status == SubmissionStatus.PENDING,
            )
            .order_by(Submission.id.desc())
            .first()
        )
        if stuck_arena is not None:
            self._finish_pending_judge(stuck_arena, code_stripped)
            self.db.refresh(stuck_arena)
            return self._to_detail(stuck_arena, test_cases)

        self._ensure_no_pending_submission(user_id, problem.id)
        # 擂台每局仅一次提交，由 session 约束；不再占用 30s 判题锁，避免失败后无法重试

        submission = Submission(
            user_id=user_id,
            problem_id=problem.id,
            homework_id=None,
            arena_session_id=arena_session_id,
            code=code_stripped,
            language=payload.language,
            status=SubmissionStatus.PENDING,
            is_late=False,
        )
        self.db.add(submission)
        self._log(user_id, "arena_submit", f"arena_session_id={arena_session_id}")
        self.db.commit()
        self.db.refresh(submission)

        settings = get_settings()
        if settings.use_async_judge:
            from app.tasks.judge_tasks import judge_submission_task

            judge_submission_task.delay(submission.id)
        else:
            self.run_judge(submission.id)
            self.db.refresh(submission)

        return self._to_detail(submission, test_cases)

    def run_judge(self, submission_id: int) -> None:
        submission = self.db.query(Submission).filter(Submission.id == submission_id).first()
        if submission is None:
            return
        if submission.status != SubmissionStatus.PENDING:
            return

        problem = self.db.get(Problem, submission.problem_id)
        if problem is None:
            submission.status = SubmissionStatus.RE
            submission.error_message = "题目不存在"
            self.db.commit()
            return

        test_cases = self._load_test_cases(problem.id)
        if not test_cases:
            submission.status = SubmissionStatus.RE
            submission.error_message = "题目暂无测试用例"
            self.db.commit()
            return

        judge_cases = [
            (index, tc.input_data, tc.expected_output, tc.is_sample)
            for index, tc in enumerate(test_cases)
        ]

        try:
            judge_result = self.judge.judge(
                code=submission.code,
                language=submission.language,
                test_cases=judge_cases,
                time_limit_ms=problem.time_limit_ms,
                memory_limit_mb=problem.memory_limit_mb,
            )
        except Exception as exc:  # noqa: BLE001
            submission.status = SubmissionStatus.RE
            submission.error_message = f"判题服务异常: {str(exc)[:200]}"
            self.db.commit()
            return

        submission.status = judge_result.status
        submission.runtime_ms = judge_result.runtime_ms
        submission.memory_kb = judge_result.memory_kb
        submission.error_message = judge_result.error_message
        submission.compile_output = judge_result.compile_output

        self.db.query(SubmissionCaseResult).filter(
            SubmissionCaseResult.submission_id == submission.id
        ).delete()

        for case_result in judge_result.case_results:
            test_case = test_cases[case_result.case_index] if case_result.case_index < len(test_cases) else None
            self.db.add(
                SubmissionCaseResult(
                    submission_id=submission.id,
                    test_case_id=test_case.id if test_case else None,
                    case_index=case_result.case_index,
                    status=case_result.status,
                    actual_output=case_result.actual_output,
                    runtime_ms=case_result.runtime_ms,
                )
            )

        self.db.commit()
        SUBMISSIONS_TOTAL.labels(submission.status.value).inc()

        if submission.status == SubmissionStatus.AC:
            submitter = self.db.get(User, submission.user_id)
            if submitter is not None and submitter.role == UserRole.STUDENT:
                from app.services.pet_points_service import PetPointsService

                PetPointsService(self.db).try_grant_first_ac(submission)

        if submission.arena_session_id is not None:
            from app.services.arena_service import ArenaService

            ArenaService(self.db).process_after_judge(submission_id)

    def list_submissions(
        self,
        user_id: int,
        problem_id: int,
        homework_id: int | None = None,
        limit: int = 20,
    ) -> list[SubmissionListItem]:
        if not self._can_access_problem(user_id, problem_id):
            raise_forbidden(self.db, user_id, "submission", f"problem_id={problem_id}")

        query = self.db.query(Submission).filter(
            Submission.user_id == user_id,
            Submission.problem_id == problem_id,
        )
        if homework_id is not None:
            query = query.filter(Submission.homework_id == homework_id)

        submissions = query.order_by(Submission.id.desc()).limit(limit).all()
        return [self._to_list_item(item) for item in submissions]

    def get_submission(self, submission_id: int, user_id: int) -> SubmissionDetail:
        submission = self.db.query(Submission).filter(Submission.id == submission_id).first()
        if submission is None:
            raise AppException(404, "提交记录不存在")
        if submission.user_id != user_id:
            raise_forbidden(self.db, user_id, "submission", f"submission_id={submission_id}")

        test_cases = self._load_test_cases(submission.problem_id)
        return self._to_detail(submission, test_cases)

    def get_submission_for_teacher(
        self,
        teacher_id: int,
        homework_id: int,
        submission_id: int,
    ) -> TeacherSubmissionDetail:
        hw_service = HomeworkService(self.db)
        homework = hw_service._get_owned_homework(homework_id, teacher_id)
        submission = self.db.query(Submission).filter(Submission.id == submission_id).first()
        if submission is None:
            raise AppException(404, "提交记录不存在")
        if submission.homework_id != homework.id:
            raise_forbidden(self.db, teacher_id, "submission", f"submission_id={submission_id}")

        target_ids = set(hw_service._target_student_ids(homework))
        if submission.user_id not in target_ids:
            raise_forbidden(self.db, teacher_id, "submission", f"submission_id={submission_id}")

        student = self.db.get(User, submission.user_id)
        display_name = (student.display_name or student.account if student else None) or f"学生#{submission.user_id}"
        account = student.account if student else ""

        test_cases = self._load_test_cases(submission.problem_id)
        detail = self._to_detail(submission, test_cases)
        return TeacherSubmissionDetail(
            **detail.model_dump(),
            code=submission.code,
            student_display_name=display_name,
            student_account=account,
        )

    def _load_test_cases(self, problem_id: int) -> list[TestCase]:
        return (
            self.db.query(TestCase)
            .filter(TestCase.problem_id == problem_id, TestCase.deleted_at.is_(None))
            .order_by(TestCase.sort_order.asc(), TestCase.id.asc())
            .all()
        )

    def _can_access_problem(self, user_id: int, problem_id: int) -> bool:
        from app.services.problem_access import ProblemAccessHelper

        user = self.db.get(User, user_id)
        problem = (
            self.db.query(Problem)
            .filter(Problem.id == problem_id, Problem.deleted_at.is_(None))
            .first()
        )
        if problem is None or user is None:
            return False
        helper = ProblemAccessHelper(self.db)
        if user.role == UserRole.TEACHER:
            return helper.teacher_can_preview_problem(user_id, problem)
        return helper.student_can_access_problem(user_id, problem)

    def _student_teacher_ids(self, student_id: int) -> list[int]:
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

    def _validate_homework_submission(self, student_id: int, homework_id: int, problem_id: int) -> bool:
        homework = (
            self.db.query(Homework)
            .filter(Homework.id == homework_id, Homework.deleted_at.is_(None))
            .first()
        )
        if homework is None:
            raise AppException(404, "作业不存在")

        class_ids = [
            row.class_id
            for row in self.db.query(ClassEnrollment)
            .filter(ClassEnrollment.student_id == student_id, ClassEnrollment.deleted_at.is_(None))
            .all()
        ]
        hw_service = HomeworkService(self.db)
        if not hw_service._is_visible_to_student(homework, student_id, class_ids):
            raise_forbidden(self.db, student_id, "submission", f"homework_id={homework_id}")

        status = hw_service.compute_status(homework)
        if status == "未开始":
            raise AppException(400, "作业尚未开始")
        if status == "已撤回":
            raise AppException(400, "作业已撤回，无法提交")

        is_late = False
        if status == "已截止":
            if not homework.allow_late_submission:
                raise AppException(400, "作业已截止，无法提交")
            is_late = True

        problem_linked = (
            self.db.query(HomeworkProblem)
            .filter(HomeworkProblem.homework_id == homework_id, HomeworkProblem.problem_id == problem_id)
            .first()
        )
        if problem_linked is None:
            raise AppException(400, "该题目不属于此作业")

        return is_late

    @staticmethod
    def _to_list_item(submission: Submission) -> SubmissionListItem:
        return SubmissionListItem(
            id=submission.id,
            problem_id=submission.problem_id,
            homework_id=submission.homework_id,
            language=submission.language,
            status=submission.status.value,
            runtime_ms=submission.runtime_ms,
            is_late=submission.is_late,
            created_at=submission.created_at,
        )

    def _to_detail(self, submission: Submission, test_cases: list[TestCase]) -> SubmissionDetail:
        sample_map = {index: tc.is_sample for index, tc in enumerate(test_cases)}
        case_results = [
            SubmissionCaseResultItem(
                case_index=case.case_index,
                status=case.status.value,
                is_sample=sample_map.get(case.case_index, False),
                actual_output=case.actual_output,
                runtime_ms=case.runtime_ms,
            )
            for case in sorted(submission.case_results, key=lambda item: item.case_index)
        ]
        ai_text, ai_lines = unpack_ai_analysis(submission.ai_analysis)
        from app.services.pet_points_service import PetPointsService

        submitter = self.db.get(User, submission.user_id)
        if submitter is not None and submitter.role != UserRole.STUDENT:
            points_awarded, points_balance = None, None
        else:
            points_awarded, points_balance = PetPointsService(self.db).submission_points_fields(submission.id)
        return SubmissionDetail(
            id=submission.id,
            problem_id=submission.problem_id,
            homework_id=submission.homework_id,
            language=submission.language,
            status=submission.status.value,
            runtime_ms=submission.runtime_ms,
            memory_kb=submission.memory_kb,
            is_late=submission.is_late,
            error_message=submission.error_message,
            compile_output=submission.compile_output,
            ai_analysis=ai_text or None,
            ai_highlight_lines=ai_lines,
            case_results=case_results,
            created_at=submission.created_at,
            points_awarded=points_awarded,
            points_balance=points_balance,
        )

    @staticmethod
    def list_ac_solvers(db: Session, problem_id: int) -> list[ProblemAcSolverItem]:
        rows = (
            db.query(
                Submission.user_id,
                func.min(Submission.created_at).label("first_ac_at"),
            )
            .filter(
                Submission.problem_id == problem_id,
                Submission.status == SubmissionStatus.AC,
            )
            .group_by(Submission.user_id)
            .order_by(func.min(Submission.created_at))
            .all()
        )
        if not rows:
            return []
        user_ids = [int(row.user_id) for row in rows]
        users = (
            db.query(User)
            .filter(User.id.in_(user_ids), User.role == UserRole.STUDENT)
            .all()
        )
        user_map = {user.id: user for user in users}
        items: list[ProblemAcSolverItem] = []
        for row in rows:
            user = user_map.get(int(row.user_id))
            if user is None:
                continue
            items.append(
                ProblemAcSolverItem(
                    user_id=user.id,
                    display_name=user.display_name or user.account,
                    account=user.account,
                    student_no=user.student_no,
                    first_ac_at=row.first_ac_at,
                )
            )
        return items

    @staticmethod
    def _student_submissions_filter(problem_id: int):
        return (
            Submission.problem_id == problem_id,
            User.role == UserRole.STUDENT,
        )

    @staticmethod
    def teacher_passed_problem_ids(db: Session, teacher_id: int) -> list[int]:
        rows = (
            db.query(Submission.problem_id)
            .filter(
                Submission.user_id == teacher_id,
                Submission.status == SubmissionStatus.AC,
            )
            .distinct()
            .all()
        )
        return [int(row[0]) for row in rows]

    @staticmethod
    def apply_my_passed_filter(query, db: Session, viewer_id: int, my_passed: bool):
        if not my_passed:
            return query
        passed_ids = SubmissionService.teacher_passed_problem_ids(db, viewer_id)
        if not passed_ids:
            return query.filter(Problem.id < 0)
        return query.filter(Problem.id.in_(passed_ids))

    @staticmethod
    def compute_pass_rate(db: Session, problem_id: int) -> tuple[float, int]:
        valid_count = (
            db.query(func.count(Submission.id))
            .join(User, User.id == Submission.user_id)
            .filter(
                *SubmissionService._student_submissions_filter(problem_id),
                Submission.status.in_(VALID_SUBMISSION_STATUSES),
            )
            .scalar()
            or 0
        )
        ac_count = (
            db.query(func.count(Submission.id))
            .join(User, User.id == Submission.user_id)
            .filter(
                *SubmissionService._student_submissions_filter(problem_id),
                Submission.status == SubmissionStatus.AC,
            )
            .scalar()
            or 0
        )
        pass_rate = round(ac_count / valid_count * 100, 1) if valid_count > 0 else 0.0
        return pass_rate, valid_count

    @staticmethod
    def student_best_status(
        db: Session,
        user_id: int,
        problem_id: int,
        homework_id: int | None = None,
    ) -> SubmissionStatus | None:
        query = db.query(Submission).filter(
            Submission.user_id == user_id,
            Submission.problem_id == problem_id,
            Submission.status.in_(VALID_SUBMISSION_STATUSES),
        )
        if homework_id is not None:
            query = query.filter(Submission.homework_id == homework_id)

        submissions = query.order_by(Submission.id.desc()).all()
        if not submissions:
            return None

        priority = {
            SubmissionStatus.AC: 5,
            SubmissionStatus.WA: 4,
            SubmissionStatus.TLE: 3,
            SubmissionStatus.RE: 2,
        }
        best = max(submissions, key=lambda item: priority.get(item.status, 0))
        return best.status

    @staticmethod
    def student_submission_count(
        db: Session,
        user_id: int,
        problem_id: int,
        homework_id: int | None = None,
    ) -> int:
        query = db.query(func.count(Submission.id)).filter(
            Submission.user_id == user_id,
            Submission.problem_id == problem_id,
            Submission.status.in_(VALID_SUBMISSION_STATUSES),
        )
        if homework_id is not None:
            query = query.filter(Submission.homework_id == homework_id)
        return query.scalar() or 0

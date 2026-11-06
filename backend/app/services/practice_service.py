from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.forbidden import raise_forbidden
from app.models.class_model import ClassEnrollment, TeachingClass
from app.models.homework import Homework, HomeworkProblem
from app.models.problem import Problem, ProblemScope, PublicPublishStatus, TestCase
from app.models.submission import Submission, SubmissionStatus
from app.models.problem import ProblemDifficulty
from app.schemas.practice_schema import (
    KnowledgePointDetailResponse,
    KnowledgePointDifficultyProgress,
    KnowledgePointListResponse,
    KnowledgePointTagItem,
    PracticeProblemDetail,
    PracticeProblemListItem,
    PracticeProblemListResponse,
    StudentHomeworkDetail,
    StudentHomeworkProblemItem,
    StudentTestCaseItem,
)
from app.services.homework_service import HomeworkService
from app.services.problem_access import ProblemAccessHelper
from app.knowledge.catalog import get_entry, sorted_entries
from app.utils.problem_knowledge import (
    KNOWLEDGE_TOPIC_ALIASES,
    apply_knowledge_point_filter,
    get_problem_knowledge_points,
    resolve_knowledge_topic_name,
)
from app.utils.problem_languages import apply_language_filter
from app.services.submission_service import SubmissionService, VALID_SUBMISSION_STATUSES


class PracticeService:
    def __init__(self, db: Session):
        self.db = db

    def _public_catalog_query(self):
        return ProblemAccessHelper(self.db).list_public_catalog_query()

    @staticmethod
    def _knowledge_point_tags(problem: Problem) -> list[str]:
        tags = get_problem_knowledge_points(problem)
        return tags if tags else ["未分类"]

    @classmethod
    def _apply_knowledge_point_filter(cls, query, knowledge_point: str):
        return apply_knowledge_point_filter(query, knowledge_point)

    @staticmethod
    def _difficulty_bucket(difficulty: ProblemDifficulty) -> str:
        if difficulty in (ProblemDifficulty.BEGINNER, ProblemDifficulty.EASY):
            return "简单"
        if difficulty == ProblemDifficulty.MEDIUM:
            return "中等"
        return "困难"

    def _student_problem_progress(self, student_id: int, problem_ids: list[int]) -> tuple[int, int]:
        if not problem_ids:
            return 0, 0
        solved = 0
        attempting = 0
        for pid in problem_ids:
            best = SubmissionService.student_best_status(self.db, student_id, pid)
            if best == SubmissionStatus.AC:
                solved += 1
            elif best is not None:
                attempting += 1
        return solved, attempting

    def list_knowledge_points(self, student_id: int) -> KnowledgePointListResponse:
        base_query = self._public_catalog_query()
        problems = base_query.order_by(Problem.id.asc()).all()
        all_ids = [p.id for p in problems]
        solved_total, _ = self._student_problem_progress(student_id, all_ids)
        items = [
            KnowledgePointTagItem(
                name=entry.name,
                problem_count=self._apply_knowledge_point_filter(base_query, entry.name).count(),
            )
            for entry in sorted_entries()
            if entry.name != "未分类" and entry.name not in KNOWLEDGE_TOPIC_ALIASES
        ]
        return KnowledgePointListResponse(
            items=items,
            total_problems=len(problems),
            solved_count=solved_total,
        )

    def get_knowledge_point_detail(self, student_id: int, knowledge_point: str) -> KnowledgePointDetailResponse:
        name = resolve_knowledge_topic_name(knowledge_point.strip())
        entry = get_entry(name)
        if entry is None:
            raise AppException(404, "知识点不存在")
        query = self._apply_knowledge_point_filter(self._public_catalog_query(), name)
        problems = query.order_by(Problem.id.asc()).all()

        problem_ids = [p.id for p in problems]
        solved_count, attempting_count = self._student_problem_progress(student_id, problem_ids)

        bucket_stats: dict[str, dict[str, int]] = {
            "简单": {"total": 0, "solved": 0, "attempting": 0},
            "中等": {"total": 0, "solved": 0, "attempting": 0},
            "困难": {"total": 0, "solved": 0, "attempting": 0},
        }
        first_untried: int | None = None
        for problem in problems:
            bucket = self._difficulty_bucket(problem.difficulty)
            bucket_stats[bucket]["total"] += 1
            best = SubmissionService.student_best_status(self.db, student_id, problem.id)
            if best == SubmissionStatus.AC:
                bucket_stats[bucket]["solved"] += 1
            elif best is not None:
                bucket_stats[bucket]["attempting"] += 1
            elif first_untried is None:
                first_untried = problem.id

        difficulty_progress = [
            KnowledgePointDifficultyProgress(
                label=label,
                total=stats["total"],
                solved=stats["solved"],
                attempting=stats["attempting"],
            )
            for label, stats in bucket_stats.items()
            if stats["total"] > 0
        ]

        return KnowledgePointDetailResponse(
            name=name,
            problem_count=len(problems),
            solved_count=solved_count,
            attempting_count=attempting_count,
            description=entry.summary,
            content_markdown=entry.content_markdown,
            difficulty_progress=difficulty_progress,
            first_untried_problem_id=first_untried or (problems[0].id if problems else None),
            first_problem_id=problems[0].id if problems else None,
        )

    @staticmethod
    def _difficulty_sort_key():
        return case(
            (Problem.difficulty == ProblemDifficulty.BEGINNER, 0),
            (Problem.difficulty == ProblemDifficulty.EASY, 1),
            (Problem.difficulty == ProblemDifficulty.MEDIUM, 2),
            (Problem.difficulty == ProblemDifficulty.HARD, 3),
            else_=99,
        )

    def list_problems(
        self,
        student_id: int,
        page: int = 1,
        page_size: int = 20,
        keyword: str | None = None,
        difficulty: str | None = None,
        knowledge_point: str | None = None,
        language: str | None = None,
        sort_by: str = "id",
        sort_order: str = "asc",
    ) -> PracticeProblemListResponse:
        query = self._public_catalog_query()
        if keyword:
            like = f"%{keyword.strip()}%"
            if keyword.strip().isdigit():
                query = query.filter((Problem.title.ilike(like)) | (Problem.id == int(keyword.strip())))
            else:
                query = query.filter(Problem.title.ilike(like))
        if difficulty:
            query = query.filter(Problem.difficulty == ProblemDifficulty(difficulty))
        if knowledge_point:
            query = self._apply_knowledge_point_filter(query, knowledge_point)
        if language:
            query = apply_language_filter(query, language)

        total = query.count()
        order_asc = sort_order.lower() != "desc"
        if sort_by == "difficulty":
            diff_key = self._difficulty_sort_key()
            primary = diff_key.asc() if order_asc else diff_key.desc()
            secondary = Problem.id.asc()
            order_clause = (primary, secondary)
        else:
            primary = Problem.id.asc() if order_asc else Problem.id.desc()
            order_clause = (primary,)

        problems = (
            query.order_by(*order_clause)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        items = [self._to_practice_list_item(problem, student_id) for problem in problems]
        return PracticeProblemListResponse(items=items, total=total, page=page, page_size=page_size)

    def get_problem(self, student_id: int, problem_id: int) -> PracticeProblemDetail:
        problem = (
            self.db.query(Problem)
            .filter(Problem.id == problem_id, Problem.deleted_at.is_(None))
            .first()
        )
        if problem is None or not ProblemAccessHelper(self.db).student_can_access_problem(student_id, problem):
            raise_forbidden(self.db, student_id, "practice", f"problem_id={problem_id}")

        pass_rate, submission_count = SubmissionService.compute_pass_rate(self.db, problem.id)
        best_status = SubmissionService.student_best_status(self.db, student_id, problem.id)
        test_cases = self._student_test_cases(problem)

        return self._to_practice_detail(
            problem,
            test_cases=test_cases,
            pass_rate=pass_rate,
            submission_count=submission_count,
            my_best_status=best_status.value if best_status else None,
        )

    def get_problem_for_teacher(self, teacher_id: int, problem_id: int) -> PracticeProblemDetail:
        problem = (
            self.db.query(Problem)
            .filter(Problem.id == problem_id, Problem.deleted_at.is_(None))
            .first()
        )
        if problem is None or not ProblemAccessHelper(self.db).teacher_can_preview_problem(
            teacher_id, problem
        ):
            raise_forbidden(self.db, teacher_id, "practice", f"problem_id={problem_id}")

        pass_rate, submission_count = SubmissionService.compute_pass_rate(self.db, problem.id)
        test_cases = self._student_test_cases(problem)
        return self._to_practice_detail(
            problem,
            test_cases=test_cases,
            pass_rate=pass_rate,
            submission_count=submission_count,
            my_best_status=None,
        )

    def get_problem_for_admin(self, admin_id: int, problem_id: int) -> PracticeProblemDetail:
        problem = (
            self.db.query(Problem)
            .filter(Problem.id == problem_id, Problem.deleted_at.is_(None))
            .first()
        )
        if problem is None or problem.scope != ProblemScope.PUBLIC:
            raise_forbidden(self.db, admin_id, "practice", f"problem_id={problem_id}")
        pass_rate, submission_count = SubmissionService.compute_pass_rate(self.db, problem.id)
        test_cases = self._student_test_cases(problem)
        return self._to_practice_detail(
            problem,
            test_cases=test_cases,
            pass_rate=pass_rate,
            submission_count=submission_count,
            my_best_status=None,
        )

    def _to_practice_detail(
        self,
        problem: Problem,
        *,
        test_cases: list,
        pass_rate: float,
        submission_count: int,
        my_best_status: str | None,
    ) -> PracticeProblemDetail:
        langs = self._problem_languages(problem)
        access = ProblemAccessHelper(self.db)
        from app.utils.problem_images import get_problem_image_urls

        return PracticeProblemDetail(
            id=problem.id,
            title=problem.title,
            description=problem.description,
            image_urls=get_problem_image_urls(problem),
            language=langs[0],
            languages=langs,
            difficulty=problem.difficulty.value,
            gesp_level=problem.gesp_level.value,
            knowledge_point=problem.knowledge_point,
            input_format=problem.input_format,
            output_format=problem.output_format,
            sample_input=problem.sample_input,
            sample_output=problem.sample_output,
            hint=problem.hint,
            time_limit_ms=problem.time_limit_ms,
            memory_limit_mb=problem.memory_limit_mb,
            test_cases=test_cases,
            pass_rate=pass_rate,
            submission_count=submission_count,
            my_best_status=my_best_status,
            is_public_catalog=access.is_public_catalog_problem(problem),
        )

    def get_student_homework(self, student_id: int, homework_id: int) -> StudentHomeworkDetail:
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
            raise_forbidden(self.db, student_id, "practice", f"homework_id={homework_id}")

        status = hw_service.compute_status(homework)
        class_name = hw_service._primary_class_name(homework, class_ids)

        sorted_links = sorted(homework.problem_links, key=lambda item: item.sort_order)
        problems: list[StudentHomeworkProblemItem] = []
        ac_count = 0
        for link in sorted_links:
            problem = self.db.get(Problem, link.problem_id)
            if problem is None:
                continue
            best = SubmissionService.student_best_status(
                self.db, student_id, problem.id, homework_id=homework.id
            )
            sub_count = SubmissionService.student_submission_count(
                self.db, student_id, problem.id, homework_id=homework.id
            )
            if best == SubmissionStatus.AC:
                ac_count += 1
            problems.append(
                StudentHomeworkProblemItem(
                    id=problem.id,
                    title=problem.title,
                    language=problem.language.value,
                    difficulty=problem.difficulty.value,
                    best_status=best.value if best else None,
                    submission_count=sub_count,
                )
            )

        total = len(problems)
        progress = f"{ac_count}/{total} 已完成" if total else "0/0 已完成"
        has_unread_update = hw_service._has_unread_update(homework, student_id)
        update_notice = (
            "老师已更新该作业的题目或说明，请留意下列题目列表。"
            if has_unread_update
            else None
        )

        return StudentHomeworkDetail(
            id=homework.id,
            title=homework.title,
            description=homework.description,
            status=status,
            class_name=class_name,
            start_time=homework.start_time,
            end_time=homework.end_time,
            allow_late_submission=homework.allow_late_submission,
            progress=progress,
            problems=problems,
            has_unread_update=has_unread_update,
            update_notice=update_notice,
        )

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

    def _to_practice_list_item(self, problem: Problem, student_id: int) -> PracticeProblemListItem:
        pass_rate, submission_count = SubmissionService.compute_pass_rate(self.db, problem.id)
        best = SubmissionService.student_best_status(self.db, student_id, problem.id)
        sub_count = SubmissionService.student_submission_count(self.db, student_id, problem.id)

        if best == SubmissionStatus.AC:
            my_status = "passed"
        elif best is not None:
            my_status = "failed"
        else:
            my_status = "untried"

        langs = self._problem_languages(problem)
        return PracticeProblemListItem(
            id=problem.id,
            title=problem.title,
            language=langs[0],
            languages=langs,
            difficulty=problem.difficulty.value,
            gesp_level=problem.gesp_level.value,
            knowledge_point=problem.knowledge_point,
            pass_rate=pass_rate,
            submission_count=submission_count,
            my_status=my_status,
            my_submission_count=sub_count,
            best_status=best.value if best else None,
        )

    @staticmethod
    def _problem_languages(problem: Problem) -> list[str]:
        from app.utils.problem_languages import get_problem_languages

        return get_problem_languages(problem)

    def _student_test_cases(self, problem: Problem) -> list[StudentTestCaseItem]:
        cases = (
            self.db.query(TestCase)
            .filter(TestCase.problem_id == problem.id, TestCase.deleted_at.is_(None))
            .order_by(TestCase.sort_order.asc(), TestCase.id.asc())
            .all()
        )
        return [
            StudentTestCaseItem(
                id=case.id,
                input_data=case.input_data if case.is_sample else None,
                expected_output=case.expected_output if case.is_sample else None,
                is_sample=case.is_sample,
                sort_order=case.sort_order,
            )
            for case in cases
        ]

    @staticmethod
    def homework_submission_stats(db: Session, homework_id: int) -> tuple[int, int, int]:
        """Return submitted_count, correct_count, wrong_count for a homework."""
        problem_ids = [
            row.problem_id
            for row in db.query(HomeworkProblem.problem_id)
            .filter(HomeworkProblem.homework_id == homework_id)
            .all()
        ]
        if not problem_ids:
            return 0, 0, 0

        student_ids_subquery = (
            db.query(Submission.user_id)
            .filter(
                Submission.homework_id == homework_id,
                Submission.is_late.is_(False),
                Submission.status.in_(VALID_SUBMISSION_STATUSES),
            )
            .distinct()
        )
        submitted_count = student_ids_subquery.count()

        ac_students = (
            db.query(Submission.user_id)
            .filter(
                Submission.homework_id == homework_id,
                Submission.is_late.is_(False),
                Submission.status == SubmissionStatus.AC,
            )
            .distinct()
            .count()
        )
        wrong_count = max(submitted_count - ac_students, 0)
        return submitted_count, ac_students, wrong_count

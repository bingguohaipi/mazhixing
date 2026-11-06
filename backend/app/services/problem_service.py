from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.services.practice_service import PracticeService

from app.core.exceptions import AppException
from app.core.forbidden import raise_forbidden
from app.models.audit import OperationLog
from app.models.problem import (
    GespLevel,
    Problem,
    ProblemDifficulty,
    ProblemLanguage,
    ProblemScope,
    PublicPublishStatus,
    TestCase,
)
from pydantic import ValidationError

from app.schemas.problem_schema import (
    ProblemCreateRequest,
    ProblemDetail,
    ProblemImportFailedRow,
    ProblemImportResult,
    ProblemListItem,
    ProblemListResponse,
    ProblemUpdateRequest,
    TestCaseItem,
)
from app.services.submission_service import SubmissionService
from app.utils.problem_images import get_problem_image_urls, normalize_problem_image_urls


class ProblemService:
    def __init__(self, db: Session):
        self.db = db

    def _log(self, user_id: int, action: str, detail: str | None = None) -> None:
        self.db.add(OperationLog(user_id=user_id, action=action, resource="problem", detail=detail))

    def _get_owned_problem(self, problem_id: int, teacher_id: int) -> Problem:
        problem = (
            self.db.query(Problem)
            .filter(
                Problem.id == problem_id,
                Problem.teacher_id == teacher_id,
                Problem.deleted_at.is_(None),
            )
            .first()
        )
        if problem is None:
            raise_forbidden(self.db, teacher_id, "problem", f"problem_id={problem_id}")
        return problem

    def _get_owned_private_problem(self, problem_id: int, teacher_id: int) -> Problem:
        problem = self._get_owned_problem(problem_id, teacher_id)
        if problem.scope != ProblemScope.PRIVATE:
            raise AppException(403, "仅可管理自有题库中的题目", status_code=403)
        return problem

    def list_problems(
        self,
        teacher_id: int,
        page: int = 1,
        page_size: int = 20,
        keyword: str | None = None,
        language: str | None = None,
        difficulty: str | None = None,
        gesp_level: str | None = None,
        knowledge_point: str | None = None,
        sort_by: str = "id",
        sort_order: str = "asc",
        my_passed: bool = False,
    ) -> ProblemListResponse:
        query = self.db.query(Problem).filter(
            Problem.teacher_id == teacher_id,
            Problem.scope == ProblemScope.PRIVATE,
            Problem.deleted_at.is_(None),
        )

        if keyword:
            raw = keyword.strip()
            if raw.startswith("#"):
                raw = raw[1:].strip()
            like = f"%{raw}%"
            if raw.isdigit():
                num = int(raw)
                query = query.filter((Problem.title.ilike(like)) | (Problem.private_no == num))
            else:
                query = query.filter(Problem.title.ilike(like))

        if language:
            from app.utils.problem_languages import apply_language_filter

            query = apply_language_filter(query, language)
        if difficulty:
            query = query.filter(Problem.difficulty == ProblemDifficulty(difficulty))
        if gesp_level:
            query = query.filter(Problem.gesp_level == GespLevel(gesp_level))
        if knowledge_point:
            query = PracticeService._apply_knowledge_point_filter(query, knowledge_point.strip())

        if my_passed:
            query = SubmissionService.apply_my_passed_filter(query, self.db, teacher_id, True)

        total = query.count()
        order_asc = sort_order.lower() != "desc"
        if sort_by == "difficulty":
            diff_key = PracticeService._difficulty_sort_key()
            primary = diff_key.asc() if order_asc else diff_key.desc()
            secondary = Problem.private_no.asc().nulls_last(), Problem.id.asc()
            order_clause = (primary, *secondary)
        else:
            primary = Problem.private_no.asc() if order_asc else Problem.private_no.desc()
            secondary = Problem.id.asc() if order_asc else Problem.id.desc()
            order_clause = (primary.nulls_last(), secondary)

        problems = (
            query.order_by(*order_clause)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        items = [self._to_list_item(problem) for problem in problems]
        return ProblemListResponse(items=items, total=total, page=page, page_size=page_size)

    def get_problem(self, problem_id: int, teacher_id: int) -> ProblemDetail:
        problem = self._get_owned_private_problem(problem_id, teacher_id)
        return self._to_detail(problem)

    def _next_private_no(self, teacher_id: int) -> int:
        current_max = (
            self.db.query(func.max(Problem.private_no))
            .filter(
                Problem.teacher_id == teacher_id,
                Problem.scope == ProblemScope.PRIVATE,
                Problem.deleted_at.is_(None),
            )
            .scalar()
        )
        return int(current_max or 0) + 1

    def create_problem(self, teacher_id: int, payload: ProblemCreateRequest) -> ProblemDetail:
        problem = Problem(
            teacher_id=teacher_id,
            scope=ProblemScope.PRIVATE,
            private_no=self._next_private_no(teacher_id),
            publish_status=PublicPublishStatus.PUBLISHED,
            title=payload.title.strip(),
            description=payload.description.strip(),
            difficulty=ProblemDifficulty(payload.difficulty),
            gesp_level=GespLevel(payload.gesp_level or "GESP1"),
            language=ProblemLanguage.PYTHON,
            input_format=payload.input_format,
            output_format=payload.output_format,
            sample_input=payload.sample_input,
            sample_output=payload.sample_output,
            reference_answer=payload.reference_answer,
            hint=payload.hint,
            time_limit_ms=payload.time_limit_ms,
            memory_limit_mb=payload.memory_limit_mb,
            created_by=teacher_id,
            updated_by=teacher_id,
            image_urls=normalize_problem_image_urls(payload.image_urls),
        )
        from app.utils.problem_knowledge import apply_knowledge_points_to_problem
        from app.utils.problem_languages import apply_languages_to_problem

        apply_languages_to_problem(problem, payload.languages)
        apply_knowledge_points_to_problem(problem, payload.knowledge_points)
        self.db.add(problem)
        self.db.flush()
        self._replace_test_cases(problem.id, payload.test_cases)
        self._log(teacher_id, "create_problem", f"problem_id={problem.id}, title={problem.title}")
        self.db.commit()
        self.db.refresh(problem)
        return self._to_detail(problem)

    def update_problem(self, problem_id: int, teacher_id: int, payload: ProblemUpdateRequest) -> ProblemDetail:
        problem = self._get_owned_private_problem(problem_id, teacher_id)
        updates = payload.model_dump(
            exclude_unset=True,
            exclude={"test_cases", "knowledge_points", "languages", "image_urls"},
        )
        if payload.image_urls is not None:
            problem.image_urls = normalize_problem_image_urls(payload.image_urls)
        if payload.languages is not None:
            from app.utils.problem_languages import apply_languages_to_problem

            apply_languages_to_problem(problem, payload.languages)
        if payload.knowledge_points is not None:
            from app.utils.problem_knowledge import apply_knowledge_points_to_problem

            apply_knowledge_points_to_problem(problem, payload.knowledge_points)
        for field, value in updates.items():
            if field in ("language", "difficulty", "gesp_level") and value is not None:
                enum_cls = {
                    "language": ProblemLanguage,
                    "difficulty": ProblemDifficulty,
                    "gesp_level": GespLevel,
                }[field]
                value = enum_cls(value)
            elif isinstance(value, str):
                value = value.strip() if field != "description" else value.strip()
            setattr(problem, field, value)

        if payload.test_cases is not None:
            self._replace_test_cases(problem.id, payload.test_cases)

        problem.updated_by = teacher_id
        self._log(teacher_id, "update_problem", f"problem_id={problem_id}")
        self.db.commit()
        self.db.refresh(problem)
        return self._to_detail(problem)

    def import_problems(self, teacher_id: int, raw_items: list[dict]) -> ProblemImportResult:
        if len(raw_items) > 50:
            raise AppException(400, "单次最多导入 50 道题")

        created_ids: list[int] = []
        failed: list[ProblemImportFailedRow] = []
        for index, raw in enumerate(raw_items, start=1):
            title = str(raw.get("title") or "")
            try:
                payload = ProblemCreateRequest.model_validate(raw)
                detail = self.create_problem(teacher_id, payload)
                created_ids.append(detail.id)
            except ValidationError as exc:
                reason = exc.errors()[0].get("msg", "字段校验失败")
                failed.append(ProblemImportFailedRow(row=index, title=title or None, reason=str(reason)))
            except AppException as exc:
                failed.append(ProblemImportFailedRow(row=index, title=title or None, reason=exc.message))
            except Exception:
                failed.append(ProblemImportFailedRow(row=index, title=title or None, reason="导入失败"))

        self._log(teacher_id, "import_problems", f"success={len(created_ids)}, failed={len(failed)}")
        return ProblemImportResult(
            success_count=len(created_ids),
            failed=failed,
            created_ids=created_ids,
        )

    def export_lesson_pack(self, teacher_id: int, problem_ids: list[int]) -> str:
        if not problem_ids:
            raise AppException(400, "请至少选择一道题目")
        if len(problem_ids) > 50:
            raise AppException(400, "单次最多导出 50 道题")

        lines = ["# 码智星备课包", ""]
        for problem_id in problem_ids:
            detail = self.get_problem(problem_id, teacher_id)
            lines.extend([
                f"## #{detail.id} {detail.title}",
                f"- 语言：{detail.language} | 难度：{detail.difficulty} | GESP：{detail.gesp_level}",
            ])
            if detail.knowledge_point:
                lines.append(f"- 知识点：{detail.knowledge_point}")
            lines.extend(["", "### 题目描述", detail.description, ""])
            if detail.sample_input or detail.sample_output:
                lines.extend([
                    "### 样例",
                    f"输入：\n```\n{detail.sample_input or ''}\n```",
                    f"输出：\n```\n{detail.sample_output or ''}\n```",
                    "",
                ])
            sample_cases = [tc for tc in detail.test_cases if tc.is_sample]
            if sample_cases:
                lines.append("### 测试用例（样例）")
                for idx, test_case in enumerate(sample_cases, start=1):
                    lines.extend([
                        f"用例 {idx}：",
                        f"输入：\n```\n{test_case.input_data}\n```",
                        f"期望输出：\n```\n{test_case.expected_output}\n```",
                        "",
                    ])
            if detail.reference_answer:
                lines.extend(["### 参考答案", f"```\n{detail.reference_answer}\n```", ""])
            if detail.hint:
                lines.extend(["### 提示", detail.hint, ""])
            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def delete_problem(self, problem_id: int, teacher_id: int) -> None:
        from app.models.homework import HomeworkProblem

        problem = self._get_owned_private_problem(problem_id, teacher_id)
        linked_homework = (
            self.db.query(func.count(HomeworkProblem.id))
            .filter(HomeworkProblem.problem_id == problem_id)
            .scalar()
            or 0
        )
        if linked_homework > 0:
            raise AppException(400, "该题已被作业引用，无法删除")
        now = datetime.now(timezone.utc)
        problem.deleted_at = now
        problem.updated_by = teacher_id
        for test_case in self._active_test_cases(problem.id):
            test_case.deleted_at = now
        self._log(teacher_id, "delete_problem", f"problem_id={problem_id}")
        self.db.commit()

    def _replace_test_cases(self, problem_id: int, test_cases: list) -> None:
        now = datetime.now(timezone.utc)
        for existing in self._active_test_cases(problem_id):
            existing.deleted_at = now

        for index, test_case in enumerate(test_cases):
            self.db.add(
                TestCase(
                    problem_id=problem_id,
                    input_data=test_case.input_data.strip(),
                    expected_output=test_case.expected_output.strip(),
                    is_sample=test_case.is_sample,
                    sort_order=test_case.sort_order if test_case.sort_order else index,
                )
            )

    def _active_test_cases(self, problem_id: int) -> list[TestCase]:
        return (
            self.db.query(TestCase)
            .filter(TestCase.problem_id == problem_id, TestCase.deleted_at.is_(None))
            .order_by(TestCase.sort_order.asc(), TestCase.id.asc())
            .all()
        )

    def _test_case_count(self, problem_id: int) -> int:
        return (
            self.db.query(func.count(TestCase.id))
            .filter(TestCase.problem_id == problem_id, TestCase.deleted_at.is_(None))
            .scalar()
            or 0
        )

    def _to_list_item(self, problem: Problem) -> ProblemListItem:
        count = self._test_case_count(problem.id)
        pass_rate, submission_count = SubmissionService.compute_pass_rate(self.db, problem.id)
        return ProblemListItem(
            id=problem.id,
            private_no=problem.private_no,
            title=problem.title,
            language=self._languages(problem)[0],
            languages=self._languages(problem),
            difficulty=problem.difficulty.value,
            gesp_level=problem.gesp_level.value,
            knowledge_point=problem.knowledge_point,
            knowledge_points=self._knowledge_points(problem),
            test_case_count=count,
            is_publishable=count > 0,
            pass_rate=pass_rate,
            submission_count=submission_count,
            created_at=problem.created_at,
        )

    @staticmethod
    def _knowledge_points(problem: Problem) -> list[str]:
        from app.utils.problem_knowledge import get_problem_knowledge_points

        return get_problem_knowledge_points(problem)

    @staticmethod
    def _languages(problem: Problem) -> list[str]:
        from app.utils.problem_languages import get_problem_languages

        return get_problem_languages(problem)

    def _to_detail(self, problem: Problem) -> ProblemDetail:
        test_cases = self._active_test_cases(problem.id)
        count = len(test_cases)
        pass_rate, submission_count = SubmissionService.compute_pass_rate(self.db, problem.id)
        return ProblemDetail(
            id=problem.id,
            private_no=problem.private_no,
            title=problem.title,
            description=problem.description,
            image_urls=get_problem_image_urls(problem),
            language=self._languages(problem)[0],
            languages=self._languages(problem),
            difficulty=problem.difficulty.value,
            gesp_level=problem.gesp_level.value,
            knowledge_point=problem.knowledge_point,
            knowledge_points=self._knowledge_points(problem),
            input_format=problem.input_format,
            output_format=problem.output_format,
            sample_input=problem.sample_input,
            sample_output=problem.sample_output,
            reference_answer=problem.reference_answer,
            hint=problem.hint,
            time_limit_ms=problem.time_limit_ms,
            memory_limit_mb=problem.memory_limit_mb,
            test_cases=[
                TestCaseItem(
                    id=tc.id,
                    input_data=tc.input_data,
                    expected_output=tc.expected_output,
                    is_sample=tc.is_sample,
                    sort_order=tc.sort_order,
                )
                for tc in test_cases
            ],
            is_publishable=count > 0,
            pass_rate=pass_rate,
            submission_count=submission_count,
            created_at=problem.created_at,
            updated_at=problem.updated_at,
        )

import json
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.utils.io_text import normalize_io_text
from app.core.security import hash_password
from app.models.audit import OperationLog, ParentStudentBinding
from app.models.class_model import ClassEnrollment, TeachingClass
from app.models.homework import HomeworkProblem
from app.models.problem import (
    GespLevel,
    Problem,
    ProblemDifficulty,
    ProblemLanguage,
    ProblemScope,
    PublicPublishStatus,
    TestCase,
)
from app.models.user import User, UserRole
from app.schemas.auth import validate_phone
from app.schemas.admin_schema import (
    AdminParentBindingItem,
    AdminParentRebindRequest,
    AdminParentStudentBindRequest,
    AdminStudentTeacherBindRequest,
    AdminTeacherBrief,
    AdminUserCreateRequest,
    AdminUserListItem,
    AdminUserListResponse,
    AdminUserRelationsResponse,
    AdminUserUpdateRequest,
    PublicProblemListItem,
    PublicProblemListResponse,
)
from app.schemas.problem_schema import (
    ProblemCreateRequest,
    ProblemDetail,
    ProblemImportFailedRow,
    ProblemImportResult,
    ProblemUpdateRequest,
    TestCaseItem,
)
from pydantic import ValidationError
from app.services.submission_service import SubmissionService
from app.utils.user_class_names import class_names_for_users


class AdminUserService:
    def __init__(self, db: Session):
        self.db = db

    def _log(self, admin_id: int, action: str, detail: str | None = None) -> None:
        self.db.add(OperationLog(user_id=admin_id, action=action, resource="admin_user", detail=detail))

    def list_users(
        self,
        role: UserRole | None,
        keyword: str | None,
        page: int,
        page_size: int,
    ) -> AdminUserListResponse:
        query = self.db.query(User).filter(User.deleted_at.is_(None), User.role != UserRole.ADMIN)
        if role:
            query = query.filter(User.role == role)
        if keyword:
            like = f"%{keyword.strip()}%"
            query = query.filter(
                (User.account.ilike(like))
                | (User.display_name.ilike(like))
                | (User.nickname.ilike(like))
                | (User.phone.ilike(like))
            )
        total = query.count()
        users = query.order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        relation_map = self._relation_summaries_for_users(users)
        class_map = class_names_for_users(self.db, users)
        items = [self._to_list_item(user, relation_map, class_map) for user in users]
        return AdminUserListResponse(items=items, total=total, page=page, page_size=page_size)

    def create_user(self, admin_id: int, payload: AdminUserCreateRequest) -> AdminUserListItem:
        from app.utils.student_account import DEFAULT_STUDENT_PASSWORD, allocate_student_account

        role = UserRole(payload.role)
        if role == UserRole.ADMIN:
            raise AppException(400, "不能通过此接口创建管理员")
        account = (payload.account or "").strip()
        phone = payload.phone.strip() if payload.phone else None
        student_no = payload.student_no.strip() if payload.student_no else None
        password = payload.password or ""

        if role == UserRole.STUDENT:
            display = (payload.display_name or "").strip()
            if not display:
                raise AppException(400, "请填写学生真实姓名")
            account, auto_no = allocate_student_account(self.db)
            student_no = student_no or auto_no
            password = password or DEFAULT_STUDENT_PASSWORD
        elif role == UserRole.PARENT:
            try:
                phone = validate_phone(phone or account)
            except ValueError as exc:
                raise AppException(400, str(exc)) from exc
            account = phone
        else:
            if not account:
                raise AppException(400, "请填写账号")
            if len(password) < 6:
                raise AppException(400, "请填写至少 6 位密码")

        exists = (
            self.db.query(User)
            .filter(User.account == account, User.role == role, User.deleted_at.is_(None))
            .first()
        )
        if exists:
            raise AppException(400, "该账号在此身份下已存在")
        user = User(
            account=account,
            phone=phone if role == UserRole.PARENT else (phone or None),
            password_hash=hash_password(password),
            role=role,
            display_name=payload.display_name.strip() if payload.display_name else None,
            student_no=student_no,
            created_by_teacher_id=payload.created_by_teacher_id,
            is_active=True,
            created_by=admin_id,
            updated_by=admin_id,
        )
        self.db.add(user)
        self._log(admin_id, "create_user", f"user_id=pending, role={role.value}")
        self.db.commit()
        self.db.refresh(user)
        return self._to_admin_list_item(user)

    def update_user(self, admin_id: int, user_id: int, payload: AdminUserUpdateRequest) -> AdminUserListItem:
        user = self.db.get(User, user_id)
        if user is None or user.deleted_at is not None or user.role == UserRole.ADMIN:
            raise AppException(404, "用户不存在")
        if user.role == UserRole.PARENT:
            self._apply_parent_account_update(user, payload)
        else:
            if payload.account is not None:
                new_account = payload.account.strip()
                if not new_account:
                    raise AppException(400, "账号不能为空")
                if new_account != user.account:
                    conflict = (
                        self.db.query(User)
                        .filter(
                            User.account == new_account,
                            User.role == user.role,
                            User.id != user.id,
                            User.deleted_at.is_(None),
                        )
                        .first()
                    )
                    if conflict:
                        raise AppException(400, "该角色下账号已存在")
                    user.account = new_account
            if payload.phone is not None:
                user.phone = payload.phone.strip() or None
        if payload.display_name is not None:
            user.display_name = payload.display_name.strip() or None
        if payload.nickname is not None:
            from app.utils.nickname_unique import assert_nickname_unique

            raw = payload.nickname.strip()
            if not raw:
                user.nickname = None
            else:
                user.nickname = assert_nickname_unique(self.db, raw, exclude_user_id=user.id)
        if payload.student_no is not None:
            if user.role != UserRole.STUDENT:
                raise AppException(400, "仅学生可设置学号")
            user.student_no = payload.student_no.strip() or None
        if "created_by_teacher_id" in payload.model_fields_set:
            if user.role != UserRole.STUDENT:
                raise AppException(400, "仅学生可设置负责教师")
            if payload.created_by_teacher_id is None:
                user.created_by_teacher_id = None
            else:
                teacher = self.db.get(User, payload.created_by_teacher_id)
                if teacher is None or teacher.deleted_at is not None or teacher.role != UserRole.TEACHER:
                    raise AppException(404, "教师不存在")
                user.created_by_teacher_id = teacher.id
        if payload.is_active is not None:
            user.is_active = payload.is_active
            if not payload.is_active:
                user.token_version += 1
        if payload.password:
            user.password_hash = hash_password(payload.password)
            user.token_version += 1
        user.updated_by = admin_id
        self._log(admin_id, "update_user", f"user_id={user_id}")
        self.db.commit()
        self.db.refresh(user)
        return self._to_admin_list_item(user)

    def _to_list_item(
        self,
        user: User,
        relation_map: dict[int, list[str]],
        class_map: dict[int, list[str]],
    ) -> AdminUserListItem:
        real = user.display_name
        return AdminUserListItem(
            id=user.id,
            account=user.account,
            role=user.role.value,
            display_name=real,
            real_name=real,
            nickname=user.nickname,
            class_names=class_map.get(user.id, []),
            phone=user.phone,
            is_active=user.is_active,
            student_no=user.student_no,
            created_at=user.created_at,
            relation_summary=relation_map.get(user.id, []),
        )

    def _to_admin_list_item(self, user: User) -> AdminUserListItem:
        relation_map = self._relation_summaries_for_users([user])
        class_map = class_names_for_users(self.db, [user])
        return self._to_list_item(user, relation_map, class_map)

    def _apply_parent_account_update(self, user: User, payload: AdminUserUpdateRequest) -> None:
        raw = payload.phone if payload.phone is not None else payload.account
        if raw is None:
            return
        try:
            phone = validate_phone(raw.strip())
        except ValueError as exc:
            raise AppException(400, str(exc)) from exc
        if phone != user.account:
            conflict = (
                self.db.query(User)
                .filter(
                    User.account == phone,
                    User.role == UserRole.PARENT,
                    User.id != user.id,
                    User.deleted_at.is_(None),
                )
                .first()
            )
            if conflict:
                raise AppException(400, "该手机号已注册为家长")
        user.account = phone
        user.phone = phone

    def get_user_relations(self, user_id: int) -> AdminUserRelationsResponse:
        user = self.db.get(User, user_id)
        if user is None or user.deleted_at is not None or user.role == UserRole.ADMIN:
            raise AppException(404, "用户不存在", status_code=404)

        parent_bindings: list[AdminParentBindingItem] = []
        bound_children: list[AdminParentBindingItem] = []
        teacher: AdminTeacherBrief | None = None
        teaching_classes: list[str] = []
        student_teacher_lines: list[str] = []

        if user.role == UserRole.STUDENT:
            student_teacher_lines = self._relation_summaries_for_users([user]).get(user.id, [])
            parent_bindings = self._bindings_for_student(user.id)
            if user.created_by_teacher_id:
                t = self.db.get(User, user.created_by_teacher_id)
                if t and t.deleted_at is None:
                    teacher = AdminTeacherBrief(id=t.id, display_name=t.display_name, account=t.account)
        elif user.role == UserRole.PARENT:
            bound_children = self._bindings_for_parent(user.id)
        elif user.role == UserRole.TEACHER:
            teaching_classes = self._teacher_class_names(user.id)

        return AdminUserRelationsResponse(
            user_id=user.id,
            role=user.role.value,
            parent_bindings=parent_bindings,
            bound_children=bound_children,
            teacher=teacher,
            teaching_classes=teaching_classes,
            student_teacher_lines=student_teacher_lines,
        )

    def bind_parent_student(self, admin_id: int, payload: AdminParentStudentBindRequest) -> AdminParentBindingItem:
        parent = self._get_user_role(payload.parent_id, UserRole.PARENT)
        student = self._get_user_role(payload.student_id, UserRole.STUDENT)
        existing = (
            self.db.query(ParentStudentBinding)
            .filter(
                ParentStudentBinding.parent_id == parent.id,
                ParentStudentBinding.student_id == student.id,
            )
            .first()
        )
        if existing:
            raise AppException(400, "该家长与学生已绑定")
        binding = ParentStudentBinding(parent_id=parent.id, student_id=student.id)
        self.db.add(binding)
        self._log(admin_id, "admin_bind_parent_student", f"parent={parent.id}, student={student.id}")
        self.db.commit()
        self.db.refresh(binding)
        return self._binding_item(binding, parent, student)

    def unbind_parent_student(self, admin_id: int, binding_id: int) -> None:
        binding = self.db.get(ParentStudentBinding, binding_id)
        if binding is None:
            raise AppException(404, "绑定不存在", status_code=404)
        self.db.delete(binding)
        self._log(admin_id, "admin_unbind_parent_student", f"binding_id={binding_id}")
        self.db.commit()

    def rebind_parent_student(
        self, admin_id: int, binding_id: int, payload: AdminParentRebindRequest
    ) -> AdminParentBindingItem:
        binding = self.db.get(ParentStudentBinding, binding_id)
        if binding is None:
            raise AppException(404, "绑定不存在", status_code=404)
        new_parent = self._get_user_role(payload.new_parent_id, UserRole.PARENT)
        student = self._get_user_role(binding.student_id, UserRole.STUDENT)
        conflict = (
            self.db.query(ParentStudentBinding)
            .filter(
                ParentStudentBinding.parent_id == new_parent.id,
                ParentStudentBinding.student_id == student.id,
                ParentStudentBinding.id != binding_id,
            )
            .first()
        )
        if conflict:
            raise AppException(400, "新家长已与该学生绑定")
        binding.parent_id = new_parent.id
        self._log(admin_id, "admin_rebind_parent", f"binding_id={binding_id}, new_parent={new_parent.id}")
        self.db.commit()
        self.db.refresh(binding)
        return self._binding_item(binding, new_parent, student)

    def set_student_teacher(
        self, admin_id: int, student_id: int, payload: AdminStudentTeacherBindRequest
    ) -> AdminUserRelationsResponse:
        student = self._get_user_role(student_id, UserRole.STUDENT)
        if payload.teacher_id is None:
            student.created_by_teacher_id = None
        else:
            teacher = self._get_user_role(payload.teacher_id, UserRole.TEACHER)
            student.created_by_teacher_id = teacher.id
        student.updated_by = admin_id
        self._log(
            admin_id,
            "admin_set_student_teacher",
            f"student={student_id}, teacher={payload.teacher_id}",
        )
        self.db.commit()
        return self.get_user_relations(student_id)

    def _get_user_role(self, user_id: int, role: UserRole) -> User:
        user = self.db.get(User, user_id)
        if user is None or user.deleted_at is not None or user.role != role:
            raise AppException(404, "用户不存在或角色不匹配", status_code=404)
        return user

    def _teacher_class_names(self, teacher_id: int) -> list[str]:
        rows = (
            self.db.query(TeachingClass.name)
            .filter(TeachingClass.teacher_id == teacher_id, TeachingClass.deleted_at.is_(None))
            .order_by(TeachingClass.id.desc())
            .all()
        )
        return [name for (name,) in rows]

    def _relation_summaries_for_users(self, users: list[User]) -> dict[int, list[str]]:
        result: dict[int, list[str]] = {user.id: [] for user in users}
        if not users:
            return result

        student_ids = [u.id for u in users if u.role == UserRole.STUDENT]
        parent_ids = [u.id for u in users if u.role == UserRole.PARENT]
        teacher_ids = [u.id for u in users if u.role == UserRole.TEACHER]

        if teacher_ids:
            class_rows = (
                self.db.query(TeachingClass.teacher_id, TeachingClass.name)
                .filter(
                    TeachingClass.teacher_id.in_(teacher_ids),
                    TeachingClass.deleted_at.is_(None),
                )
                .order_by(TeachingClass.id.desc())
                .all()
            )
            by_teacher: dict[int, list[str]] = defaultdict(list)
            for teacher_id, name in class_rows:
                by_teacher[teacher_id].append(name)
            for teacher_id in teacher_ids:
                result[teacher_id] = by_teacher.get(teacher_id, [])

        if parent_ids:
            child_rows = (
                self.db.query(ParentStudentBinding.parent_id, User.display_name, User.account)
                .join(User, User.id == ParentStudentBinding.student_id)
                .filter(
                    ParentStudentBinding.parent_id.in_(parent_ids),
                    User.deleted_at.is_(None),
                )
                .all()
            )
            by_parent: dict[int, list[str]] = defaultdict(list)
            for parent_id, display_name, account in child_rows:
                label = (display_name or account or "").strip()
                if account and label != account:
                    label = f"{label}（{account}）"
                elif account:
                    label = account
                if label:
                    by_parent[parent_id].append(label)
            for parent_id in parent_ids:
                result[parent_id] = by_parent.get(parent_id, [])

        if student_ids:
            teacher_classes: dict[int, dict[int, set[str]]] = defaultdict(lambda: defaultdict(set))
            teacher_ids_needed: set[int] = set()

            for student in users:
                if student.role != UserRole.STUDENT:
                    continue
                if student.created_by_teacher_id:
                    teacher_ids_needed.add(student.created_by_teacher_id)
                    teacher_classes[student.id][student.created_by_teacher_id]

            enroll_rows = (
                self.db.query(
                    ClassEnrollment.student_id,
                    TeachingClass.teacher_id,
                    TeachingClass.name,
                )
                .join(TeachingClass, TeachingClass.id == ClassEnrollment.class_id)
                .filter(
                    ClassEnrollment.student_id.in_(student_ids),
                    ClassEnrollment.deleted_at.is_(None),
                    TeachingClass.deleted_at.is_(None),
                )
                .all()
            )
            for student_id, teacher_id, class_name in enroll_rows:
                teacher_ids_needed.add(teacher_id)
                teacher_classes[student_id][teacher_id].add(class_name)

            teacher_name_map: dict[int, str] = {}
            if teacher_ids_needed:
                for t in (
                    self.db.query(User)
                    .filter(User.id.in_(teacher_ids_needed), User.deleted_at.is_(None))
                    .all()
                ):
                    teacher_name_map[t.id] = t.display_name or t.account

            for student_id in student_ids:
                lines: list[str] = []
                for teacher_id in sorted(
                    teacher_classes.get(student_id, {}).keys(),
                    key=lambda tid: teacher_name_map.get(tid, ""),
                ):
                    name = teacher_name_map.get(teacher_id)
                    if not name:
                        continue
                    classes = sorted(teacher_classes[student_id][teacher_id])
                    if classes:
                        lines.append(f"{name}（{'、'.join(classes)}）")
                    else:
                        lines.append(name)
                result[student_id] = lines

        return result

    def _bindings_for_student(self, student_id: int) -> list[AdminParentBindingItem]:
        rows = (
            self.db.query(ParentStudentBinding, User)
            .join(User, User.id == ParentStudentBinding.parent_id)
            .filter(ParentStudentBinding.student_id == student_id)
            .all()
        )
        student = self.db.get(User, student_id)
        return [
            self._binding_item(binding, parent, student)
            for binding, parent in rows
            if student is not None
        ]

    def _bindings_for_parent(self, parent_id: int) -> list[AdminParentBindingItem]:
        rows = (
            self.db.query(ParentStudentBinding, User)
            .join(User, User.id == ParentStudentBinding.student_id)
            .filter(ParentStudentBinding.parent_id == parent_id)
            .all()
        )
        parent = self.db.get(User, parent_id)
        return [
            self._binding_item(binding, parent, student)
            for binding, student in rows
            if parent is not None
        ]

    def _binding_item(
        self, binding: ParentStudentBinding, parent: User, student: User
    ) -> AdminParentBindingItem:
        return AdminParentBindingItem(
            id=binding.id,
            parent_id=parent.id,
            parent_account=parent.account,
            parent_name=parent.display_name,
            student_id=student.id,
            student_name=student.display_name,
        )


class AdminPublicProblemService:
    def __init__(self, db: Session):
        self.db = db

    def _log(self, admin_id: int, action: str, detail: str | None = None) -> None:
        self.db.add(OperationLog(user_id=admin_id, action=action, resource="public_problem", detail=detail))

    def list_problems(
        self,
        page: int,
        page_size: int,
        status: str | None = None,
        keyword: str | None = None,
        difficulty: str | None = None,
    ) -> PublicProblemListResponse:
        query = self.db.query(Problem).filter(
            Problem.scope == ProblemScope.PUBLIC,
            Problem.deleted_at.is_(None),
        )
        if status:
            query = query.filter(Problem.publish_status == PublicPublishStatus(status))
        if difficulty:
            query = query.filter(Problem.difficulty == difficulty.strip())
        if keyword:
            raw = keyword.strip()
            like = f"%{raw}%"
            if raw.isdigit():
                query = query.filter((Problem.title.ilike(like)) | (Problem.id == int(raw)))
            else:
                query = query.filter(Problem.title.ilike(like))
        total = query.count()
        problems = (
            query.order_by(Problem.public_group_id.desc(), Problem.version.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        items = [self._to_public_item(problem) for problem in problems]
        return PublicProblemListResponse(items=items, total=total, page=page, page_size=page_size)

    def list_published_catalog(
        self,
        page: int,
        page_size: int,
        keyword: str | None,
        difficulty: str | None,
        language: str | None = None,
        gesp_level: str | None = None,
        knowledge_point: str | None = None,
        sort_by: str = "id",
        sort_order: str = "asc",
        viewer_id: int | None = None,
        my_passed: bool = False,
    ):
        from app.schemas.problem_schema import ProblemListItem, ProblemListResponse
        from app.services.practice_service import PracticeService
        from app.services.submission_service import SubmissionService

        practice = PracticeService(self.db)
        query = practice._public_catalog_query()
        if keyword:
            raw = keyword.strip()
            if raw.startswith("#"):
                raw = raw[1:].strip()
            like = f"%{raw}%"
            if raw.isdigit():
                query = query.filter((Problem.title.ilike(like)) | (Problem.id == int(raw)))
            else:
                query = query.filter(Problem.title.ilike(like))
        if difficulty:
            query = query.filter(Problem.difficulty == ProblemDifficulty(difficulty))
        if language:
            from app.utils.problem_languages import apply_language_filter

            query = apply_language_filter(query, language)
        if gesp_level:
            query = query.filter(Problem.gesp_level == GespLevel(gesp_level))
        if knowledge_point:
            query = practice._apply_knowledge_point_filter(query, knowledge_point.strip())

        if my_passed and viewer_id is not None:
            query = SubmissionService.apply_my_passed_filter(query, self.db, viewer_id, True)

        total = query.count()
        order_asc = sort_order.lower() != "desc"
        if sort_by == "difficulty":
            diff_key = practice._difficulty_sort_key()
            primary = diff_key.asc() if order_asc else diff_key.desc()
            order_clause = (primary, Problem.id.asc())
        else:
            primary = Problem.id.asc() if order_asc else Problem.id.desc()
            order_clause = (primary,)

        problems = (
            query.order_by(*order_clause)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        items = []
        for problem in problems:
            count = self._test_case_count(problem.id)
            pass_rate, submission_count = SubmissionService.compute_pass_rate(self.db, problem.id)
            items.append(
                ProblemListItem(
                    id=problem.id,
                    title=problem.title,
                    language=problem.language.value,
                    languages=self._problem_languages(problem),
                    difficulty=problem.difficulty.value,
                    gesp_level=problem.gesp_level.value,
                    knowledge_point=problem.knowledge_point,
                    knowledge_points=self._problem_knowledge_points(problem),
                    test_case_count=count,
                    is_publishable=count > 0,
                    pass_rate=pass_rate,
                    submission_count=submission_count,
                    created_at=problem.created_at,
                )
            )
        return ProblemListResponse(items=items, total=total, page=page, page_size=page_size)

    def get_published_catalog_item(self, problem_id: int) -> ProblemDetail:
        problem = self._get_public_problem(problem_id)
        if problem.publish_status != PublicPublishStatus.PUBLISHED:
            raise AppException(404, "题目未上架或不可浏览")
        return self._to_detail(problem)

    def get_problem(self, admin_id: int, problem_id: int) -> ProblemDetail:
        problem = self._get_public_problem(problem_id)
        return self._to_detail(problem)

    def import_problems(self, admin_id: int, raw_items: list[dict]) -> ProblemImportResult:
        if len(raw_items) > 50:
            raise AppException(400, "单次最多导入 50 道题")

        created_ids: list[int] = []
        failed: list[ProblemImportFailedRow] = []
        for index, raw in enumerate(raw_items, start=1):
            title = str(raw.get("title") or "")
            try:
                payload = ProblemCreateRequest.model_validate(raw)
                detail = self.create_problem(admin_id, payload)
                created_ids.append(detail.id)
            except ValidationError as exc:
                reason = exc.errors()[0].get("msg", "字段校验失败")
                failed.append(ProblemImportFailedRow(row=index, title=title or None, reason=str(reason)))
            except AppException as exc:
                failed.append(ProblemImportFailedRow(row=index, title=title or None, reason=exc.message))
            except Exception:
                failed.append(ProblemImportFailedRow(row=index, title=title or None, reason="导入失败"))

        self._log(admin_id, "import_public_problems", f"success={len(created_ids)}, failed={len(failed)}")
        return ProblemImportResult(
            success_count=len(created_ids),
            failed=failed,
            created_ids=created_ids,
        )

    def create_problem(self, admin_id: int, payload: ProblemCreateRequest) -> ProblemDetail:
        problem = Problem(
            teacher_id=admin_id,
            scope=ProblemScope.PUBLIC,
            publish_status=PublicPublishStatus.PUBLISHED,
            version=1,
            title=payload.title.strip(),
            description=payload.description.strip(),
            difficulty=ProblemDifficulty(payload.difficulty),
            gesp_level=GespLevel(payload.gesp_level or "GESP1"),
            language=ProblemLanguage.PYTHON,
            input_format=payload.input_format,
            output_format=payload.output_format,
            sample_input=normalize_io_text(payload.sample_input),
            sample_output=normalize_io_text(payload.sample_output),
            reference_answer=payload.reference_answer,
            hint=payload.hint,
            time_limit_ms=payload.time_limit_ms,
            memory_limit_mb=payload.memory_limit_mb,
            created_by=admin_id,
            updated_by=admin_id,
        )
        from app.utils.problem_images import normalize_problem_image_urls
        from app.utils.problem_knowledge import apply_knowledge_points_to_problem
        from app.utils.problem_languages import apply_languages_to_problem

        problem.image_urls = normalize_problem_image_urls(payload.image_urls)
        apply_languages_to_problem(problem, payload.languages)
        apply_knowledge_points_to_problem(problem, payload.knowledge_points)
        self.db.add(problem)
        self.db.flush()
        problem.public_group_id = problem.id
        self._replace_test_cases(problem.id, payload.test_cases)
        self._sync_catalog_publication(admin_id, problem)
        self._log(admin_id, "create_public_problem", f"problem_id={problem.id}")
        self.db.commit()
        self.db.refresh(problem)
        return self._to_detail(problem)

    def update_problem(self, admin_id: int, problem_id: int, payload: ProblemUpdateRequest) -> ProblemDetail:
        problem = self._get_public_problem(problem_id)
        updates = payload.model_dump(
            exclude_unset=True,
            exclude={"test_cases", "knowledge_points", "languages", "image_urls"},
        )
        if payload.languages is not None:
            from app.utils.problem_languages import apply_languages_to_problem

            apply_languages_to_problem(problem, payload.languages)
        if payload.knowledge_points is not None:
            from app.utils.problem_knowledge import apply_knowledge_points_to_problem

            apply_knowledge_points_to_problem(problem, payload.knowledge_points)
        if payload.image_urls is not None:
            from app.utils.problem_images import normalize_problem_image_urls

            problem.image_urls = normalize_problem_image_urls(payload.image_urls)
        for field, value in updates.items():
            if field in ("language", "difficulty", "gesp_level") and value is not None:
                enum_cls = {
                    "language": ProblemLanguage,
                    "difficulty": ProblemDifficulty,
                    "gesp_level": GespLevel,
                }[field]
                value = enum_cls(value)
            elif isinstance(value, str):
                if field in ("sample_input", "sample_output"):
                    value = normalize_io_text(value)
                else:
                    value = value.strip() if field != "description" else value.strip()
            setattr(problem, field, value)
        if payload.test_cases is not None:
            self._replace_test_cases(problem.id, payload.test_cases)
        problem.updated_by = admin_id
        self._sync_catalog_publication(admin_id, problem)
        self._log(admin_id, "update_public_problem", f"problem_id={problem_id}")
        self.db.commit()
        self.db.refresh(problem)
        return self._to_detail(problem)

    def _sync_catalog_publication(self, admin_id: int, problem: Problem) -> None:
        """组内最新版本在有用例时自动对学生可见，无需手动上下架。"""
        if problem.public_group_id is None:
            return
        max_version = (
            self.db.query(func.max(Problem.version))
            .filter(
                Problem.public_group_id == problem.public_group_id,
                Problem.deleted_at.is_(None),
            )
            .scalar()
            or problem.version
        )
        if problem.version < max_version:
            return
        siblings = (
            self.db.query(Problem)
            .filter(
                Problem.public_group_id == problem.public_group_id,
                Problem.id != problem.id,
                Problem.deleted_at.is_(None),
            )
            .all()
        )
        for sibling in siblings:
            if sibling.publish_status == PublicPublishStatus.PUBLISHED:
                sibling.publish_status = PublicPublishStatus.ARCHIVED
                sibling.updated_by = admin_id
        problem.publish_status = PublicPublishStatus.PUBLISHED
        problem.updated_by = admin_id

    def publish(self, admin_id: int, problem_id: int) -> ProblemDetail:
        problem = self._get_public_problem(problem_id)
        if problem.publish_status == PublicPublishStatus.PUBLISHED:
            return self._to_detail(problem)
        if self._test_case_count(problem.id) == 0:
            raise AppException(400, "需要至少一个测试用例才能上架")
        if problem.public_group_id:
            siblings = (
                self.db.query(Problem)
                .filter(
                    Problem.public_group_id == problem.public_group_id,
                    Problem.publish_status == PublicPublishStatus.PUBLISHED,
                    Problem.id != problem.id,
                    Problem.deleted_at.is_(None),
                )
                .all()
            )
            for sibling in siblings:
                sibling.publish_status = PublicPublishStatus.ARCHIVED
                sibling.updated_by = admin_id
        problem.publish_status = PublicPublishStatus.PUBLISHED
        problem.updated_by = admin_id
        self._log(admin_id, "publish_public_problem", f"problem_id={problem_id}")
        self.db.commit()
        self.db.refresh(problem)
        return self._to_detail(problem)

    def archive(self, admin_id: int, problem_id: int) -> ProblemDetail:
        problem = self._get_public_problem(problem_id)
        problem.publish_status = PublicPublishStatus.ARCHIVED
        problem.updated_by = admin_id
        self._log(admin_id, "archive_public_problem", f"problem_id={problem_id}")
        self.db.commit()
        self.db.refresh(problem)
        return self._to_detail(problem)

    def create_new_version(self, admin_id: int, problem_id: int) -> ProblemDetail:
        source = self._get_public_problem(problem_id)
        if source.public_group_id is None:
            raise AppException(400, "题目组无效")
        max_version = (
            self.db.query(func.max(Problem.version))
            .filter(Problem.public_group_id == source.public_group_id)
            .scalar()
            or source.version
        )
        clone = Problem(
            teacher_id=admin_id,
            scope=ProblemScope.PUBLIC,
            publish_status=PublicPublishStatus.DRAFT,
            public_group_id=source.public_group_id,
            version=max_version + 1,
            title=source.title,
            description=source.description,
            language=source.language,
            languages=source.languages,
            difficulty=source.difficulty,
            gesp_level=source.gesp_level,
            knowledge_point=source.knowledge_point,
            knowledge_points=source.knowledge_points,
            input_format=source.input_format,
            output_format=source.output_format,
            sample_input=source.sample_input,
            sample_output=source.sample_output,
            reference_answer=source.reference_answer,
            hint=source.hint,
            time_limit_ms=source.time_limit_ms,
            memory_limit_mb=source.memory_limit_mb,
            created_by=admin_id,
            updated_by=admin_id,
        )
        self.db.add(clone)
        self.db.flush()
        for tc in self._active_test_cases(source.id):
            self.db.add(
                TestCase(
                    problem_id=clone.id,
                    input_data=tc.input_data,
                    expected_output=tc.expected_output,
                    is_sample=tc.is_sample,
                    sort_order=tc.sort_order,
                )
            )
        self._sync_catalog_publication(admin_id, clone)
        self._log(admin_id, "new_version_public_problem", f"from={problem_id}, new={clone.id}")
        self.db.commit()
        self.db.refresh(clone)
        return self._to_detail(clone)

    def delete_problem_version(self, admin_id: int, problem_id: int) -> None:
        problem = self._get_public_problem(problem_id)
        if problem.public_group_id is None:
            raise AppException(400, "题目组无效")

        linked_homework = (
            self.db.query(func.count(HomeworkProblem.id))
            .filter(HomeworkProblem.problem_id == problem_id)
            .scalar()
            or 0
        )
        if linked_homework > 0:
            raise AppException(400, "该版本已被作业引用，无法删除")

        now = datetime.now(timezone.utc)
        problem.deleted_at = now
        problem.updated_by = admin_id
        for test_case in self._active_test_cases(problem.id):
            test_case.deleted_at = now
        self._log(admin_id, "delete_public_problem_version", f"problem_id={problem_id}")
        self.db.commit()

    def reconcile_public_catalog(self) -> None:
        """启动时修正：每组仅最新版对学生可见，旧版归档，便于直接删除历史版本。"""
        group_ids = [
            row[0]
            for row in self.db.query(Problem.public_group_id)
            .filter(
                Problem.scope == ProblemScope.PUBLIC,
                Problem.deleted_at.is_(None),
                Problem.public_group_id.isnot(None),
            )
            .distinct()
            .all()
            if row[0] is not None
        ]
        changed = False
        for gid in group_ids:
            rows = (
                self.db.query(Problem)
                .filter(Problem.public_group_id == gid, Problem.deleted_at.is_(None))
                .order_by(Problem.version.desc())
                .all()
            )
            if not rows:
                continue
            latest = rows[0]
            for older in rows[1:]:
                if older.publish_status == PublicPublishStatus.PUBLISHED:
                    older.publish_status = PublicPublishStatus.ARCHIVED
                    changed = True
            if latest.publish_status != PublicPublishStatus.PUBLISHED:
                latest.publish_status = PublicPublishStatus.PUBLISHED
                changed = True
        if changed:
            self.db.commit()

    def _get_public_problem(self, problem_id: int) -> Problem:
        problem = (
            self.db.query(Problem)
            .filter(
                Problem.id == problem_id,
                Problem.scope == ProblemScope.PUBLIC,
                Problem.deleted_at.is_(None),
            )
            .first()
        )
        if problem is None:
            raise AppException(404, "公共题目不存在")
        return problem

    def _replace_test_cases(self, problem_id: int, test_cases: list) -> None:
        now = datetime.now(timezone.utc)
        for existing in self._active_test_cases(problem_id):
            existing.deleted_at = now
        for index, test_case in enumerate(test_cases):
            self.db.add(
                TestCase(
                    problem_id=problem_id,
                    input_data=normalize_io_text(test_case.input_data) or "",
                    expected_output=normalize_io_text(test_case.expected_output) or "",
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

    def _to_public_item(self, problem: Problem) -> PublicProblemListItem:
        count = self._test_case_count(problem.id)
        return PublicProblemListItem(
            id=problem.id,
            public_group_id=problem.public_group_id or problem.id,
            version=problem.version,
            title=problem.title,
            language=problem.language.value,
            difficulty=problem.difficulty.value,
            publish_status=problem.publish_status.value,
            test_case_count=count,
            arena_enabled=bool(problem.arena_enabled),
            created_at=problem.created_at,
        )

    def _to_detail(self, problem: Problem) -> ProblemDetail:
        test_cases = self._active_test_cases(problem.id)
        count = len(test_cases)
        pass_rate, submission_count = SubmissionService.compute_pass_rate(self.db, problem.id)
        return ProblemDetail(
            id=problem.id,
            title=problem.title,
            description=problem.description,
            image_urls=self._problem_image_urls(problem),
            language=self._problem_languages(problem)[0],
            languages=self._problem_languages(problem),
            difficulty=problem.difficulty.value,
            gesp_level=problem.gesp_level.value,
            knowledge_point=problem.knowledge_point,
            knowledge_points=self._problem_knowledge_points(problem),
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

    @staticmethod
    def _problem_image_urls(problem: Problem) -> list[str]:
        from app.utils.problem_images import get_problem_image_urls

        return get_problem_image_urls(problem)

    @staticmethod
    def _problem_knowledge_points(problem: Problem) -> list[str]:
        from app.utils.problem_knowledge import get_problem_knowledge_points

        return get_problem_knowledge_points(problem)

    @staticmethod
    def _problem_languages(problem: Problem) -> list[str]:
        from app.utils.problem_languages import get_problem_languages

        return get_problem_languages(problem)

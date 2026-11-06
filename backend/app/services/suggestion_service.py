import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.forbidden import raise_forbidden
from app.models.audit import OperationLog, ParentStudentBinding
from app.models.class_model import ClassEnrollment, TeachingClass
from app.models.problem import Problem, ProblemScope
from app.models.suggestion import Suggestion, SuggestionContextType, SuggestionStatus
from app.models.suggestion_reply import SuggestionReply
from app.models.user import User, UserRole
from app.schemas.suggestion_schema import (
    SuggestionCreateRequest,
    SuggestionItem,
    SuggestionListResponse,
    SuggestionProblemContext,
    SuggestionRecipient,
    SuggestionRatingRequest,
    SuggestionReplyCreateRequest,
    SuggestionReplyItem,
    SuggestionStatusUpdateRequest,
)
from app.services.problem_access import ProblemAccessHelper
from app.services.user_notification_service import UserNotificationService


class SuggestionService:
    DAILY_LIMIT_PER_PAIR = 20

    @staticmethod
    def _derive_title(title: str | None, content: str) -> str:
        cleaned = (title or "").strip()
        if cleaned:
            return cleaned[:200]
        first_line = content.strip().split("\n", 1)[0].strip()
        if first_line:
            return first_line[:200]
        return "建议"

    def __init__(self, db: Session):
        self.db = db
        self.access = ProblemAccessHelper(db)

    def _log(self, user_id: int, action: str, detail: str | None = None) -> None:
        self.db.add(OperationLog(user_id=user_id, action=action, resource="suggestion", detail=detail))

    def list_recipients(self, user: User, context_type: str | None = None, context_id: int | None = None) -> list[SuggestionRecipient]:
        allowed_ids = self._allowed_recipient_ids(user)
        if context_type == "problem" and context_id:
            problem = self.db.get(Problem, context_id)
            if problem and problem.deleted_at is None:
                default_id = self.access.default_suggestion_recipient_for_problem(user, problem)
                if default_id and default_id in allowed_ids:
                    allowed_ids = [default_id] + [uid for uid in allowed_ids if uid != default_id]
        allowed_roles = self._allowed_recipient_roles(user.role)
        users = (
            self.db.query(User)
            .filter(
                User.id.in_(allowed_ids),
                User.role.in_(allowed_roles),
                User.is_active.is_(True),
                User.deleted_at.is_(None),
            )
            .order_by(User.role.asc(), User.id.asc())
            .all()
        )
        return [
            SuggestionRecipient(
                id=item.id,
                role=item.role.value,
                display_name=item.display_name or item.account,
                account=item.account,
            )
            for item in users
        ]

    def create(self, user: User, payload: SuggestionCreateRequest) -> SuggestionItem:
        if not payload.content.strip():
            raise AppException(400, "请填写建议内容")
        if payload.to_user_id == user.id:
            raise AppException(400, "不能给自己发送建议")
        allowed = self._allowed_recipient_ids(user)
        if payload.to_user_id not in allowed:
            raise_forbidden(self.db, user.id, "suggestion", f"to_user_id={payload.to_user_id}")
        self._check_rate_limit(user.id, payload.to_user_id)
        context_type = SuggestionContextType(payload.context_type) if payload.context_type else SuggestionContextType.GENERAL
        if context_type == SuggestionContextType.PROBLEM and payload.context_id:
            problem = self.db.get(Problem, payload.context_id)
            if problem is None or problem.deleted_at is not None:
                raise AppException(400, "关联题目不存在")
        image_urls_json = None
        if payload.image_urls:
            if len(payload.image_urls) > 3:
                raise AppException(400, "最多上传 3 张图片")
            image_urls_json = json.dumps(payload.image_urls[:3], ensure_ascii=False)
        suggestion = Suggestion(
            from_user_id=user.id,
            to_user_id=payload.to_user_id,
            context_type=context_type,
            context_id=payload.context_id,
            title=self._derive_title(payload.title, payload.content),
            content=payload.content.strip(),
            image_urls=image_urls_json,
            status=SuggestionStatus.PENDING,
        )
        self.db.add(suggestion)
        self._log(user.id, "create_suggestion", f"to={payload.to_user_id}")
        self.db.commit()
        self.db.refresh(suggestion)
        problem_ctx = self._problem_context_for_id(suggestion.context_id, suggestion.context_type)
        return self._to_item(suggestion, [], problem_ctx)

    def list_inbox(
        self,
        user: User,
        page: int,
        page_size: int,
        sender_keyword: str | None = None,
        processed: bool | None = None,
    ) -> SuggestionListResponse:
        query = self.db.query(Suggestion).filter(
            Suggestion.to_user_id == user.id,
            Suggestion.deleted_at.is_(None),
        )
        query = self._apply_list_filters(query, sender_keyword, processed, status=None)
        total = query.count()
        rows = (
            query.order_by(Suggestion.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return self._list_response(rows, total, page, page_size)

    def list_sent(
        self,
        user: User,
        page: int,
        page_size: int,
        sender_keyword: str | None = None,
        processed: bool | None = None,
    ) -> SuggestionListResponse:
        query = self.db.query(Suggestion).filter(
            Suggestion.from_user_id == user.id,
            Suggestion.deleted_at.is_(None),
        )
        query = self._apply_list_filters(query, sender_keyword, processed, status=None)
        total = query.count()
        rows = (
            query.order_by(Suggestion.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return self._list_response(rows, total, page, page_size)

    def admin_list(
        self,
        page: int,
        page_size: int,
        status: str | None = None,
        sender_keyword: str | None = None,
        processed: bool | None = None,
    ) -> SuggestionListResponse:
        query = self.db.query(Suggestion).filter(Suggestion.deleted_at.is_(None))
        query = self._apply_list_filters(query, sender_keyword, processed, status=status)
        total = query.count()
        rows = (
            query.order_by(Suggestion.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return self._list_response(rows, total, page, page_size)

    def get_detail(self, user: User, suggestion_id: int) -> SuggestionItem:
        suggestion = self.db.get(Suggestion, suggestion_id)
        if suggestion is None or suggestion.deleted_at is not None:
            raise AppException(404, "建议不存在")
        if not self._can_participate(user, suggestion):
            raise_forbidden(self.db, user.id, "suggestion", f"id={suggestion_id}")
        replies_map = self._replies_for_suggestions([suggestion.id])
        problem_ctx = self._problem_context_for_id(suggestion.context_id, suggestion.context_type)
        return self._to_item(suggestion, replies_map.get(suggestion.id, []), problem_ctx)

    def add_reply(
        self,
        user: User,
        suggestion_id: int,
        payload: SuggestionReplyCreateRequest,
    ) -> SuggestionReplyItem:
        suggestion = self.db.get(Suggestion, suggestion_id)
        if suggestion is None or suggestion.deleted_at is not None:
            raise AppException(404, "建议不存在")
        if not self._can_participate(user, suggestion):
            raise_forbidden(self.db, user.id, "suggestion_reply", f"suggestion_id={suggestion_id}")
        if suggestion.status in (SuggestionStatus.RESOLVED, SuggestionStatus.CLOSED):
            raise AppException(400, "建议已处理，无法继续回复")
        content = payload.content.strip()
        images = payload.image_urls[:3] if payload.image_urls else []
        if not content and not images:
            raise AppException(400, "请填写回复文字或上传图片")
        image_urls_json = json.dumps(images, ensure_ascii=False) if images else None
        reply = SuggestionReply(
            suggestion_id=suggestion.id,
            from_user_id=user.id,
            content=content,
            image_urls=image_urls_json,
        )
        if suggestion.status == SuggestionStatus.PENDING and user.id == suggestion.to_user_id:
            suggestion.status = SuggestionStatus.READ
        self.db.add(reply)
        self._log(user.id, "reply_suggestion", f"suggestion_id={suggestion_id}")
        self.db.commit()
        self.db.refresh(reply)
        return self._to_reply_item(reply)

    def update_status(self, user: User, suggestion_id: int, payload: SuggestionStatusUpdateRequest) -> SuggestionItem:
        suggestion = self.db.get(Suggestion, suggestion_id)
        if suggestion is None or suggestion.deleted_at is not None:
            raise AppException(404, "建议不存在")
        if user.role != UserRole.ADMIN and suggestion.to_user_id != user.id:
            raise_forbidden(self.db, user.id, "suggestion", f"id={suggestion_id}")
        old_status = suggestion.status
        suggestion.status = SuggestionStatus(payload.status)
        if old_status != SuggestionStatus.RESOLVED and suggestion.status == SuggestionStatus.RESOLVED:
            handler_name = user.display_name or user.account
            UserNotificationService(self.db).push(
                suggestion.from_user_id,
                "suggestion_resolved",
                "建议已处理",
                f"您提交的建议已被「{handler_name}」标记为已处理，可在建议中心查看。",
                {"suggestion_id": suggestion.id},
            )
        self._log(user.id, "update_suggestion_status", f"id={suggestion_id},status={payload.status}")
        self.db.commit()
        self.db.refresh(suggestion)
        replies_map = self._replies_for_suggestions([suggestion.id])
        problem_ctx = self._problem_context_for_id(suggestion.context_id, suggestion.context_type)
        return self._to_item(suggestion, replies_map.get(suggestion.id, []), problem_ctx)

    def rate_satisfaction(self, user: User, suggestion_id: int, payload: SuggestionRatingRequest) -> SuggestionItem:
        suggestion = self.db.get(Suggestion, suggestion_id)
        if suggestion is None or suggestion.deleted_at is not None:
            raise AppException(404, "建议不存在")
        if user.id != suggestion.from_user_id:
            raise_forbidden(self.db, user.id, "suggestion_rating", f"id={suggestion_id}")
        if suggestion.status != SuggestionStatus.RESOLVED:
            raise AppException(400, "仅已处理的建议可评分")
        if suggestion.satisfaction_rating is not None:
            raise AppException(400, "您已提交过评分")
        suggestion.satisfaction_rating = payload.score
        self._log(user.id, "rate_suggestion", f"id={suggestion_id},score={payload.score}")
        self.db.commit()
        self.db.refresh(suggestion)
        replies_map = self._replies_for_suggestions([suggestion.id])
        problem_ctx = self._problem_context_for_id(suggestion.context_id, suggestion.context_type)
        return self._to_item(suggestion, replies_map.get(suggestion.id, []), problem_ctx)

    def unread_count(self, user_id: int) -> int:
        return (
            self.db.query(func.count(Suggestion.id))
            .filter(
                Suggestion.to_user_id == user_id,
                Suggestion.status == SuggestionStatus.PENDING,
                Suggestion.deleted_at.is_(None),
            )
            .scalar()
            or 0
        )

    def _apply_list_filters(
        self,
        query,
        sender_keyword: str | None,
        processed: bool | None,
        status: str | None,
    ):
        raw = (sender_keyword or "").strip()
        if raw:
            like = f"%{raw}%"
            query = query.join(User, User.id == Suggestion.from_user_id).filter(
                (User.display_name.ilike(like)) | (User.account.ilike(like))
            )
        if processed is True:
            query = query.filter(Suggestion.status == SuggestionStatus.RESOLVED)
        elif processed is False:
            query = query.filter(Suggestion.status != SuggestionStatus.RESOLVED)
        elif status:
            query = query.filter(Suggestion.status == SuggestionStatus(status))
        return query

    def _check_rate_limit(self, from_id: int, to_id: int) -> None:
        since = datetime.now(timezone.utc) - timedelta(days=1)
        count = (
            self.db.query(func.count(Suggestion.id))
            .filter(
                Suggestion.from_user_id == from_id,
                Suggestion.to_user_id == to_id,
                Suggestion.created_at >= since,
            )
            .scalar()
            or 0
        )
        if count >= self.DAILY_LIMIT_PER_PAIR:
            raise AppException(429, "今日向该用户发送建议次数已达上限")

    def _allowed_recipient_ids(self, user: User) -> list[int]:
        ids: set[int] = set()
        admins = (
            self.db.query(User.id)
            .filter(User.role == UserRole.ADMIN, User.is_active.is_(True), User.deleted_at.is_(None))
            .all()
        )
        ids.update(row.id for row in admins)

        if user.role == UserRole.ADMIN:
            others = (
                self.db.query(User.id)
                .filter(User.role != UserRole.ADMIN, User.is_active.is_(True), User.deleted_at.is_(None))
                .all()
            )
            ids.update(row.id for row in others)
            return sorted(ids)

        if user.role == UserRole.TEACHER:
            ids.update(self._teacher_related_user_ids(user.id))
            return sorted(ids)

        if user.role == UserRole.STUDENT:
            ids.update(self.access.student_teacher_ids(user.id))
            return sorted(ids)

        if user.role == UserRole.PARENT:
            bindings = (
                self.db.query(ParentStudentBinding.student_id)
                .filter(ParentStudentBinding.parent_id == user.id)
                .all()
            )
            for row in bindings:
                ids.update(self.access.student_teacher_ids(row.student_id))
            return sorted(ids)

        return sorted(ids)

    def _allowed_recipient_roles(self, sender_role: UserRole) -> tuple[UserRole, ...]:
        if sender_role == UserRole.TEACHER:
            return (UserRole.STUDENT, UserRole.PARENT, UserRole.ADMIN)
        if sender_role == UserRole.STUDENT:
            return (UserRole.TEACHER, UserRole.ADMIN)
        if sender_role == UserRole.PARENT:
            return (UserRole.TEACHER, UserRole.ADMIN)
        if sender_role == UserRole.ADMIN:
            return (UserRole.TEACHER, UserRole.STUDENT, UserRole.PARENT)
        return (UserRole.ADMIN,)

    def _teacher_related_user_ids(self, teacher_id: int) -> set[int]:
        ids: set[int] = set()
        class_ids = [
            row.id
            for row in self.db.query(TeachingClass)
            .filter(TeachingClass.teacher_id == teacher_id, TeachingClass.deleted_at.is_(None))
            .all()
        ]
        if not class_ids:
            return ids
        students = (
            self.db.query(ClassEnrollment.student_id)
            .filter(ClassEnrollment.class_id.in_(class_ids), ClassEnrollment.deleted_at.is_(None))
            .distinct()
            .all()
        )
        student_ids = [row.student_id for row in students]
        ids.update(student_ids)
        if student_ids:
            parents = (
                self.db.query(ParentStudentBinding.parent_id)
                .filter(ParentStudentBinding.student_id.in_(student_ids))
                .all()
            )
            ids.update(row.parent_id for row in parents)
        return ids

    def _list_response(
        self,
        rows: list[Suggestion],
        total: int,
        page: int,
        page_size: int,
    ) -> SuggestionListResponse:
        ids = [row.id for row in rows]
        replies_map = self._replies_for_suggestions(ids)
        problem_map = self._problem_context_map(rows)
        return SuggestionListResponse(
            items=[
                self._to_item(row, replies_map.get(row.id, []), problem_map.get(row.context_id))
                for row in rows
            ],
            total=total,
            page=page,
            page_size=page_size,
        )

    def _can_participate(self, user: User, suggestion: Suggestion) -> bool:
        if user.role == UserRole.ADMIN:
            return True
        return user.id in (suggestion.from_user_id, suggestion.to_user_id)

    def _replies_for_suggestions(self, suggestion_ids: list[int]) -> dict[int, list[SuggestionReplyItem]]:
        if not suggestion_ids:
            return {}
        rows = (
            self.db.query(SuggestionReply)
            .filter(SuggestionReply.suggestion_id.in_(suggestion_ids))
            .order_by(SuggestionReply.id.asc())
            .all()
        )
        grouped: dict[int, list[SuggestionReplyItem]] = {sid: [] for sid in suggestion_ids}
        for row in rows:
            grouped.setdefault(row.suggestion_id, []).append(self._to_reply_item(row))
        return grouped

    def _parse_image_urls(self, raw: str | None) -> list[str]:
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []

    def _to_reply_item(self, reply: SuggestionReply) -> SuggestionReplyItem:
        from_user = self.db.get(User, reply.from_user_id)
        return SuggestionReplyItem(
            id=reply.id,
            suggestion_id=reply.suggestion_id,
            from_user_id=reply.from_user_id,
            from_user_name=(from_user.display_name or from_user.account) if from_user else "",
            from_user_role=from_user.role.value if from_user else "",
            content=reply.content or "",
            image_urls=self._parse_image_urls(reply.image_urls),
            created_at=reply.created_at,
        )

    def _problem_context_map(self, rows: list[Suggestion]) -> dict[int, SuggestionProblemContext]:
        problem_ids = [
            row.context_id
            for row in rows
            if row.context_type == SuggestionContextType.PROBLEM and row.context_id
        ]
        if not problem_ids:
            return {}
        problems = (
            self.db.query(Problem)
            .filter(Problem.id.in_(problem_ids), Problem.deleted_at.is_(None))
            .all()
        )
        return {p.id: self._problem_to_context(p) for p in problems}

    def _problem_context_for_id(
        self,
        context_id: int | None,
        context_type: SuggestionContextType,
    ) -> SuggestionProblemContext | None:
        if context_type != SuggestionContextType.PROBLEM or not context_id:
            return None
        problem = self.db.get(Problem, context_id)
        if problem is None or problem.deleted_at is not None:
            return None
        return self._problem_to_context(problem)

    @staticmethod
    def _problem_to_context(problem: Problem) -> SuggestionProblemContext:
        return SuggestionProblemContext(
            id=problem.id,
            title=problem.title,
            scope=problem.scope.value if isinstance(problem.scope, ProblemScope) else str(problem.scope),
            private_no=problem.private_no,
        )

    def _to_item(
        self,
        suggestion: Suggestion,
        replies: list[SuggestionReplyItem] | None = None,
        context_problem: SuggestionProblemContext | None = None,
    ) -> SuggestionItem:
        from_user = self.db.get(User, suggestion.from_user_id)
        to_user = self.db.get(User, suggestion.to_user_id)
        images = self._parse_image_urls(suggestion.image_urls)
        if context_problem is None:
            context_problem = self._problem_context_for_id(suggestion.context_id, suggestion.context_type)
        stored_title = getattr(suggestion, "title", "") or ""
        display_title = self._derive_title(stored_title, suggestion.content)
        return SuggestionItem(
            id=suggestion.id,
            title=display_title,
            from_user_id=suggestion.from_user_id,
            from_user_name=(from_user.display_name or from_user.account) if from_user else "",
            from_user_role=from_user.role.value if from_user else "",
            to_user_id=suggestion.to_user_id,
            to_user_name=(to_user.display_name or to_user.account) if to_user else "",
            to_user_role=to_user.role.value if to_user else "",
            context_type=suggestion.context_type.value,
            context_id=suggestion.context_id,
            context_problem=context_problem,
            content=suggestion.content,
            image_urls=images,
            status=suggestion.status.value,
            satisfaction_rating=suggestion.satisfaction_rating,
            created_at=suggestion.created_at,
            replies=replies or [],
        )

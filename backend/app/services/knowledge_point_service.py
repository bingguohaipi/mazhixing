from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.knowledge import registry
from app.knowledge.catalog import default_seed_entries
from app.models.knowledge_point import KnowledgePoint
from app.models.problem import Problem
from app.schemas.knowledge_point_schema import (
    AdminKnowledgePointCreateRequest,
    AdminKnowledgePointListItem,
    AdminKnowledgePointListResponse,
    AdminKnowledgePointUpdateRequest,
)
from app.schemas.practice_schema import KnowledgePointOptionItem
from app.utils.problem_knowledge import KNOWLEDGE_TOPIC_ALIASES


class KnowledgePointService:
    def __init__(self, db: Session):
        self.db = db

    def ensure_catalog(self) -> None:
        active_count = (
            self.db.query(func.count(KnowledgePoint.id))
            .filter(KnowledgePoint.deleted_at.is_(None))
            .scalar()
            or 0
        )
        if active_count == 0:
            for entry in default_seed_entries():
                self.db.add(
                    KnowledgePoint(
                        name=entry.name,
                        summary=entry.summary,
                        content_markdown=entry.content_markdown,
                        sort_order=entry.sort_order,
                    )
                )
            self.db.commit()
        registry.reload_from_db(self.db)

    def refresh_registry(self) -> None:
        registry.reload_from_db(self.db)

    def _problem_counts(self) -> dict[str, int]:
        from app.utils.problem_knowledge import get_problem_knowledge_points

        counts: dict[str, int] = {}
        problems = self.db.query(Problem).filter(Problem.deleted_at.is_(None)).all()
        from app.utils.problem_knowledge import resolve_knowledge_topic_name

        for problem in problems:
            for name in get_problem_knowledge_points(problem):
                canonical = resolve_knowledge_topic_name(name)
                counts[canonical] = counts.get(canonical, 0) + 1
        return counts

    def list_form_options(self, keyword: str | None = None, limit: int = 80) -> list[KnowledgePointOptionItem]:
        self.ensure_catalog()
        query = self.db.query(KnowledgePoint).filter(KnowledgePoint.deleted_at.is_(None))
        raw = (keyword or "").strip()
        if raw:
            like = f"%{raw}%"
            query = query.filter(
                (KnowledgePoint.name.ilike(like)) | (KnowledgePoint.summary.ilike(like))
            )
        rows = (
            query.order_by(KnowledgePoint.sort_order.asc(), KnowledgePoint.name.asc())
            .limit(max(1, min(limit, 200)))
            .all()
        )
        return [
            KnowledgePointOptionItem(name=row.name, summary=row.summary or "")
            for row in rows
            if row.name not in KNOWLEDGE_TOPIC_ALIASES
        ]

    def list_for_admin(
        self,
        keyword: str | None = None,
        sort_by: str = "sort_order",
        sort_order: str = "asc",
    ) -> AdminKnowledgePointListResponse:
        self.ensure_catalog()
        query = self.db.query(KnowledgePoint).filter(KnowledgePoint.deleted_at.is_(None))
        raw = (keyword or "").strip()
        if raw:
            like = f"%{raw}%"
            query = query.filter(
                (KnowledgePoint.name.ilike(like))
                | (KnowledgePoint.summary.ilike(like))
            )
        rows = query.order_by(KnowledgePoint.sort_order.asc(), KnowledgePoint.name.asc()).all()
        counts = self._problem_counts()
        items = [
            AdminKnowledgePointListItem(
                id=row.id,
                name=row.name,
                summary=row.summary or "",
                content_markdown=row.content_markdown or "",
                sort_order=row.sort_order,
                problem_count=counts.get(row.name, 0),
            )
            for row in rows
        ]
        if sort_by == "problem_count":
            reverse = sort_order.lower() == "desc"
            items.sort(key=lambda item: (item.problem_count, item.name), reverse=reverse)
        return AdminKnowledgePointListResponse(items=items)

    def create(self, admin_id: int, payload: AdminKnowledgePointCreateRequest) -> AdminKnowledgePointListItem:
        self.ensure_catalog()
        name = payload.name.strip()
        if not name:
            raise AppException(400, "知识点名称不能为空")
        exists = (
            self.db.query(KnowledgePoint)
            .filter(KnowledgePoint.name == name, KnowledgePoint.deleted_at.is_(None))
            .first()
        )
        if exists is not None:
            raise AppException(400, f"知识点「{name}」已存在")
        row = KnowledgePoint(
            name=name,
            summary=(payload.summary or "").strip(),
            content_markdown=payload.content_markdown or "",
            sort_order=payload.sort_order,
            created_by=admin_id,
            updated_by=admin_id,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        self.refresh_registry()
        return AdminKnowledgePointListItem(
            id=row.id,
            name=row.name,
            summary=row.summary or "",
            content_markdown=row.content_markdown or "",
            sort_order=row.sort_order,
            problem_count=0,
        )

    def update(
        self, admin_id: int, point_id: int, payload: AdminKnowledgePointUpdateRequest
    ) -> AdminKnowledgePointListItem:
        self.ensure_catalog()
        row = self.db.get(KnowledgePoint, point_id)
        if row is None or row.deleted_at is not None:
            raise AppException(404, "知识点不存在")
        old_name = row.name
        if payload.name is not None:
            new_name = payload.name.strip()
            if not new_name:
                raise AppException(400, "知识点名称不能为空")
            if new_name != row.name:
                conflict = (
                    self.db.query(KnowledgePoint)
                    .filter(
                        KnowledgePoint.name == new_name,
                        KnowledgePoint.deleted_at.is_(None),
                        KnowledgePoint.id != row.id,
                    )
                    .first()
                )
                if conflict is not None:
                    raise AppException(400, f"知识点「{new_name}」已存在")
                from app.utils.problem_knowledge import apply_knowledge_points_to_problem, get_problem_knowledge_points

                for problem in self.db.query(Problem).filter(Problem.deleted_at.is_(None)).all():
                    tags = get_problem_knowledge_points(problem)
                    if old_name not in tags:
                        continue
                    apply_knowledge_points_to_problem(
                        problem,
                        [new_name if t == old_name else t for t in tags],
                    )
                row.name = new_name
        if payload.summary is not None:
            row.summary = payload.summary.strip()
        if payload.content_markdown is not None:
            row.content_markdown = payload.content_markdown
        if payload.sort_order is not None:
            row.sort_order = payload.sort_order
        row.updated_by = admin_id
        self.db.commit()
        self.db.refresh(row)
        self.refresh_registry()
        counts = self._problem_counts()
        return AdminKnowledgePointListItem(
            id=row.id,
            name=row.name,
            summary=row.summary or "",
            content_markdown=row.content_markdown or "",
            sort_order=row.sort_order,
            problem_count=counts.get(row.name, 0),
        )

    def delete(self, admin_id: int, point_id: int) -> None:
        self.ensure_catalog()
        row = self.db.get(KnowledgePoint, point_id)
        if row is None or row.deleted_at is not None:
            raise AppException(404, "知识点不存在")
        if row.name == "未分类":
            raise AppException(400, "系统保留知识点「未分类」不可删除")
        from app.utils.problem_knowledge import get_problem_knowledge_points

        in_use = 0
        for problem in self.db.query(Problem).filter(Problem.deleted_at.is_(None)).all():
            if row.name in get_problem_knowledge_points(problem):
                in_use += 1
        if in_use > 0:
            raise AppException(400, f"仍有 {in_use} 道题目使用该知识点，无法删除")
        row.deleted_at = datetime.now(timezone.utc)
        row.updated_by = admin_id
        self.db.commit()
        self.refresh_registry()

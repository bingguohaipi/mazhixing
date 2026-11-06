"""In-memory knowledge-point catalog mirror (loaded from DB)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.knowledge.catalog import KnowledgePointEntry, default_seed_entries
from app.models.knowledge_point import KnowledgePoint as KnowledgePointModel

_entries: dict[str, KnowledgePointEntry] = {}


def clear() -> None:
    _entries.clear()


def load_from_defaults() -> None:
    _entries.clear()
    for entry in default_seed_entries():
        _entries[entry.name] = entry


def reload_from_db(db: Session) -> None:
    rows = (
        db.query(KnowledgePointModel)
        .filter(KnowledgePointModel.deleted_at.is_(None))
        .order_by(KnowledgePointModel.sort_order.asc(), KnowledgePointModel.name.asc())
        .all()
    )
    if not rows:
        load_from_defaults()
        return
    _entries.clear()
    for row in rows:
        _entries[row.name] = KnowledgePointEntry(
            name=row.name,
            summary=row.summary or "",
            content_markdown=row.content_markdown or "",
            sort_order=row.sort_order,
        )


def catalog_names() -> frozenset[str]:
    return frozenset(_entries.keys())


def get_entry(name: str) -> KnowledgePointEntry | None:
    key = (name or "").strip()
    if not key:
        return None
    return _entries.get(key)


def sorted_entries() -> tuple[KnowledgePointEntry, ...]:
    return tuple(sorted(_entries.values(), key=lambda e: (e.sort_order, e.name)))

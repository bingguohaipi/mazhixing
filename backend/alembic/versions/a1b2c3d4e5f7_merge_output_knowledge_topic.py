"""merge 输出 knowledge topic into 输入输出

Revision ID: a1b2c3d4e5f7
Revises: f2a3b4c5d6e7
Create Date: 2026-10-23

"""

from __future__ import annotations

import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f7"
down_revision: Union[str, None] = "f2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ALIAS = "输出"
_CANONICAL = "输入输出"


def _merge_tags(raw: object) -> list[str] | None:
    if not isinstance(raw, list):
        return None
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        name = str(item).strip()
        if not name:
            continue
        if name == _ALIAS:
            name = _CANONICAL
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out or None


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT id, knowledge_point, knowledge_points FROM problems "
            "WHERE deleted_at IS NULL"
        )
    ).fetchall()

    for row in rows:
        pid = row[0]
        kp = (row[1] or "").strip()
        tags = row[2]
        new_kp = _CANONICAL if kp == _ALIAS else (kp or None)
        merged = _merge_tags(tags)
        if kp == _ALIAS and merged is None:
            merged = [_CANONICAL]
        elif merged is None and new_kp:
            merged = [new_kp]

        conn.execute(
            sa.text(
                "UPDATE problems SET knowledge_point = :kp, knowledge_points = :kps WHERE id = :id"
            ),
            {
                "id": pid,
                "kp": new_kp,
                "kps": json.dumps(merged, ensure_ascii=False) if merged else None,
            },
        )

    conn.execute(
        sa.text(
            "UPDATE knowledge_points SET deleted_at = CURRENT_TIMESTAMP "
            "WHERE name = :name AND deleted_at IS NULL"
        ),
        {"name": _ALIAS},
    )


def downgrade() -> None:
    pass

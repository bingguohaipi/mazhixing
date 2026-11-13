"""补模型与迁移之间缺失的三列

Revision ID: d2a3b4c5d6e7
Revises: d1e2f3a4b5c6
Create Date: 2026-11-14

- users.avatar_path
- problems.private_no（含索引 ix_problems_private_no）
- student_pets.last_play_at

这些字段在 ORM 模型里存在，但历史迁移漏了 add_column，
MySQL 表结构缺列，查询 users 时会报 1054 Unknown column。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "d2a3b4c5d6e7"
down_revision: Union[str, None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    return column in {col["name"] for col in inspector.get_columns(table)}


def _has_index(table: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    return index_name in {idx["name"] for idx in inspector.get_indexes(table)}


def upgrade() -> None:
    if not _has_column("users", "avatar_path"):
        op.add_column("users", sa.Column("avatar_path", sa.String(length=255), nullable=True))

    if not _has_column("problems", "private_no"):
        op.add_column("problems", sa.Column("private_no", sa.Integer(), nullable=True))
    if not _has_index("problems", "ix_problems_private_no"):
        op.create_index("ix_problems_private_no", "problems", ["private_no"])

    if not _has_column("student_pets", "last_play_at"):
        op.add_column(
            "student_pets",
            sa.Column("last_play_at", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    if _has_column("student_pets", "last_play_at"):
        op.drop_column("student_pets", "last_play_at")

    if _has_index("problems", "ix_problems_private_no"):
        op.drop_index("ix_problems_private_no", table_name="problems")
    if _has_column("problems", "private_no"):
        op.drop_column("problems", "private_no")

    if _has_column("users", "avatar_path"):
        op.drop_column("users", "avatar_path")

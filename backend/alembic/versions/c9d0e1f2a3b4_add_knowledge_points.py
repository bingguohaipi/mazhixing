"""add knowledge_points table

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-10-22

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, None] = "b8c9d0e1f2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_points",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.String(length=512), server_default="", nullable=False),
        sa.Column("content_markdown", sa.Text(), server_default="", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="100", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_knowledge_points_name"),
    )
    op.create_index("idx_knowledge_points_name", "knowledge_points", ["name"], unique=False)
    op.create_index("idx_knowledge_points_deleted_at", "knowledge_points", ["deleted_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_knowledge_points_deleted_at", table_name="knowledge_points")
    op.drop_index("idx_knowledge_points_name", table_name="knowledge_points")
    op.drop_table("knowledge_points")

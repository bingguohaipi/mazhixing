"""admin role, public problem versioning, suggestions

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    return column in {col["name"] for col in inspector.get_columns(table)}


def _has_table(table: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    return table in inspector.get_table_names()


def _has_index(table: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    return index_name in {idx["name"] for idx in inspector.get_indexes(table)}


def upgrade() -> None:
    op.execute(
        sa.text(
            "ALTER TABLE users MODIFY COLUMN role "
            "ENUM('admin','teacher','student','parent') NOT NULL"
        )
    )

    if not _has_column("problems", "scope"):
        op.add_column(
            "problems",
            sa.Column(
                "scope",
                sa.Enum("private", "public", name="problemscope"),
                nullable=False,
                server_default="private",
            ),
        )
    if not _has_column("problems", "publish_status"):
        op.add_column(
            "problems",
            sa.Column(
                "publish_status",
                sa.Enum("draft", "published", "archived", name="publicpublishstatus"),
                nullable=False,
                server_default="published",
            ),
        )
    if not _has_column("problems", "public_group_id"):
        op.add_column("problems", sa.Column("public_group_id", sa.Integer(), nullable=True))
    if not _has_column("problems", "version"):
        op.add_column(
            "problems",
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        )
    if not _has_index("problems", "idx_problems_scope"):
        op.create_index("idx_problems_scope", "problems", ["scope"])
    if not _has_index("problems", "idx_problems_publish_status"):
        op.create_index("idx_problems_publish_status", "problems", ["publish_status"])
    if not _has_index("problems", "idx_problems_public_group_id"):
        op.create_index("idx_problems_public_group_id", "problems", ["public_group_id"])

    if not _has_table("suggestions"):
        op.create_table(
            "suggestions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("from_user_id", sa.Integer(), nullable=False),
            sa.Column("to_user_id", sa.Integer(), nullable=False),
            sa.Column(
                "context_type",
                sa.Enum("general", "problem", name="suggestioncontexttype"),
                nullable=False,
                server_default="general",
            ),
            sa.Column("context_id", sa.Integer(), nullable=True),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("image_urls", sa.Text(), nullable=True),
            sa.Column(
                "status",
                sa.Enum("pending", "read", "resolved", "closed", name="suggestionstatus"),
                nullable=False,
                server_default="pending",
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["from_user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["to_user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("idx_suggestions_from_user_id", "suggestions", ["from_user_id"])
        op.create_index("idx_suggestions_to_user_id", "suggestions", ["to_user_id"])
        op.create_index("idx_suggestions_status", "suggestions", ["status"])


def downgrade() -> None:
    if _has_table("suggestions"):
        op.drop_table("suggestions")
    if _has_index("problems", "idx_problems_public_group_id"):
        op.drop_index("idx_problems_public_group_id", table_name="problems")
    if _has_index("problems", "idx_problems_publish_status"):
        op.drop_index("idx_problems_publish_status", table_name="problems")
    if _has_index("problems", "idx_problems_scope"):
        op.drop_index("idx_problems_scope", table_name="problems")
    if _has_column("problems", "version"):
        op.drop_column("problems", "version")
    if _has_column("problems", "public_group_id"):
        op.drop_column("problems", "public_group_id")
    if _has_column("problems", "publish_status"):
        op.drop_column("problems", "publish_status")
    if _has_column("problems", "scope"):
        op.drop_column("problems", "scope")
    op.execute(
        sa.text(
            "ALTER TABLE users MODIFY COLUMN role "
            "ENUM('teacher','student','parent') NOT NULL"
        )
    )

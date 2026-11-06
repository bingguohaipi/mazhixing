"""add_notices

Revision ID: a1b2c3d4e5f6
Revises: c93e52c1aa80
Create Date: 2026-09-17 10:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "c93e52c1aa80"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notices",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notices_teacher_id"), "notices", ["teacher_id"], unique=False)

    op.create_table(
        "notice_classes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("notice_id", sa.Integer(), nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["notice_id"], ["notices.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("notice_id", "class_id", name="uq_notice_class"),
    )
    op.create_index(op.f("ix_notice_classes_notice_id"), "notice_classes", ["notice_id"], unique=False)
    op.create_index(op.f("ix_notice_classes_class_id"), "notice_classes", ["class_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_notice_classes_class_id"), table_name="notice_classes")
    op.drop_index(op.f("ix_notice_classes_notice_id"), table_name="notice_classes")
    op.drop_table("notice_classes")
    op.drop_index(op.f("ix_notices_teacher_id"), table_name="notices")
    op.drop_table("notices")

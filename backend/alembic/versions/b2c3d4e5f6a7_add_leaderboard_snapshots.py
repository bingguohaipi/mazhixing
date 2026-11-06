"""add_leaderboard_snapshots

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-17 11:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "leaderboard_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=64), nullable=False),
        sa.Column("completed_problems", sa.Integer(), nullable=False),
        sa.Column("accuracy_rate", sa.Float(), nullable=False),
        sa.Column("accuracy_score", sa.Float(), nullable=False),
        sa.Column("time_score", sa.Float(), nullable=False),
        sa.Column("total_score", sa.Float(), nullable=False),
        sa.Column("avg_runtime_ms", sa.Float(), nullable=True),
        sa.Column("refreshed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("class_id", "snapshot_date", "student_id", name="uq_lb_snapshot_student"),
    )
    op.create_index(op.f("ix_leaderboard_snapshots_class_id"), "leaderboard_snapshots", ["class_id"], unique=False)
    op.create_index(op.f("ix_leaderboard_snapshots_snapshot_date"), "leaderboard_snapshots", ["snapshot_date"], unique=False)
    op.create_index(op.f("ix_leaderboard_snapshots_student_id"), "leaderboard_snapshots", ["student_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_leaderboard_snapshots_student_id"), table_name="leaderboard_snapshots")
    op.drop_index(op.f("ix_leaderboard_snapshots_snapshot_date"), table_name="leaderboard_snapshots")
    op.drop_index(op.f("ix_leaderboard_snapshots_class_id"), table_name="leaderboard_snapshots")
    op.drop_table("leaderboard_snapshots")

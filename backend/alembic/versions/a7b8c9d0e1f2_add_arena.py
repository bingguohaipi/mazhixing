"""add arena (擂台) tables and columns

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-10-11

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("problems", sa.Column("arena_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("problems", sa.Column("arena_opened_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_problems_arena_enabled", "problems", ["arena_enabled"], unique=False)

    op.add_column("users", sa.Column("arena_ranking_opt_out", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("arena_agreed_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "arena_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("problem_id", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "in_progress",
                "submitted",
                "exited",
                "expired",
                "cancelled",
                name="arenasessionstatus",
            ),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("exited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submission_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_arena_sessions_user_id", "arena_sessions", ["user_id"], unique=False)
    op.create_index("ix_arena_sessions_problem_id", "arena_sessions", ["problem_id"], unique=False)
    op.create_index("ix_arena_sessions_status", "arena_sessions", ["status"], unique=False)
    op.create_index("ix_arena_sessions_submission_id", "arena_sessions", ["submission_id"], unique=False)

    op.add_column("submissions", sa.Column("arena_session_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_submissions_arena_session_id",
        "submissions",
        "arena_sessions",
        ["arena_session_id"],
        ["id"],
    )
    op.create_index("ix_submissions_arena_session_id", "submissions", ["arena_session_id"], unique=False)

    op.create_table(
        "arena_session_metrics",
        sa.Column("arena_session_id", sa.Integer(), nullable=False),
        sa.Column("first_keystroke_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paste_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("paste_char_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("risk_flags", sa.Text(), nullable=True),
        sa.Column("similarity_max", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["arena_session_id"], ["arena_sessions.id"]),
        sa.PrimaryKeyConstraint("arena_session_id"),
    )

    op.create_table(
        "arena_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("arena_session_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("problem_id", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("submission_id", sa.Integer(), nullable=False),
        sa.Column("judge_status", sa.Enum("PENDING", "AC", "WA", "CE", "TLE", "RE", name="submissionstatus"), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("arena_score", sa.Float(), nullable=True),
        sa.Column(
            "review_status",
            sa.Enum("none", "pending", "approved", "rejected", name="arenareviewstatus"),
            nullable=False,
        ),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reject_reason", sa.Text(), nullable=True),
        sa.Column("ranked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("achieved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["arena_session_id"], ["arena_sessions.id"]),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["submission_id"], ["submissions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("arena_session_id"),
        sa.UniqueConstraint("submission_id"),
    )
    op.create_index("ix_arena_results_user_id", "arena_results", ["user_id"], unique=False)
    op.create_index("ix_arena_results_problem_id", "arena_results", ["problem_id"], unique=False)
    op.create_index("ix_arena_results_language", "arena_results", ["language"], unique=False)
    op.create_index("ix_arena_results_review_status", "arena_results", ["review_status"], unique=False)

    op.create_table(
        "user_notifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("event_key", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_notifications_user_id", "user_notifications", ["user_id"], unique=False)
    op.create_index("ix_user_notifications_event_key", "user_notifications", ["event_key"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_notifications_event_key", table_name="user_notifications")
    op.drop_index("ix_user_notifications_user_id", table_name="user_notifications")
    op.drop_table("user_notifications")
    op.drop_index("ix_arena_results_review_status", table_name="arena_results")
    op.drop_index("ix_arena_results_language", table_name="arena_results")
    op.drop_index("ix_arena_results_problem_id", table_name="arena_results")
    op.drop_index("ix_arena_results_user_id", table_name="arena_results")
    op.drop_table("arena_results")
    op.drop_table("arena_session_metrics")
    op.drop_index("ix_submissions_arena_session_id", table_name="submissions")
    op.drop_constraint("fk_submissions_arena_session_id", "submissions", type_="foreignkey")
    op.drop_column("submissions", "arena_session_id")
    op.drop_index("ix_arena_sessions_submission_id", table_name="arena_sessions")
    op.drop_index("ix_arena_sessions_status", table_name="arena_sessions")
    op.drop_index("ix_arena_sessions_problem_id", table_name="arena_sessions")
    op.drop_index("ix_arena_sessions_user_id", table_name="arena_sessions")
    op.drop_table("arena_sessions")
    op.drop_column("users", "arena_agreed_at")
    op.drop_column("users", "arena_ranking_opt_out")
    op.drop_index("ix_problems_arena_enabled", table_name="problems")
    op.drop_column("problems", "arena_opened_at")
    op.drop_column("problems", "arena_enabled")

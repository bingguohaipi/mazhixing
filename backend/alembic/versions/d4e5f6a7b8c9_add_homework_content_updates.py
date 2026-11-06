"""add homework content updates and student acks

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-09-17

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("homeworks", sa.Column("content_updated_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        "homework_student_acks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("homework_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["homework_id"], ["homeworks.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("homework_id", "student_id", name="uq_homework_student_ack"),
    )
    op.create_index("ix_homework_student_acks_homework_id", "homework_student_acks", ["homework_id"])
    op.create_index("ix_homework_student_acks_student_id", "homework_student_acks", ["student_id"])


def downgrade() -> None:
    op.drop_index("ix_homework_student_acks_student_id", table_name="homework_student_acks")
    op.drop_index("ix_homework_student_acks_homework_id", table_name="homework_student_acks")
    op.drop_table("homework_student_acks")
    op.drop_column("homeworks", "content_updated_at")

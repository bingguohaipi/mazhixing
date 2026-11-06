"""add_student_groups

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-09-17 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "student_groups",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("class_id", "name", name="uq_class_group_name"),
    )
    op.create_index(op.f("ix_student_groups_class_id"), "student_groups", ["class_id"], unique=False)

    with op.batch_alter_table("class_students", schema=None) as batch_op:
        batch_op.add_column(sa.Column("group_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_class_students_group_id", "student_groups", ["group_id"], ["id"])
        batch_op.create_index(batch_op.f("ix_class_students_group_id"), ["group_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("class_students", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_class_students_group_id"))
        batch_op.drop_constraint("fk_class_students_group_id", type_="foreignkey")
        batch_op.drop_column("group_id")

    op.drop_index(op.f("ix_student_groups_class_id"), table_name="student_groups")
    op.drop_table("student_groups")

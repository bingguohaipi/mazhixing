"""suggestion replies

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-03-22

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, None] = "e1f2a3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "suggestion_replies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("suggestion_id", sa.Integer(), nullable=False),
        sa.Column("from_user_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("image_urls", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["from_user_id"], ["users.id"], name="fk_suggestion_replies_from_user"),
        sa.ForeignKeyConstraint(["suggestion_id"], ["suggestions.id"], name="fk_suggestion_replies_suggestion"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_suggestion_replies_suggestion_id", "suggestion_replies", ["suggestion_id"])


def downgrade() -> None:
    op.drop_index("idx_suggestion_replies_suggestion_id", table_name="suggestion_replies")
    op.drop_table("suggestion_replies")

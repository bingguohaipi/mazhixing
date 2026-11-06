"""add problems.knowledge_points JSON

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-10-22

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d0e1f2a3b4c5"
down_revision: Union[str, None] = "c9d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("problems", sa.Column("knowledge_points", sa.JSON(), nullable=True))
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        conn.execute(
            sa.text(
                "UPDATE problems SET knowledge_points = json_array(knowledge_point) "
                "WHERE knowledge_point IS NOT NULL AND trim(knowledge_point) != ''"
            )
        )
    else:
        conn.execute(
            sa.text(
                "UPDATE problems SET knowledge_points = JSON_ARRAY(knowledge_point) "
                "WHERE knowledge_point IS NOT NULL AND TRIM(knowledge_point) != ''"
            )
        )


def downgrade() -> None:
    op.drop_column("problems", "knowledge_points")

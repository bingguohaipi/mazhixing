"""add problems.languages JSON

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-10-22

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, None] = "d0e1f2a3b4c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("problems", sa.Column("languages", sa.JSON(), nullable=True))
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        conn.execute(
            sa.text(
                "UPDATE problems SET languages = json_array("
                "CASE language WHEN 'Python' THEN 'Python' WHEN 'C++' THEN 'C++' "
                "ELSE language END)"
            )
        )
    else:
        conn.execute(
            sa.text(
                "UPDATE problems SET languages = JSON_ARRAY("
                "CASE language WHEN 'Python' THEN 'Python' WHEN 'C++' THEN 'C++' "
                "ELSE language END)"
            )
        )


def downgrade() -> None:
    op.drop_column("problems", "languages")

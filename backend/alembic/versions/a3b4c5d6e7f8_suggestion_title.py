"""suggestion title

Revision ID: a3b4c5d6e7f8
Revises: f2a3b4c5d6e7
Create Date: 2026-11-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a3b4c5d6e7f8"
down_revision: Union[str, None] = "f2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "suggestions",
        sa.Column("title", sa.String(length=200), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("suggestions", "title")

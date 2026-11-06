"""suggestion satisfaction rating

Revision ID: b4c5d6e7f8a9
Revises: a3b4c5d6e7f8
Create Date: 2026-11-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b4c5d6e7f8a9"
down_revision: Union[str, None] = "a3b4c5d6e7f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("suggestions", sa.Column("satisfaction_rating", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("suggestions", "satisfaction_rating")

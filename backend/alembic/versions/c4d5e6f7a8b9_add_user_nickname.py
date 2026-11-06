"""add users.nickname

Revision ID: c4d5e6f7a8b9
Revises: a1b2c3d4e5f7
Create Date: 2026-10-23

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, None] = "a1b2c3d4e5f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("nickname", sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "nickname")

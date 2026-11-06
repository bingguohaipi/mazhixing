"""problems.image_urls

Revision ID: f1a2b3c4d5e6
Revises: e1f2a3b4c5d6
Create Date: 2026-11-01

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "e1f2a3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("problems", sa.Column("image_urls", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("problems", "image_urls")

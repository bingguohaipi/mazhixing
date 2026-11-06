"""merge alembic heads (public langs + verification out_id)

Revision ID: e1f2a3b4c5d6
Revises: b2c3d4e5f6a8, d7e8f9a0b1c2
Create Date: 2026-10-31

"""

from typing import Sequence, Union

revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, tuple[str, ...], None] = ("b2c3d4e5f6a8", "d7e8f9a0b1c2")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

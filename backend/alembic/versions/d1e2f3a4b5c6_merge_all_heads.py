"""merge all alembic heads (public langs / suggestion rating / out_id / image urls)

Revision ID: d1e2f3a4b5c6
Revises: b2c3d4e5f6a8, b4c5d6e7f8a9, d7e8f9a0b1c2, f1a2b3c4d5e6
Create Date: 2026-11-13

合并历史上被重复 revision id（e1f2a3b4c5d6）搅乱的四个并行 head。
"""

from typing import Sequence, Union

revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, Sequence[str], None] = (
    "b2c3d4e5f6a8",
    "b4c5d6e7f8a9",
    "d7e8f9a0b1c2",
    "f1a2b3c4d5e6",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

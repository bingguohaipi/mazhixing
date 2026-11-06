"""public problems default Python + C++

Revision ID: b2c3d4e5f6a8
Revises: a1b2c3d4e5f7
Create Date: 2026-10-23

"""

from __future__ import annotations

import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a8"
down_revision: Union[str, None] = "a1b2c3d4e5f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_DUAL = json.dumps(["Python", "C++"], ensure_ascii=False)


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE problems SET languages = :langs "
            "WHERE deleted_at IS NULL AND lower(scope) = 'public'"
        ),
        {"langs": _DUAL},
    )


def downgrade() -> None:
    pass

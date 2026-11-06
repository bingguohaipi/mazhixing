"""promote legacy private problems to public catalog

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-10-09

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE problems
            SET
                scope = 'public',
                publish_status = CASE
                    WHEN publish_status = 'draft' THEN 'published'
                    ELSE publish_status
                END,
                public_group_id = COALESCE(public_group_id, id),
                version = CASE WHEN version IS NULL OR version < 1 THEN 1 ELSE version END
            WHERE scope = 'private' AND deleted_at IS NULL
            """
        )
    )


def downgrade() -> None:
    pass

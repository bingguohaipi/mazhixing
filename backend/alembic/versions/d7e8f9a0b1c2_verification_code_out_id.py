"""verification_codes out_id for Dypns

Revision ID: d7e8f9a0b1c2
Revises: c4d5e6f7a8b9
Create Date: 2026-10-31

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d7e8f9a0b1c2"
down_revision: Union[str, None] = "c4d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("verification_codes", sa.Column("out_id", sa.String(length=64), nullable=True))
    op.create_index(op.f("ix_verification_codes_out_id"), "verification_codes", ["out_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_verification_codes_out_id"), table_name="verification_codes")
    op.drop_column("verification_codes", "out_id")

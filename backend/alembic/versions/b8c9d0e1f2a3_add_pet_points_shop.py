"""add pet points and shop

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-10-20

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b8c9d0e1f2a3"
down_revision: Union[str, None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pet_system_config",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("points_launched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("points_per_first_ac", sa.Integer(), server_default="10", nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        sa.text(
            "INSERT INTO pet_system_config (id, points_launched_at, points_per_first_ac) "
            "VALUES (1, CURRENT_TIMESTAMP, 10)"
        )
    )

    op.create_table(
        "student_points_accounts",
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("balance", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_earned", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_spent", sa.Integer(), server_default="0", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("student_id"),
    )

    op.create_table(
        "shop_items",
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("category", sa.Enum("pet", "food", "drink", name="shopitemcategory"), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("rarity", sa.Enum("common", "rare", name="shopitemrarity"), nullable=True),
        sa.Column("preview_asset_url", sa.String(length=255), nullable=False),
        sa.Column("asset_key", sa.String(length=64), nullable=False),
        sa.Column("effect_json", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.PrimaryKeyConstraint("sku"),
    )
    op.create_index("ix_shop_items_category", "shop_items", ["category"], unique=False)

    op.create_table(
        "point_ledgers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column(
            "type",
            sa.Enum("EARN_FIRST_AC", "SPEND_SHOP", "ADMIN_ADJUST", name="pointledgertype"),
            nullable=False,
        ),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("ref_type", sa.String(length=32), nullable=True),
        sa.Column("ref_id", sa.Integer(), nullable=True),
        sa.Column("ref_title", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_point_ledgers_student_id", "point_ledgers", ["student_id"], unique=False)
    op.create_index("ix_point_ledgers_type", "point_ledgers", ["type"], unique=False)

    op.create_table(
        "point_first_ac_grants",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("problem_id", sa.Integer(), nullable=False),
        sa.Column("submission_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["submission_id"], ["submissions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "problem_id", name="uq_first_ac_student_problem"),
        sa.UniqueConstraint("submission_id"),
    )
    op.create_index("ix_point_first_ac_grants_student_id", "point_first_ac_grants", ["student_id"], unique=False)
    op.create_index("ix_point_first_ac_grants_problem_id", "point_first_ac_grants", ["problem_id"], unique=False)

    op.create_table(
        "student_pets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("catalog_sku", sa.String(length=64), nullable=False),
        sa.Column("level", sa.Integer(), server_default="1", nullable=False),
        sa.Column("exp", sa.Integer(), server_default="0", nullable=False),
        sa.Column("satiety", sa.Integer(), server_default="80", nullable=False),
        sa.Column("mood", sa.Integer(), server_default="80", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("last_decay_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("drink_buff_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["catalog_sku"], ["shop_items.sku"]),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_student_pets_student_id", "student_pets", ["student_id"], unique=False)
    op.create_index("ix_student_pets_catalog_sku", "student_pets", ["catalog_sku"], unique=False)

    op.create_table(
        "student_inventories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("quantity", sa.Integer(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(["sku"], ["shop_items.sku"]),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "sku", name="uq_student_inventory_sku"),
    )
    op.create_index("ix_student_inventories_student_id", "student_inventories", ["student_id"], unique=False)
    op.create_index("ix_student_inventories_sku", "student_inventories", ["sku"], unique=False)

    op.create_table(
        "student_pet_settings",
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("desktop_pet_enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("silent_while_coding", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("student_id"),
    )


def downgrade() -> None:
    op.drop_table("student_pet_settings")
    op.drop_index("ix_student_inventories_sku", table_name="student_inventories")
    op.drop_index("ix_student_inventories_student_id", table_name="student_inventories")
    op.drop_table("student_inventories")
    op.drop_index("ix_student_pets_catalog_sku", table_name="student_pets")
    op.drop_index("ix_student_pets_student_id", table_name="student_pets")
    op.drop_table("student_pets")
    op.drop_index("ix_point_first_ac_grants_problem_id", table_name="point_first_ac_grants")
    op.drop_index("ix_point_first_ac_grants_student_id", table_name="point_first_ac_grants")
    op.drop_table("point_first_ac_grants")
    op.drop_index("ix_point_ledgers_type", table_name="point_ledgers")
    op.drop_index("ix_point_ledgers_student_id", table_name="point_ledgers")
    op.drop_table("point_ledgers")
    op.drop_index("ix_shop_items_category", table_name="shop_items")
    op.drop_table("shop_items")
    op.drop_table("student_points_accounts")
    op.drop_table("pet_system_config")

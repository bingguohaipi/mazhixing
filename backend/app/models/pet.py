import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ShopItemCategory(str, enum.Enum):
    PET = "pet"
    FOOD = "food"
    DRINK = "drink"


class ShopItemRarity(str, enum.Enum):
    COMMON = "common"
    RARE = "rare"


class PointLedgerType(str, enum.Enum):
    EARN_FIRST_AC = "EARN_FIRST_AC"
    SPEND_SHOP = "SPEND_SHOP"
    ADMIN_ADJUST = "ADMIN_ADJUST"


class PetSystemConfig(Base):
    __tablename__ = "pet_system_config"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    points_launched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    points_per_first_ac: Mapped[int] = mapped_column(Integer, default=10, server_default="10")


class StudentPointsAccount(Base):
    __tablename__ = "student_points_accounts"

    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    balance: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_earned: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_spent: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(),
        onupdate=lambda: datetime.now(),
        server_default=func.now(),
    )


class PointLedger(Base, TimestampMixin):
    __tablename__ = "point_ledgers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[PointLedgerType] = mapped_column(Enum(PointLedgerType), index=True)
    delta: Mapped[int] = mapped_column(Integer)
    balance_after: Mapped[int] = mapped_column(Integer)
    ref_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ref_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ref_title: Mapped[str | None] = mapped_column(String(255), nullable=True)


class PointFirstAcGrant(Base):
    __tablename__ = "point_first_ac_grants"
    __table_args__ = (UniqueConstraint("student_id", "problem_id", name="uq_first_ac_student_problem"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(),
        server_default=func.now(),
    )


class ShopItem(Base):
    __tablename__ = "shop_items"

    sku: Mapped[str] = mapped_column(String(64), primary_key=True)
    category: Mapped[ShopItemCategory] = mapped_column(Enum(ShopItemCategory), index=True)
    name: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(String(255), default="")
    price: Mapped[int] = mapped_column(Integer)
    rarity: Mapped[ShopItemRarity | None] = mapped_column(Enum(ShopItemRarity), nullable=True)
    preview_asset_url: Mapped[str] = mapped_column(String(255), default="")
    asset_key: Mapped[str] = mapped_column(String(64), default="")
    effect_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")


class StudentPet(Base, TimestampMixin):
    __tablename__ = "student_pets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    catalog_sku: Mapped[str] = mapped_column(ForeignKey("shop_items.sku"), index=True)
    level: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    exp: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    satiety: Mapped[int] = mapped_column(Integer, default=80, server_default="80")
    mood: Mapped[int] = mapped_column(Integer, default=80, server_default="80")
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    last_decay_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_play_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    drink_buff_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class StudentInventory(Base):
    __tablename__ = "student_inventories"
    __table_args__ = (UniqueConstraint("student_id", "sku", name="uq_student_inventory_sku"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    sku: Mapped[str] = mapped_column(ForeignKey("shop_items.sku"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class StudentPetSetting(Base):
    __tablename__ = "student_pet_settings"

    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    desktop_pet_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    silent_while_coding: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(),
        onupdate=lambda: datetime.now(),
        server_default=func.now(),
    )

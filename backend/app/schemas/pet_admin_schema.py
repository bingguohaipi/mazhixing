from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.pet_shop_schema import ShopItemCategoryLiteral, ShopItemRarityLiteral


class AdminShopItemListItem(BaseModel):
    sku: str
    category: ShopItemCategoryLiteral
    category_label: str
    name: str
    description: str
    price: int
    rarity: ShopItemRarityLiteral | None
    asset_key: str
    preview_asset_url: str
    is_active: bool


class AdminShopItemListResponse(BaseModel):
    items: list[AdminShopItemListItem]


class AdminShopItemCreateRequest(BaseModel):
    sku: str = Field(min_length=2, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    category: ShopItemCategoryLiteral
    name: str = Field(min_length=1, max_length=64)
    description: str = Field(default="", max_length=255)
    price: int = Field(ge=1, le=100000)
    asset_key: str = Field(min_length=1, max_length=64)
    rarity: ShopItemRarityLiteral | None = None
    effect_exp: int | None = Field(default=None, ge=0, le=9999)
    effect_satiety: int | None = Field(default=None, ge=0, le=9999)
    effect_mood: int | None = Field(default=None, ge=0, le=9999)
    is_active: bool = True


class AdminShopItemPatchRequest(BaseModel):
    name: str | None = Field(default=None, max_length=64)
    description: str | None = Field(default=None, max_length=255)
    price: int | None = Field(default=None, ge=1, le=100000)
    preview_asset_url: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class AdminPetPointsConfigResponse(BaseModel):
    points_launched_at: datetime | None
    points_per_first_ac: int

from typing import Literal

from pydantic import BaseModel, Field

ShopItemCategoryLiteral = Literal["pet", "food", "drink"]
ShopItemRarityLiteral = Literal["common", "rare"]


class PetShopCatalogItem(BaseModel):
    sku: str
    category: ShopItemCategoryLiteral
    name: str
    description: str
    price: int
    rarity: ShopItemRarityLiteral | None = None
    preview_asset_url: str
    lottie_url: str | None = None
    effect_summary: str | None = None
    owned: bool = False
    can_afford: bool = True


class PetShopCatalogResponse(BaseModel):
    balance: int
    items: list[PetShopCatalogItem]


class PetShopOrderCreateRequest(BaseModel):
    sku: str
    quantity: int = Field(default=1, ge=1, le=99)


class PetShopOrderGrantPet(BaseModel):
    type: Literal["pet"] = "pet"
    student_pet_id: int


class PetShopOrderGrantInventory(BaseModel):
    type: Literal["inventory"] = "inventory"
    sku: str
    quantity_after: int


class PetShopOrderResponse(BaseModel):
    order_id: str
    sku: str
    spent: int
    balance: int
    grant: PetShopOrderGrantPet | PetShopOrderGrantInventory

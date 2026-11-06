from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

ShopItemCategoryLiteral = Literal["pet", "food", "drink"]
PetStateHintLiteral = Literal["idle", "sleep", "happy"]
PetBuffTypeLiteral = Literal["drink_mood"]


class PetBuffItem(BaseModel):
    type: PetBuffTypeLiteral
    expires_at: datetime


class StudentPetListItem(BaseModel):
    id: int
    catalog_sku: str
    name: str
    level: int
    exp: int
    exp_to_next: int
    satiety: int
    mood: int
    is_active: bool
    asset_key: str


class StudentPetListResponse(BaseModel):
    items: list[StudentPetListItem]


class StudentPetActiveResponse(BaseModel):
    id: int
    catalog_sku: str
    name: str
    level: int
    exp: int
    exp_to_next: int
    satiety: int
    mood: int
    is_active: bool
    asset_key: str
    state_hint: PetStateHintLiteral
    buffs: list[PetBuffItem] = Field(default_factory=list)
    last_sync_at: datetime


PetPlayReactionLiteral = Literal["jump", "happy", "wiggle"]


class PetPlayResponse(BaseModel):
    pet: StudentPetActiveResponse
    reaction: PetPlayReactionLiteral
    mood_delta: int


class InventoryItem(BaseModel):
    sku: str
    name: str
    category: ShopItemCategoryLiteral
    quantity: int


class StudentInventoryResponse(BaseModel):
    items: list[InventoryItem]


class InventoryUseRequest(BaseModel):
    sku: str
    quantity: int = Field(default=1, ge=1, le=10)


class InventoryUsePetSnapshot(BaseModel):
    id: int
    level: int
    exp: int
    satiety: int
    mood: int
    leveled_up: bool
    exp_to_next: int


class InventoryUseResponse(BaseModel):
    pet: InventoryUsePetSnapshot
    inventory_quantity_after: int


class PetSyncRequest(BaseModel):
    client_scene: Literal["default", "coding", "dashboard"] | None = None


class StudentPetSettingsResponse(BaseModel):
    desktop_pet_enabled: bool
    silent_while_coding: bool


class StudentPetSettingsPatchRequest(BaseModel):
    desktop_pet_enabled: bool | None = None
    silent_while_coding: bool | None = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> "StudentPetSettingsPatchRequest":
        if self.desktop_pet_enabled is None and self.silent_while_coding is None:
            raise ValueError("至少提供一个设置项")
        return self

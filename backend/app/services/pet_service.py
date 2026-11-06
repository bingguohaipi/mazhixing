import json
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.pet import (
    ShopItem,
    ShopItemCategory,
    StudentInventory,
    StudentPet,
    StudentPetSetting,
)
from app.schemas.pet_schema import (
    InventoryItem,
    InventoryUsePetSnapshot,
    InventoryUseResponse,
    PetBuffItem,
    PetPlayResponse,
    StudentInventoryResponse,
    StudentPetActiveResponse,
    StudentPetListItem,
    StudentPetListResponse,
    StudentPetSettingsResponse,
)
from app.schemas.pet_shop_schema import (
    PetShopCatalogItem,
    PetShopCatalogResponse,
    PetShopOrderGrantInventory,
    PetShopOrderGrantPet,
    PetShopOrderResponse,
)
from app.services.pet_catalog_defaults import ensure_shop_catalog
from app.services.pet_points_service import PetPointsService

from app.services.pet_decay import compute_decay

MAX_LEVEL = 20
MAX_INVENTORY = 99
PLAY_COOLDOWN_SECONDS = 2.0
MOOD_PLAY_GAIN_MIN = 4
MOOD_PLAY_GAIN_MAX = 8
PET_PLAY_REACTIONS = ("jump", "happy", "wiggle")


def exp_to_next(level: int) -> int:
    if level >= MAX_LEVEL:
        return 0
    return 20 + (level - 1) * 15


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


class PetService:
    def __init__(self, db: Session):
        self.db = db
        self.points = PetPointsService(db)

    def _shop_item(self, sku: str) -> ShopItem:
        item = self.db.get(ShopItem, sku)
        if item is None or not item.is_active:
            raise AppException(404, "商品不存在")
        return item

    def _pet_display_name(self, pet: StudentPet) -> str:
        item = self._shop_item(pet.catalog_sku)
        return item.name

    def _apply_decay(self, pet: StudentPet, now: datetime) -> None:
        if not pet.is_active:
            return
        last = pet.last_decay_at or pet.created_at
        satiety, mood, new_last = compute_decay(pet.satiety, pet.mood, last, now)
        if new_last == (pet.last_decay_at or pet.created_at) and satiety == pet.satiety:
            return
        pet.satiety = satiety
        pet.mood = mood
        pet.last_decay_at = new_last

    def _state_hint(self, pet: StudentPet) -> str:
        if pet.satiety <= 0:
            return "sleep"
        if pet.mood >= 70 and pet.satiety >= 30:
            return "happy"
        return "idle"

    def _buffs_for_pet(self, pet: StudentPet, now: datetime) -> list[PetBuffItem]:
        if pet.drink_buff_expires_at is None:
            return []
        expires = pet.drink_buff_expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires <= now:
            pet.drink_buff_expires_at = None
            return []
        return [PetBuffItem(type="drink_mood", expires_at=expires)]

    def _to_active(self, pet: StudentPet, now: datetime) -> StudentPetActiveResponse:
        item = self._shop_item(pet.catalog_sku)
        buffs = self._buffs_for_pet(pet, now)
        return StudentPetActiveResponse(
            id=pet.id,
            catalog_sku=pet.catalog_sku,
            name=item.name,
            level=pet.level,
            exp=pet.exp,
            exp_to_next=exp_to_next(pet.level),
            satiety=pet.satiety,
            mood=pet.mood,
            is_active=pet.is_active,
            asset_key=item.asset_key,
            state_hint=self._state_hint(pet),  # type: ignore[arg-type]
            buffs=buffs,
            last_sync_at=now,
        )

    def _to_list_item(self, pet: StudentPet) -> StudentPetListItem:
        item = self._shop_item(pet.catalog_sku)
        return StudentPetListItem(
            id=pet.id,
            catalog_sku=pet.catalog_sku,
            name=item.name,
            level=pet.level,
            exp=pet.exp,
            exp_to_next=exp_to_next(pet.level),
            satiety=pet.satiety,
            mood=pet.mood,
            is_active=pet.is_active,
            asset_key=item.asset_key,
        )

    def _ensure_settings(self, student_id: int) -> StudentPetSetting:
        row = self.db.get(StudentPetSetting, student_id)
        if row is None:
            row = StudentPetSetting(student_id=student_id)
            self.db.add(row)
            self.db.commit()
            self.db.refresh(row)
        return row

    def get_settings(self, student_id: int) -> StudentPetSettingsResponse:
        row = self._ensure_settings(student_id)
        return StudentPetSettingsResponse(
            desktop_pet_enabled=row.desktop_pet_enabled,
            silent_while_coding=row.silent_while_coding,
        )

    def patch_settings(
        self,
        student_id: int,
        desktop_pet_enabled: bool | None,
        silent_while_coding: bool | None,
    ) -> StudentPetSettingsResponse:
        row = self._ensure_settings(student_id)
        if desktop_pet_enabled is not None:
            row.desktop_pet_enabled = desktop_pet_enabled
        if silent_while_coding is not None:
            row.silent_while_coding = silent_while_coding
        self.db.commit()
        self.db.refresh(row)
        return self.get_settings(student_id)

    def list_pets(self, student_id: int) -> StudentPetListResponse:
        pets = (
            self.db.query(StudentPet)
            .filter(StudentPet.student_id == student_id)
            .order_by(StudentPet.id.asc())
            .all()
        )
        return StudentPetListResponse(items=[self._to_list_item(p) for p in pets])

    def get_active_pet(self, student_id: int) -> StudentPetActiveResponse | None:
        now = datetime.now(timezone.utc)
        pet = (
            self.db.query(StudentPet)
            .filter(StudentPet.student_id == student_id, StudentPet.is_active.is_(True))
            .first()
        )
        if pet is None:
            return None
        self._apply_decay(pet, now)
        self.db.commit()
        self.db.refresh(pet)
        return self._to_active(pet, now)

    def sync_active_pet(self, student_id: int) -> StudentPetActiveResponse | None:
        return self.get_active_pet(student_id)

    def play_with_active_pet(self, student_id: int) -> PetPlayResponse:
        now = datetime.now(timezone.utc)
        pet = (
            self.db.query(StudentPet)
            .filter(StudentPet.student_id == student_id, StudentPet.is_active.is_(True))
            .first()
        )
        if pet is None:
            raise AppException(404, "暂无出战小伙伴")
        self._apply_decay(pet, now)
        if pet.satiety <= 0:
            raise AppException(400, "小伙伴太饿了，先去喂点吃的吧")
        if pet.last_play_at is not None:
            last = pet.last_play_at
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            if (now - last).total_seconds() < PLAY_COOLDOWN_SECONDS:
                raise AppException(429, "小伙伴需要歇一会儿~", status_code=429)
        gain = random.randint(MOOD_PLAY_GAIN_MIN, MOOD_PLAY_GAIN_MAX)
        pet.mood = _clamp(pet.mood + gain, 0, 100)
        pet.last_play_at = now
        reaction = random.choice(PET_PLAY_REACTIONS)
        self.db.commit()
        self.db.refresh(pet)
        return PetPlayResponse(
            pet=self._to_active(pet, now),
            reaction=reaction,  # type: ignore[arg-type]
            mood_delta=gain,
        )

    def activate_pet(self, student_id: int, pet_id: int) -> StudentPetActiveResponse:
        pet = self.db.get(StudentPet, pet_id)
        if pet is None or pet.student_id != student_id:
            raise AppException(404, "宠物不存在")
        others = self.db.query(StudentPet).filter(StudentPet.student_id == student_id).all()
        for other in others:
            other.is_active = other.id == pet.id
        pet.is_active = True
        if pet.last_decay_at is None:
            pet.last_decay_at = datetime.now(timezone.utc)
        self.db.commit()
        active = self.get_active_pet(student_id)
        if active is None:
            raise AppException(500, "设置出战失败")
        return active

    def get_catalog(self, student_id: int, category: str | None) -> PetShopCatalogResponse:
        ensure_shop_catalog(self.db)
        summary = self.points.get_summary(student_id)
        owned_skus = {
            row.catalog_sku
            for row in self.db.query(StudentPet.catalog_sku)
            .filter(StudentPet.student_id == student_id)
            .all()
        }
        query = self.db.query(ShopItem).filter(ShopItem.is_active.is_(True))
        if category:
            query = query.filter(ShopItem.category == ShopItemCategory(category))
        items: list[PetShopCatalogItem] = []
        for row in query.order_by(ShopItem.price.asc()).all():
            effect_summary = None
            if row.effect_json:
                try:
                    data = json.loads(row.effect_json)
                    if row.category == ShopItemCategory.FOOD:
                        effect_summary = f"+{data.get('exp', 0)} 经验，+{data.get('satiety', 0)} 饱食"
                    elif row.category == ShopItemCategory.DRINK:
                        effect_summary = f"+{data.get('mood', 0)} 心情"
                except json.JSONDecodeError:
                    effect_summary = None
            lottie_url = f"/lottie/{row.asset_key}.json" if row.category == ShopItemCategory.PET else None
            items.append(
                PetShopCatalogItem(
                    sku=row.sku,
                    category=row.category.value,
                    name=row.name,
                    description=row.description,
                    price=row.price,
                    rarity=row.rarity.value if row.rarity else None,
                    preview_asset_url=row.preview_asset_url,
                    lottie_url=lottie_url,
                    effect_summary=effect_summary,
                    owned=row.sku in owned_skus if row.category == ShopItemCategory.PET else False,
                    can_afford=summary.balance >= row.price,
                )
            )
        return PetShopCatalogResponse(balance=summary.balance, items=items)

    def create_order(self, student_id: int, sku: str, quantity: int) -> PetShopOrderResponse:
        ensure_shop_catalog(self.db)
        item = self._shop_item(sku)
        if item.category == ShopItemCategory.PET:
            if quantity != 1:
                raise AppException(400, "宠物只能购买 1 只")
            exists = (
                self.db.query(StudentPet)
                .filter(StudentPet.student_id == student_id, StudentPet.catalog_sku == sku)
                .first()
            )
            if exists is not None:
                raise AppException(400, "已拥有该宠物")
            total = item.price
        else:
            total = item.price * quantity
            inv = (
                self.db.query(StudentInventory)
                .filter(StudentInventory.student_id == student_id, StudentInventory.sku == sku)
                .first()
            )
            current = inv.quantity if inv else 0
            if current + quantity > MAX_INVENTORY:
                raise AppException(400, f"背包上限 {MAX_INVENTORY}")

        balance = self.points.spend_points(student_id, total, item.name)
        order_id = f"ord_{uuid.uuid4().hex[:12]}"

        if item.category == ShopItemCategory.PET:
            has_active = (
                self.db.query(StudentPet)
                .filter(StudentPet.student_id == student_id, StudentPet.is_active.is_(True))
                .first()
            )
            pet = StudentPet(
                student_id=student_id,
                catalog_sku=sku,
                is_active=has_active is None,
                last_decay_at=datetime.now(timezone.utc),
            )
            self.db.add(pet)
            self.db.commit()
            self.db.refresh(pet)
            return PetShopOrderResponse(
                order_id=order_id,
                sku=sku,
                spent=total,
                balance=balance,
                grant=PetShopOrderGrantPet(student_pet_id=pet.id),
            )

        inv = (
            self.db.query(StudentInventory)
            .filter(StudentInventory.student_id == student_id, StudentInventory.sku == sku)
            .first()
        )
        if inv is None:
            inv = StudentInventory(student_id=student_id, sku=sku, quantity=0)
            self.db.add(inv)
            self.db.flush()
        inv.quantity += quantity
        self.db.commit()
        return PetShopOrderResponse(
            order_id=order_id,
            sku=sku,
            spent=total,
            balance=balance,
            grant=PetShopOrderGrantInventory(sku=sku, quantity_after=inv.quantity),
        )

    def list_inventory(self, student_id: int) -> StudentInventoryResponse:
        rows = (
            self.db.query(StudentInventory)
            .filter(StudentInventory.student_id == student_id, StudentInventory.quantity > 0)
            .all()
        )
        items: list[InventoryItem] = []
        for row in rows:
            item = self._shop_item(row.sku)
            items.append(
                InventoryItem(
                    sku=row.sku,
                    name=item.name,
                    category=item.category.value,  # type: ignore[arg-type]
                    quantity=row.quantity,
                )
            )
        return StudentInventoryResponse(items=items)

    def _add_exp(self, pet: StudentPet, amount: int) -> bool:
        leveled = False
        if pet.level >= MAX_LEVEL:
            return False
        pet.exp += amount
        while pet.level < MAX_LEVEL and pet.exp >= exp_to_next(pet.level):
            pet.exp -= exp_to_next(pet.level)
            pet.level += 1
            leveled = True
        if pet.level >= MAX_LEVEL:
            pet.exp = min(pet.exp, exp_to_next(MAX_LEVEL))
        return leveled

    def use_inventory(self, student_id: int, sku: str, quantity: int) -> InventoryUseResponse:
        pet = (
            self.db.query(StudentPet)
            .filter(StudentPet.student_id == student_id, StudentPet.is_active.is_(True))
            .first()
        )
        if pet is None:
            raise AppException(400, "请先设置一只出战宠物")

        inv = (
            self.db.query(StudentInventory)
            .filter(StudentInventory.student_id == student_id, StudentInventory.sku == sku)
            .first()
        )
        if inv is None or inv.quantity < quantity:
            raise AppException(400, "背包数量不足")

        item = self._shop_item(sku)
        if item.category not in (ShopItemCategory.FOOD, ShopItemCategory.DRINK):
            raise AppException(400, "该物品不可使用")

        effect = json.loads(item.effect_json or "{}")
        leveled = False
        for _ in range(quantity):
            if item.category == ShopItemCategory.FOOD:
                leveled = self._add_exp(pet, int(effect.get("exp", 0))) or leveled
                pet.satiety = _clamp(pet.satiety + int(effect.get("satiety", 0)), 0, 100)
            else:
                pet.mood = _clamp(pet.mood + int(effect.get("mood", 0)), 0, 100)
                minutes = int(effect.get("buff_minutes", 30))
                now = datetime.now(timezone.utc)
                base = pet.drink_buff_expires_at or now
                if base.tzinfo is None:
                    base = base.replace(tzinfo=timezone.utc)
                if base < now:
                    base = now
                pet.drink_buff_expires_at = base + timedelta(minutes=minutes)

        inv.quantity -= quantity
        if inv.quantity <= 0:
            self.db.delete(inv)
            qty_after = 0
        else:
            qty_after = inv.quantity

        self.db.commit()
        self.db.refresh(pet)

        return InventoryUseResponse(
            pet=InventoryUsePetSnapshot(
                id=pet.id,
                level=pet.level,
                exp=pet.exp,
                satiety=pet.satiety,
                mood=pet.mood,
                leveled_up=leveled,
                exp_to_next=exp_to_next(pet.level),
            ),
            inventory_quantity_after=qty_after,
        )

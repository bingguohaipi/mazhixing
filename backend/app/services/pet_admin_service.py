import json
import re
import uuid
from pathlib import Path

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.pet import ShopItem, ShopItemCategory, ShopItemRarity, StudentInventory, StudentPet
from app.schemas.pet_admin_schema import (
    AdminPetPointsConfigResponse,
    AdminShopItemCreateRequest,
    AdminShopItemListItem,
    AdminShopItemListResponse,
    AdminShopItemPatchRequest,
)
from app.services.pet_catalog_defaults import ensure_shop_catalog
from app.services.pet_points_service import PetPointsService
from app.utils.pet_shop_labels import CATEGORY_ZH_TO_ENUM, category_label

UPLOAD_ROOT = Path(__file__).resolve().parent.parent.parent / "uploads"
PREVIEW_DIR = UPLOAD_ROOT / "pet-shop"
ALLOWED_PREVIEW_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
MAX_PREVIEW_BYTES = 2 * 1024 * 1024


class PetAdminService:
    def __init__(self, db: Session):
        self.db = db

    def list_shop_items(self, keyword: str | None = None) -> AdminShopItemListResponse:
        ensure_shop_catalog(self.db)
        query = self.db.query(ShopItem)
        raw = (keyword or "").strip()
        if raw:
            like = f"%{raw}%"
            filters = [
                ShopItem.sku.ilike(like),
                ShopItem.name.ilike(like),
                ShopItem.description.ilike(like),
                ShopItem.asset_key.ilike(like),
            ]
            matched_category = CATEGORY_ZH_TO_ENUM.get(raw)
            if matched_category is not None:
                filters.append(ShopItem.category == matched_category)
            else:
                for zh, cat in CATEGORY_ZH_TO_ENUM.items():
                    if raw in zh:
                        filters.append(ShopItem.category == cat)
                        break
            query = query.filter(or_(*filters))
        rows = query.order_by(ShopItem.category.asc(), ShopItem.price.asc()).all()
        items = [self._to_admin_item(row) for row in rows]
        return AdminShopItemListResponse(items=items)

    def create_shop_item(self, payload: AdminShopItemCreateRequest) -> AdminShopItemListItem:
        sku = payload.sku.strip()
        if self.db.get(ShopItem, sku) is not None:
            raise AppException(400, "SKU 已存在")
        category = ShopItemCategory(payload.category)
        rarity = ShopItemRarity(payload.rarity) if payload.rarity else None
        if category == ShopItemCategory.PET and rarity is None:
            rarity = ShopItemRarity.COMMON
        if category != ShopItemCategory.PET and rarity is not None:
            raise AppException(400, "仅宠物可设置稀有度")
        effect_json = self._build_effect_json(category, payload)
        asset_key = payload.asset_key.strip()
        if not re.match(r"^[a-z][a-z0-9_]*$", asset_key):
            raise AppException(400, "资源 key 格式无效")
        item = ShopItem(
            sku=sku,
            category=category,
            name=payload.name.strip(),
            description=(payload.description or "").strip(),
            price=payload.price,
            rarity=rarity,
            preview_asset_url="",
            asset_key=asset_key,
            effect_json=effect_json,
            is_active=payload.is_active,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return self._to_admin_item(item)

    def delete_shop_item(self, sku: str) -> None:
        item = self.db.get(ShopItem, sku)
        if item is None:
            raise AppException(404, "商品不存在")
        pet_refs = (
            self.db.query(func.count(StudentPet.id)).filter(StudentPet.catalog_sku == sku).scalar() or 0
        )
        inv_refs = (
            self.db.query(func.count(StudentInventory.id)).filter(StudentInventory.sku == sku).scalar() or 0
        )
        if pet_refs > 0 or inv_refs > 0:
            raise AppException(400, "已有学生拥有该商品，无法删除，可改为下架")
        self.db.delete(item)
        self.db.commit()

    def patch_shop_item(self, sku: str, payload: AdminShopItemPatchRequest) -> AdminShopItemListItem:
        item = self.db.get(ShopItem, sku)
        if item is None:
            raise AppException(404, "商品不存在")
        if payload.name is not None:
            item.name = payload.name
        if payload.description is not None:
            item.description = payload.description
        if payload.price is not None:
            item.price = payload.price
        if payload.is_active is not None:
            item.is_active = payload.is_active
        if payload.preview_asset_url is not None:
            item.preview_asset_url = self._normalize_preview_url(payload.preview_asset_url)
        self.db.commit()
        self.db.refresh(item)
        return self._to_admin_item(item)

    async def upload_preview_image(self, sku: str, content_type: str, content: bytes) -> AdminShopItemListItem:
        if content_type not in ALLOWED_PREVIEW_TYPES:
            raise AppException(400, "仅支持 JPG/PNG/WebP/GIF 图片")
        if len(content) > MAX_PREVIEW_BYTES:
            raise AppException(400, "图片不能超过 2MB")
        item = self.db.get(ShopItem, sku)
        if item is None:
            raise AppException(404, "商品不存在")
        PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
        suffix = ALLOWED_PREVIEW_TYPES[content_type]
        filename = f"{sku}_{uuid.uuid4().hex}{suffix}"
        target = PREVIEW_DIR / filename
        target.write_bytes(content)
        item.preview_asset_url = f"/api/v1/media/pet-shop/{filename}"
        self.db.commit()
        self.db.refresh(item)
        return self._to_admin_item(item)

    def _build_effect_json(self, category: ShopItemCategory, payload: AdminShopItemCreateRequest) -> str | None:
        if category == ShopItemCategory.FOOD:
            exp = payload.effect_exp if payload.effect_exp is not None else 15
            satiety = payload.effect_satiety if payload.effect_satiety is not None else 20
            return json.dumps({"exp": exp, "satiety": satiety})
        if category == ShopItemCategory.DRINK:
            mood = payload.effect_mood if payload.effect_mood is not None else 25
            return json.dumps({"mood": mood, "buff_minutes": 30})
        return None

    def _normalize_preview_url(self, url: str) -> str:
        cleaned = url.strip()
        if not cleaned:
            return ""
        if cleaned.startswith("/api/v1/media/"):
            return cleaned[:255]
        raise AppException(400, "图片地址须为本站上传路径（/api/v1/media/...）")

    def _to_admin_item(self, row: ShopItem) -> AdminShopItemListItem:
        return AdminShopItemListItem(
            sku=row.sku,
            category=row.category.value,
            category_label=category_label(row.category),
            name=row.name,
            description=row.description,
            price=row.price,
            rarity=row.rarity.value if row.rarity else None,
            asset_key=row.asset_key,
            preview_asset_url=row.preview_asset_url or "",
            is_active=row.is_active,
        )

    def get_points_config(self) -> AdminPetPointsConfigResponse:
        config = PetPointsService(self.db)._ensure_config()
        return AdminPetPointsConfigResponse(
            points_launched_at=config.points_launched_at,
            points_per_first_ac=config.points_per_first_ac,
        )

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.pet import ShopItem, ShopItemCategory, ShopItemRarity

DEFAULT_SHOP_ITEMS: list[dict[str, Any]] = [
    {
        "sku": "pet_cat_orange",
        "category": ShopItemCategory.PET,
        "name": "橘小胖",
        "description": "懒洋洋但爱陪你刷题",
        "price": 100,
        "rarity": ShopItemRarity.COMMON,
        "preview_asset_url": "",
        "asset_key": "cat_orange",
        "effect_json": None,
    },
    {
        "sku": "pet_dog_corgi",
        "category": ShopItemCategory.PET,
        "name": "柯基豆",
        "description": "短腿也能跑满积分",
        "price": 100,
        "rarity": ShopItemRarity.COMMON,
        "preview_asset_url": "",
        "asset_key": "dog_corgi",
        "effect_json": None,
    },
    {
        "sku": "pet_robot_pixel",
        "category": ShopItemCategory.PET,
        "name": "像素机",
        "description": "赛博学伴，逻辑满分",
        "price": 120,
        "rarity": ShopItemRarity.COMMON,
        "preview_asset_url": "",
        "asset_key": "robot_pixel",
        "effect_json": None,
    },
    {
        "sku": "pet_dragon_cloud",
        "category": ShopItemCategory.PET,
        "name": "云端幼龙",
        "description": "稀有伙伴，守护你的 AC",
        "price": 280,
        "rarity": ShopItemRarity.RARE,
        "preview_asset_url": "",
        "asset_key": "dragon_cloud",
        "effect_json": None,
    },
    {
        "sku": "food_basic",
        "category": ShopItemCategory.FOOD,
        "name": "普通粮",
        "description": "基础口粮",
        "price": 5,
        "rarity": None,
        "preview_asset_url": "",
        "asset_key": "food_basic",
        "effect_json": json.dumps({"exp": 15, "satiety": 20}),
    },
    {
        "sku": "food_premium",
        "category": ShopItemCategory.FOOD,
        "name": "高级粮",
        "description": "营养满满",
        "price": 15,
        "rarity": None,
        "preview_asset_url": "",
        "asset_key": "food_premium",
        "effect_json": json.dumps({"exp": 40, "satiety": 30}),
    },
    {
        "sku": "drink_juice",
        "category": ShopItemCategory.DRINK,
        "name": "活力果汁",
        "description": "心情 UP",
        "price": 8,
        "rarity": None,
        "preview_asset_url": "",
        "asset_key": "drink_juice",
        "effect_json": json.dumps({"mood": 25, "buff_minutes": 30}),
    },
]


def ensure_shop_catalog(db: Session) -> None:
    existing = db.query(ShopItem.sku).limit(1).first()
    if existing is not None:
        return
    for row in DEFAULT_SHOP_ITEMS:
        db.add(ShopItem(**row, is_active=True))
    db.commit()

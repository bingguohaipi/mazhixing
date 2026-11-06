from app.models.pet import ShopItemCategory

CATEGORY_ZH: dict[ShopItemCategory, str] = {
    ShopItemCategory.PET: "宠物",
    ShopItemCategory.FOOD: "食物",
    ShopItemCategory.DRINK: "饮料",
}

CATEGORY_ZH_TO_ENUM: dict[str, ShopItemCategory] = {v: k for k, v in CATEGORY_ZH.items()}


def category_label(category: ShopItemCategory) -> str:
    return CATEGORY_ZH.get(category, category.value)

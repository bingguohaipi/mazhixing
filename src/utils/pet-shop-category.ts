import type { ShopItemCategory } from '@/types/pet'

export const SHOP_CATEGORY_LABEL: Record<ShopItemCategory, string> = {
  pet: '宠物',
  food: '食物',
  drink: '饮料',
}

export function shopCategoryLabel(category: ShopItemCategory | string): string {
  if (category === 'pet' || category === 'food' || category === 'drink') {
    return SHOP_CATEGORY_LABEL[category]
  }
  return String(category)
}

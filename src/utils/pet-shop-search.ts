import type { AdminShopItem } from '@/api/admin-pet'
import { shopCategoryLabel } from '@/utils/pet-shop-category'

/** 管理端宠物商城本地模糊匹配（不依赖后端 keyword 参数） */
export function matchPetShopItemKeyword(row: AdminShopItem, rawKeyword: string): boolean {
  const q = rawKeyword.trim().toLowerCase()
  if (!q) return true
  const typeZh = shopCategoryLabel(row.category)
  const haystack = [
    row.sku,
    row.name,
    row.description,
    row.asset_key,
    row.category,
    typeZh,
    String(row.price),
  ]
    .join(' ')
    .toLowerCase()
  return haystack.includes(q)
}

export type ShopItemCategory = 'pet' | 'food' | 'drink'
export type PetStateHint = 'idle' | 'sleep' | 'happy'
export type PetPlayReaction = 'jump' | 'happy' | 'wiggle'

export interface StudentPointsSummary {
  balance: number
  total_earned: number
  total_spent: number
  first_ac_count: number
}

export interface PointLedgerItem {
  id: number
  type: 'EARN_FIRST_AC' | 'SPEND_SHOP' | 'ADMIN_ADJUST'
  delta: number
  balance_after: number
  ref_type: string | null
  ref_id: number | null
  ref_title: string | null
  created_at: string
}

export interface PointLedgerListResponse {
  items: PointLedgerItem[]
  total: number
  page: number
  page_size: number
}

export interface PetShopCatalogItem {
  sku: string
  category: ShopItemCategory
  name: string
  description: string
  price: number
  rarity: 'common' | 'rare' | null
  preview_asset_url: string
  lottie_url: string | null
  effect_summary: string | null
  owned: boolean
  can_afford: boolean
}

export interface PetShopCatalogResponse {
  balance: number
  items: PetShopCatalogItem[]
}

export interface StudentPetListItem {
  id: number
  catalog_sku: string
  name: string
  level: number
  exp: number
  exp_to_next: number
  satiety: number
  mood: number
  is_active: boolean
  asset_key: string
}

export interface StudentPetActive extends StudentPetListItem {
  state_hint: PetStateHint
  buffs: { type: 'drink_mood'; expires_at: string }[]
  last_sync_at: string
}

export interface PetPlayResponse {
  pet: StudentPetActive
  reaction: PetPlayReaction
  mood_delta: number
}

export interface InventoryItem {
  sku: string
  name: string
  category: ShopItemCategory
  quantity: number
}

export interface StudentPetSettings {
  desktop_pet_enabled: boolean
  silent_while_coding: boolean
}

export const PET_EMOJI: Record<string, string> = {
  cat_orange: '🐱',
  dog_corgi: '🐶',
  robot_pixel: '🤖',
  dragon_cloud: '🐉',
  food_basic: '🍙',
  food_premium: '🍖',
  drink_juice: '🧃',
  pet_cat_orange: '🐱',
  pet_dog_corgi: '🐶',
  pet_robot_pixel: '🤖',
  pet_dragon_cloud: '🐉',
}

export function petEmojiForAssetKey(assetKey: string): string {
  return PET_EMOJI[assetKey] ?? '🐾'
}

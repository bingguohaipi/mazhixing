import apiClient, { unwrapApi } from './client'
import type { ApiResponse } from '@/types/auth'
import type { ShopItemCategory } from '@/types/pet'

export interface AdminShopItem {
  sku: string
  category: ShopItemCategory
  category_label?: string
  name: string
  description: string
  price: number
  rarity: 'common' | 'rare' | null
  asset_key: string
  preview_asset_url: string
  is_active: boolean
}

export interface AdminPetPointsConfig {
  points_launched_at: string | null
  points_per_first_ac: number
}

export interface AdminShopItemCreatePayload {
  sku: string
  category: ShopItemCategory
  name: string
  description?: string
  price: number
  asset_key: string
  rarity?: 'common' | 'rare' | null
  effect_exp?: number
  effect_satiety?: number
  effect_mood?: number
  is_active?: boolean
}

export const adminPetApi = {
  async listItems(keyword?: string): Promise<AdminShopItem[]> {
    const res = await apiClient.get<ApiResponse<{ items: AdminShopItem[] }>>('/admin/pet-shop/items', {
      params: keyword?.trim() ? { keyword: keyword.trim() } : undefined,
    })
    return unwrapApi(res).items
  },

  async createItem(payload: AdminShopItemCreatePayload): Promise<AdminShopItem> {
    const res = await apiClient.post<ApiResponse<AdminShopItem>>('/admin/pet-shop/items', payload)
    return unwrapApi(res)
  },

  async deleteItem(sku: string): Promise<void> {
    const res = await apiClient.delete<ApiResponse<null>>(`/admin/pet-shop/items/${encodeURIComponent(sku)}`)
    unwrapApi(res)
  },

  async patchItem(
    sku: string,
    payload: Partial<Pick<AdminShopItem, 'name' | 'description' | 'price' | 'is_active' | 'preview_asset_url'>>,
  ): Promise<AdminShopItem> {
    const res = await apiClient.patch<ApiResponse<AdminShopItem>>(`/admin/pet-shop/items/${sku}`, payload)
    return unwrapApi(res)
  },

  async uploadPreviewImage(sku: string, file: File): Promise<AdminShopItem> {
    const form = new FormData()
    form.append('file', file)
    const res = await apiClient.post<ApiResponse<AdminShopItem>>(`/admin/pet-shop/items/${sku}/preview-image`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return unwrapApi(res)
  },

  async getPointsConfig(): Promise<AdminPetPointsConfig> {
    const res = await apiClient.get<ApiResponse<AdminPetPointsConfig>>('/admin/pet-points/config')
    return unwrapApi(res)
  },
}

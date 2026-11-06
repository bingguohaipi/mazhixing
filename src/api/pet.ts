import apiClient, { unwrapApi } from './client'
import type { ApiResponse } from '@/types/auth'
import type {
  InventoryItem,
  PetShopCatalogResponse,
  PointLedgerListResponse,
  PetPlayResponse,
  StudentPetActive,
  StudentPetListItem,
  StudentPetSettings,
  StudentPointsSummary,
} from '@/types/pet'

export const petApi = {
  async getPoints(): Promise<StudentPointsSummary> {
    const res = await apiClient.get<ApiResponse<StudentPointsSummary>>('/students/me/points')
    return unwrapApi(res)
  },

  async getPointLedger(page = 1, pageSize = 20, type?: string): Promise<PointLedgerListResponse> {
    const res = await apiClient.get<ApiResponse<PointLedgerListResponse>>('/students/me/points/ledger', {
      params: { page, page_size: pageSize, type },
    })
    return unwrapApi(res)
  },

  async getCatalog(category?: string): Promise<PetShopCatalogResponse> {
    const res = await apiClient.get<ApiResponse<PetShopCatalogResponse>>('/students/me/pet-shop/catalog', {
      params: category ? { category } : {},
    })
    return unwrapApi(res)
  },

  async purchase(sku: string, quantity = 1): Promise<{ balance: number }> {
    const res = await apiClient.post<ApiResponse<{ balance: number; spent: number }>>('/students/me/pet-shop/orders', {
      sku,
      quantity,
    })
    return unwrapApi(res)
  },

  async listPets(): Promise<StudentPetListItem[]> {
    const res = await apiClient.get<ApiResponse<{ items: StudentPetListItem[] }>>('/students/me/pets')
    return unwrapApi(res).items
  },

  async getActivePet(): Promise<StudentPetActive | null> {
    const res = await apiClient.get<ApiResponse<StudentPetActive | null>>('/students/me/pets/active')
    return unwrapApi(res)
  },

  async syncPet(): Promise<StudentPetActive | null> {
    const res = await apiClient.post<ApiResponse<StudentPetActive | null>>('/students/me/pets/sync', {})
    return unwrapApi(res)
  },

  async playWithActivePet(): Promise<PetPlayResponse> {
    const res = await apiClient.post<ApiResponse<PetPlayResponse>>('/students/me/pets/active/play')
    return unwrapApi(res)
  },

  async activatePet(petId: number): Promise<StudentPetActive> {
    const res = await apiClient.post<ApiResponse<StudentPetActive>>(`/students/me/pets/${petId}/activate`)
    return unwrapApi(res)
  },

  async getInventory(): Promise<InventoryItem[]> {
    const res = await apiClient.get<ApiResponse<{ items: InventoryItem[] }>>('/students/me/inventory')
    return unwrapApi(res).items
  },

  async useItem(sku: string, quantity = 1) {
    const res = await apiClient.post<ApiResponse<unknown>>('/students/me/inventory/use', { sku, quantity })
    return unwrapApi(res)
  },

  async getSettings(): Promise<StudentPetSettings> {
    const res = await apiClient.get<ApiResponse<StudentPetSettings>>('/students/me/pet-settings')
    return unwrapApi(res)
  },

  async patchSettings(payload: Partial<StudentPetSettings>): Promise<StudentPetSettings> {
    const res = await apiClient.patch<ApiResponse<StudentPetSettings>>('/students/me/pet-settings', payload)
    return unwrapApi(res)
  },
}

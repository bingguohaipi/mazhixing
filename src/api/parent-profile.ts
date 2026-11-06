import apiClient, { unwrapApi } from './client'
import type { ApiResponse } from '@/types/auth'
import type { ParentProfile } from '@/types/role-profile'

export const parentProfileApi = {
  async getProfile(): Promise<ParentProfile> {
    const res = await apiClient.get<ApiResponse<ParentProfile>>('/parents/me/profile')
    return unwrapApi(res)
  },

  async updateNickname(nickname: string): Promise<ParentProfile> {
    const res = await apiClient.patch<ApiResponse<ParentProfile>>('/parents/me/nickname', { nickname })
    return unwrapApi(res)
  },
}

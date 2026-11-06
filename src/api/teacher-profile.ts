import apiClient, { unwrapApi } from './client'
import type { ApiResponse } from '@/types/auth'
import type { TeacherProfile } from '@/types/role-profile'

export const teacherProfileApi = {
  async getProfile(): Promise<TeacherProfile> {
    const res = await apiClient.get<ApiResponse<TeacherProfile>>('/teachers/me/profile')
    return unwrapApi(res)
  },

  async updateNickname(nickname: string): Promise<TeacherProfile> {
    const res = await apiClient.patch<ApiResponse<TeacherProfile>>('/teachers/me/nickname', { nickname })
    return unwrapApi(res)
  },
}

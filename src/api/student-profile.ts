import apiClient, { unwrapApi } from './client'
import type { ApiResponse } from '@/types/auth'
import type { StudentProfile } from '@/types/student-profile'

export const studentProfileApi = {
  async getProfile(): Promise<StudentProfile> {
    const res = await apiClient.get<ApiResponse<StudentProfile>>('/students/me/profile')
    return unwrapApi(res)
  },

  async updateNickname(nickname: string): Promise<StudentProfile> {
    const res = await apiClient.patch<ApiResponse<StudentProfile>>('/students/me/nickname', { nickname })
    return unwrapApi(res)
  },

  async uploadAvatar(file: File): Promise<StudentProfile> {
    const form = new FormData()
    form.append('file', file)
    const res = await apiClient.post<ApiResponse<StudentProfile>>('/students/me/avatar', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return unwrapApi(res)
  },
}

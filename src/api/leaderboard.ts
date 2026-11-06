import apiClient, { unwrapApi } from '@/api/client'
import type { LeaderboardResponse } from '@/types/leaderboard'

export const leaderboardApi = {
  getMyClass: async (classId?: number): Promise<LeaderboardResponse> => {
    const response = await apiClient.get('/practice/leaderboard', {
      params: classId ? { class_id: classId } : undefined,
    })
    return unwrapApi(response)
  },

  getClassForTeacher: async (classId: number): Promise<LeaderboardResponse> => {
    const response = await apiClient.get(`/analytics/class/${classId}/leaderboard`)
    return unwrapApi(response)
  },
}

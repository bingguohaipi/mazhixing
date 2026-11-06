import apiClient, { unwrapApi } from '@/api/client'
import type { StudentDashboardOverview } from '@/types/student-dashboard'

export const studentDashboardApi = {
  getOverview: async (): Promise<StudentDashboardOverview> => {
    const response = await apiClient.get('/practice/dashboard')
    return unwrapApi(response)
  },
}

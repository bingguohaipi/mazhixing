import apiClient, { unwrapApi } from './client'
import type {
  ParentChildBrief,
  ParentPeriod,
  ParentStudentOverview,
  ParentWrongBookListResponse,
  WrongReviewStatus,
  WrongSortBy,
} from '@/types/parent'

export const parentApi = {
  listChildren: async (): Promise<ParentChildBrief[]> => {
    const response = await apiClient.get('/parent/children')
    return unwrapApi(response)
  },

  getOverview: async (studentId: number, period: ParentPeriod = '7'): Promise<ParentStudentOverview> => {
    const response = await apiClient.get(`/parent/children/${studentId}/overview`, {
      params: { period },
    })
    return unwrapApi(response)
  },

  getWrongBook: async (
    studentId: number,
    options?: {
      reviewStatus?: WrongReviewStatus
      knowledgePoint?: string
      sortBy?: WrongSortBy
    },
  ): Promise<ParentWrongBookListResponse> => {
    const response = await apiClient.get(`/parent/children/${studentId}/wrong-book`, {
      params: {
        review_status: options?.reviewStatus,
        knowledge_point: options?.knowledgePoint,
        sort_by: options?.sortBy ?? 'error_count',
      },
    })
    return unwrapApi(response)
  },
}

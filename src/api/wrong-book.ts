import apiClient, { unwrapApi } from '@/api/client'
import type {
  WrongBookListResponse,
  WrongReviewStatus,
  WrongSortBy,
} from '@/types/wrong-book'

export const wrongBookApi = {
  list: async (params?: {
    review_status?: WrongReviewStatus | ''
    knowledge_point?: string
    sort_by?: WrongSortBy
  }): Promise<WrongBookListResponse> => {
    const response = await apiClient.get('/practice/wrong-book', {
      params: {
        review_status: params?.review_status || undefined,
        knowledge_point: params?.knowledge_point || undefined,
        sort_by: params?.sort_by || 'error_count',
      },
    })
    return unwrapApi(response)
  },

  clear: async (problemId?: number): Promise<number> => {
    const response = await apiClient.post('/practice/wrong-book/clear', {
      problem_id: problemId ?? null,
    })
    const data = unwrapApi<{ cleared_count: number }>(response)
    return data.cleared_count
  },
}

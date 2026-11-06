import apiClient, { unwrapApi } from '@/api/client'
import type {
  KnowledgePointDetailResponse,
  KnowledgePointListResponse,
  KnowledgePointOptionItem,
  PracticeProblemDetail,
  PracticeProblemListResponse,
  StudentHomeworkDetail,
} from '@/types/practice'

export const practiceApi = {
  async listKnowledgePointOptions(search?: string): Promise<KnowledgePointOptionItem[]> {
    const response = await apiClient.get('/practice/knowledge-point-options', {
      params: search?.trim() ? { search: search.trim() } : undefined,
    })
    return unwrapApi(response)
  },

  async listKnowledgePoints(): Promise<KnowledgePointListResponse> {
    const response = await apiClient.get('/practice/knowledge-points')
    return unwrapApi(response)
  },

  async getKnowledgePoint(name: string): Promise<KnowledgePointDetailResponse> {
    const response = await apiClient.get(
      `/practice/knowledge-points/${encodeURIComponent(name)}`,
    )
    return unwrapApi(response)
  },

  async listProblems(params?: {
    page?: number
    page_size?: number
    keyword?: string
    difficulty?: string
    knowledge_point?: string
    sort_by?: 'id' | 'difficulty'
    sort_order?: 'asc' | 'desc'
    language?: string
  }): Promise<PracticeProblemListResponse> {
    const response = await apiClient.get('/practice/problems', { params })
    return unwrapApi(response)
  },

  async getProblem(problemId: number): Promise<PracticeProblemDetail> {
    const response = await apiClient.get(`/practice/problems/${problemId}`)
    return unwrapApi(response)
  },

  async getHomeworkDetail(homeworkId: number): Promise<StudentHomeworkDetail> {
    const response = await apiClient.get(`/homework/my/${homeworkId}`)
    return unwrapApi(response)
  },
}

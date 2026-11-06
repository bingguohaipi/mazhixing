import apiClient, { unwrapApi } from '@/api/client'
import type { ApiResponse } from '@/types/auth'
import type {
  ProblemAcSolverItem,
  ProblemCreatePayload,
  ProblemDetail,
  ProblemImportResult,
  ProblemListResponse,
  ProblemQuery,
  ProblemUpdatePayload,
} from '@/types/problem'

export const problemApi = {
  async list(query: ProblemQuery = {}): Promise<ProblemListResponse> {
    const params: Record<string, string | number> = {
      page: query.page ?? 1,
      page_size: query.page_size ?? 20,
    }
    if (query.keyword) params.keyword = query.keyword
    if (query.language) params.language = query.language
    if (query.difficulty) params.difficulty = query.difficulty
    if (query.gesp_level) params.gesp_level = query.gesp_level
    if (query.knowledge_point) params.knowledge_point = query.knowledge_point
    if (query.my_passed) params.my_passed = 'true'

    const res = await apiClient.get<ApiResponse<ProblemListResponse>>('/problems', { params })
    return unwrapApi(res)
  },

  async listCustom(query: ProblemQuery = {}): Promise<ProblemListResponse> {
    const params: Record<string, string | number> = {
      page: query.page ?? 1,
      page_size: query.page_size ?? 100,
    }
    if (query.keyword) params.keyword = query.keyword
    if (query.language) params.language = query.language
    if (query.difficulty) params.difficulty = query.difficulty
    if (query.gesp_level) params.gesp_level = query.gesp_level
    if (query.knowledge_point) params.knowledge_point = query.knowledge_point
    if (query.sort_by) params.sort_by = query.sort_by
    if (query.sort_order) params.sort_order = query.sort_order
    if (query.my_passed) params.my_passed = 'true'
    const res = await apiClient.get<ApiResponse<ProblemListResponse>>('/problems/custom', { params })
    return unwrapApi(res)
  },

  async listPublicCatalog(query: ProblemQuery = {}): Promise<ProblemListResponse> {
    const params: Record<string, string | number> = {
      page: query.page ?? 1,
      page_size: query.page_size ?? 100,
    }
    if (query.keyword) params.keyword = query.keyword
    if (query.difficulty) params.difficulty = query.difficulty
    if (query.language) params.language = query.language
    if (query.gesp_level) params.gesp_level = query.gesp_level
    if (query.knowledge_point) params.knowledge_point = query.knowledge_point
    if (query.sort_by) params.sort_by = query.sort_by
    if (query.sort_order) params.sort_order = query.sort_order
    if (query.my_passed) params.my_passed = 'true'
    const res = await apiClient.get<ApiResponse<ProblemListResponse>>('/problems/public/catalog', { params })
    return unwrapApi(res)
  },

  async getPublic(problemId: number): Promise<ProblemDetail> {
    const res = await apiClient.get<ApiResponse<ProblemDetail>>(`/problems/public/${problemId}`)
    return unwrapApi(res)
  },

  async listAcSolvers(problemId: number): Promise<ProblemAcSolverItem[]> {
    const res = await apiClient.get<ApiResponse<{ items: ProblemAcSolverItem[]; total: number }>>(
      `/problems/public/${problemId}/ac-solvers`,
    )
    return unwrapApi(res).items
  },

  async get(problemId: number): Promise<ProblemDetail> {
    const res = await apiClient.get<ApiResponse<ProblemDetail>>(`/problems/${problemId}`)
    return unwrapApi(res)
  },

  async create(payload: ProblemCreatePayload): Promise<ProblemDetail> {
    const res = await apiClient.post<ApiResponse<ProblemDetail>>('/problems', payload)
    return unwrapApi(res)
  },

  async update(problemId: number, payload: ProblemUpdatePayload): Promise<ProblemDetail> {
    const res = await apiClient.put<ApiResponse<ProblemDetail>>(`/problems/${problemId}`, payload)
    return unwrapApi(res)
  },

  async remove(problemId: number): Promise<void> {
    const res = await apiClient.delete<ApiResponse<null>>(`/problems/${problemId}`)
    unwrapApi(res)
  },

  async importProblems(problems: ProblemCreatePayload[]): Promise<ProblemImportResult> {
    const res = await apiClient.post<ApiResponse<ProblemImportResult>>('/problems/import', { problems })
    return unwrapApi(res)
  },

  async exportLessonPack(problemIds: number[]): Promise<Blob> {
    const res = await apiClient.get('/problems/lesson-pack/export', {
      params: { ids: problemIds },
      responseType: 'blob',
      paramsSerializer: (params) => {
        const search = new URLSearchParams()
        for (const id of params.ids as number[]) {
          search.append('ids', String(id))
        }
        return search.toString()
      },
    })
    return res.data as Blob
  },
}

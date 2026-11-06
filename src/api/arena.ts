import apiClient, { unwrapApi } from './client'
import type { ApiResponse } from '@/types/auth'
import type {
  ArenaBoardResponse,
  ArenaGlobalLeaderboardResponse,
  ArenaNotificationItem,
  ArenaOverviewResponse,
  ArenaProblemListResponse,
  ArenaSessionBrief,
  ArenaSubmitResponse,
} from '@/types/arena'
import { submissionApi } from '@/api/submission'
import type { ArenaLanguage } from '@/utils/arena-language'

export const arenaApi = {
  async agreeTerms(): Promise<void> {
    await apiClient.post<ApiResponse<null>>('/practice/arena/agreement')
  },

  async getOverview(): Promise<ArenaOverviewResponse> {
    const res = await apiClient.get<ApiResponse<ArenaOverviewResponse>>('/practice/arena/overview')
    return unwrapApi(res)
  },

  async listProblems(params: {
    language?: ArenaLanguage
    page?: number
    page_size?: number
    keyword?: string
    difficulty?: string
  }): Promise<ArenaProblemListResponse> {
    const res = await apiClient.get<ApiResponse<ArenaProblemListResponse>>('/practice/arena/problems', {
      params: {
        language: params.language || undefined,
        page: params.page ?? 1,
        page_size: params.page_size ?? 50,
        keyword: params.keyword || undefined,
        difficulty: params.difficulty || undefined,
      },
    })
    return unwrapApi(res)
  },

  async getGlobalLeaderboard(language: ArenaLanguage): Promise<ArenaGlobalLeaderboardResponse> {
    const res = await apiClient.get<ApiResponse<ArenaGlobalLeaderboardResponse>>(
      '/practice/arena/leaderboard',
      { params: { language } },
    )
    return unwrapApi(res)
  },

  async getBoard(problemId: number, language: string): Promise<ArenaBoardResponse> {
    const res = await apiClient.get<ApiResponse<ArenaBoardResponse>>(
      `/practice/arena/problems/${problemId}/board`,
      { params: { language } },
    )
    return unwrapApi(res)
  },

  async createSession(problemId: number, language: 'Python' | 'C++'): Promise<ArenaSessionBrief> {
    const res = await apiClient.post<ApiResponse<ArenaSessionBrief>>('/practice/arena/sessions', {
      problem_id: problemId,
      language,
    })
    return unwrapApi(res)
  },

  async exitSession(sessionId: number): Promise<void> {
    await apiClient.post(`/practice/arena/sessions/${sessionId}/exit`)
  },

  async patchMetrics(
    sessionId: number,
    metrics: { paste_count: number; paste_char_count: number },
  ): Promise<void> {
    await apiClient.patch(`/practice/arena/sessions/${sessionId}/metrics`, metrics)
  },

  async submitSession(sessionId: number, code: string): Promise<ArenaSubmitResponse> {
    const res = await apiClient.post<ApiResponse<ArenaSubmitResponse>>(
      `/practice/arena/sessions/${sessionId}/submit`,
      { code },
      { timeout: 30000 },
    )
    const data = unwrapApi(res)
    if (data.status === 'PENDING') {
      const detail = await submissionApi.poll(data.submission_id)
      return { ...data, status: detail.status }
    }
    return data
  },

  async listNotifications(page = 1): Promise<{ items: ArenaNotificationItem[]; total: number }> {
    const res = await apiClient.get<ApiResponse<{ items: ArenaNotificationItem[]; total: number; page: number; page_size: number }>>(
      '/practice/arena/notifications',
      { params: { page, page_size: 20 } },
    )
    const data = unwrapApi(res)
    return { items: data.items, total: data.total }
  },

  async markNotificationsRead(all = false, ids?: number[]): Promise<void> {
    await apiClient.post('/practice/arena/notifications/read', { all, ids: ids ?? null })
  },
}

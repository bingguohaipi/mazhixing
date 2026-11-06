import apiClient, { unwrapApi } from './client'
import type {
  AnalyticsPeriod,
  ClassAnalytics,
  ClassProblemWrongCodesResponse,
  ClassWrongSummary,
  SubmissionTrendRange,
  SubmissionTrendResponse,
  TeacherDashboardOverview,
} from '@/types/analytics'

export const analyticsApi = {
  getDashboard: async (): Promise<TeacherDashboardOverview> => {
    const response = await apiClient.get('/analytics/dashboard')
    return unwrapApi(response)
  },

  getSubmissionTrend: async (
    classId: number,
    trendRange: SubmissionTrendRange = '7d',
    homeworkId?: number,
  ): Promise<SubmissionTrendResponse> => {
    const response = await apiClient.get(`/analytics/class/${classId}/submission-trend`, {
      params: { trend_range: trendRange, homework_id: homeworkId },
    })
    return unwrapApi(response)
  },

  getClassAnalytics: async (
    classId: number,
    period: AnalyticsPeriod = 'week',
    homeworkId?: number,
  ): Promise<ClassAnalytics> => {
    const response = await apiClient.get(`/analytics/class/${classId}`, {
      params: { period, homework_id: homeworkId },
    })
    return unwrapApi(response)
  },

  exportReport: async (
    classId?: number,
    period: AnalyticsPeriod = 'week',
    homeworkId?: number,
  ): Promise<Blob> => {
    const response = await apiClient.get('/analytics/export', {
      params: { class_id: classId, period, homework_id: homeworkId },
      responseType: 'blob',
    })
    return response.data as Blob
  },

  getClassWrongSummary: async (
    classId: number,
    period: AnalyticsPeriod = 'week',
    homeworkId?: number,
    knowledgePoint?: string,
  ): Promise<ClassWrongSummary> => {
    const response = await apiClient.get(`/analytics/class/${classId}/wrong-summary`, {
      params: {
        period,
        homework_id: homeworkId,
        knowledge_point: knowledgePoint || undefined,
      },
    })
    return unwrapApi(response)
  },

  getClassProblemWrongCodes: async (
    classId: number,
    problemId: number,
    period: AnalyticsPeriod = 'week',
    homeworkId?: number,
  ): Promise<ClassProblemWrongCodesResponse> => {
    const response = await apiClient.get(
      `/analytics/class/${classId}/problems/${problemId}/wrong-codes`,
      { params: { period, homework_id: homeworkId } },
    )
    return unwrapApi(response)
  },

  exportWrongSummary: async (
    classId: number,
    period: AnalyticsPeriod = 'week',
    homeworkId?: number,
    knowledgePoint?: string,
  ): Promise<Blob> => {
    const response = await apiClient.get(`/analytics/class/${classId}/wrong-summary/export`, {
      params: {
        period,
        homework_id: homeworkId,
        knowledge_point: knowledgePoint || undefined,
      },
      responseType: 'blob',
    })
    return response.data as Blob
  },
}

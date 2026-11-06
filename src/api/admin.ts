import apiClient, { unwrapApi } from './client'
import type { ApiResponse } from '@/types/auth'
import type {
  ProblemCreatePayload,
  ProblemDetail,
  ProblemImportResult,
  ProblemListResponse,
} from '@/types/problem'
import type {
  AdminParentBindingItem,
  AdminUserCreatePayload,
  AdminUserListItem,
  AdminUserListResponse,
  AdminUserRelationsResponse,
  AdminUserUpdatePayload,
  EventSummaryResponse,
  PublicProblemListResponse,
} from '@/types/admin'
import type { SuggestionListResponse } from '@/types/suggestion'
import type {
  AdminKnowledgePointCreatePayload,
  AdminKnowledgePointItem,
  AdminKnowledgePointListResponse,
  AdminKnowledgePointUpdatePayload,
} from '@/types/knowledge-admin'

export const adminApi = {
  listUsers(params: { role?: string; keyword?: string; page?: number; page_size?: number }) {
    return apiClient
      .get<ApiResponse<AdminUserListResponse>>('/admin/users', { params })
      .then((res) => unwrapApi(res))
  },
  createUser(payload: AdminUserCreatePayload) {
    return apiClient
      .post<ApiResponse<AdminUserListItem>>('/admin/users', payload)
      .then((res) => unwrapApi(res))
  },
  updateUser(userId: number, payload: AdminUserUpdatePayload) {
    return apiClient
      .patch<ApiResponse<AdminUserListItem>>(`/admin/users/${userId}`, payload)
      .then((res) => unwrapApi(res))
  },
  getUserRelations(userId: number): Promise<AdminUserRelationsResponse> {
    return apiClient
      .get<ApiResponse<AdminUserRelationsResponse>>(`/admin/users/${userId}/relations`)
      .then((res) => unwrapApi(res))
  },
  bindParentStudent(parentId: number, studentId: number): Promise<AdminParentBindingItem> {
    return apiClient
      .post<ApiResponse<AdminParentBindingItem>>('/admin/bindings/parent-student', {
        parent_id: parentId,
        student_id: studentId,
      })
      .then((res) => unwrapApi(res))
  },
  unbindParentStudent(bindingId: number): Promise<void> {
    return apiClient.delete(`/admin/bindings/parent-student/${bindingId}`).then((res) => unwrapApi(res))
  },
  rebindParentStudent(bindingId: number, newParentId: number): Promise<AdminParentBindingItem> {
    return apiClient
      .put<ApiResponse<AdminParentBindingItem>>(`/admin/bindings/parent-student/${bindingId}/rebind`, {
        new_parent_id: newParentId,
      })
      .then((res) => unwrapApi(res))
  },
  setStudentTeacher(studentId: number, teacherId: number | null): Promise<AdminUserRelationsResponse> {
    return apiClient
      .put<ApiResponse<AdminUserRelationsResponse>>(`/admin/users/${studentId}/teacher`, {
        teacher_id: teacherId,
      })
      .then((res) => unwrapApi(res))
  },
  listPublicProblems(params: {
    page?: number
    page_size?: number
    status?: string
    keyword?: string
    difficulty?: string
  }) {
    return apiClient
      .get<ApiResponse<PublicProblemListResponse>>('/admin/public-problems', { params })
      .then((res) => unwrapApi(res))
  },
  getPublicProblem(id: number) {
    return apiClient.get<ApiResponse<ProblemDetail>>(`/admin/public-problems/${id}`).then((res) => unwrapApi(res))
  },
  createPublicProblem(payload: ProblemCreatePayload) {
    return apiClient.post<ApiResponse<ProblemDetail>>('/admin/public-problems', payload).then((res) => unwrapApi(res))
  },
  importPublicProblems(problems: ProblemCreatePayload[]) {
    return apiClient
      .post<ApiResponse<ProblemImportResult>>('/admin/public-problems/import', { problems })
      .then((res) => unwrapApi(res))
  },
  updatePublicProblem(id: number, payload: Partial<ProblemCreatePayload>) {
    return apiClient.put<ApiResponse<ProblemDetail>>(`/admin/public-problems/${id}`, payload).then((res) => unwrapApi(res))
  },
  publishPublicProblem(id: number) {
    return apiClient.post<ApiResponse<ProblemDetail>>(`/admin/public-problems/${id}/publish`).then((res) => unwrapApi(res))
  },
  archivePublicProblem(id: number) {
    return apiClient.post<ApiResponse<ProblemDetail>>(`/admin/public-problems/${id}/archive`).then((res) => unwrapApi(res))
  },
  newVersionPublicProblem(id: number) {
    return apiClient
      .post<ApiResponse<ProblemDetail>>(`/admin/public-problems/${id}/new-version`)
      .then((res) => unwrapApi(res))
  },
  deletePublicProblemVersion(id: number) {
    return apiClient
      .post<ApiResponse<null>>(`/admin/public-problems/${id}/delete`)
      .then((res) => unwrapApi(res))
  },
  setPublicProblemArena(id: number, arena_enabled: boolean) {
    return apiClient
      .patch<ApiResponse<null>>(`/admin/public-problems/${id}/arena`, { arena_enabled })
      .then((res) => unwrapApi(res))
  },
  listAllSuggestions(params: {
    page?: number
    page_size?: number
    status?: string
    sender?: string
    processed?: boolean
  }): Promise<SuggestionListResponse> {
    return apiClient.get('/suggestions/admin/all', { params }).then((res) => unwrapApi(res) as SuggestionListResponse)
  },
  getEventsSummary(days = 7): Promise<EventSummaryResponse> {
    return apiClient
      .get<ApiResponse<EventSummaryResponse>>('/admin/events/summary', { params: { days } })
      .then((res) => unwrapApi(res))
  },
  listKnowledgePoints(params?: {
    keyword?: string
    sort_by?: 'sort_order' | 'problem_count'
    sort_order?: 'asc' | 'desc'
  }): Promise<AdminKnowledgePointListResponse> {
    return apiClient
      .get<ApiResponse<AdminKnowledgePointListResponse>>('/admin/knowledge-points', { params })
      .then((res) => unwrapApi(res))
  },
  createKnowledgePoint(payload: AdminKnowledgePointCreatePayload): Promise<AdminKnowledgePointItem> {
    return apiClient
      .post<ApiResponse<AdminKnowledgePointItem>>('/admin/knowledge-points', payload)
      .then((res) => unwrapApi(res))
  },
  updateKnowledgePoint(
    id: number,
    payload: AdminKnowledgePointUpdatePayload,
  ): Promise<AdminKnowledgePointItem> {
    return apiClient
      .patch<ApiResponse<AdminKnowledgePointItem>>(`/admin/knowledge-points/${id}`, payload)
      .then((res) => unwrapApi(res))
  },
  deleteKnowledgePoint(id: number): Promise<void> {
    return apiClient.delete(`/admin/knowledge-points/${id}`).then((res) => unwrapApi(res))
  },
}

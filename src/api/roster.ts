import apiClient, { unwrapApi } from '@/api/client'
import type { ApiResponse } from '@/types/auth'
import type {
  RosterBatchCreateResponse,
  RosterListResponse,
  RosterStudentItem,
  RosterStudentUpdatePayload,
} from '@/types/roster'

export const rosterApi = {
  async list(keyword?: string, classId?: number | null): Promise<RosterListResponse> {
    const params: Record<string, string | number> = {}
    if (keyword) params.keyword = keyword
    if (classId != null && classId > 0) params.class_id = classId
    const res = await apiClient.get<ApiResponse<RosterListResponse>>('/teacher/roster', {
      params: Object.keys(params).length ? params : undefined,
    })
    return unwrapApi(res)
  },

  async update(studentId: number, payload: RosterStudentUpdatePayload): Promise<RosterStudentItem> {
    const res = await apiClient.put<ApiResponse<RosterStudentItem>>(
      `/teacher/roster/${studentId}`,
      payload,
    )
    return unwrapApi(res)
  },

  async batchCreate(names: string[], year: number): Promise<RosterBatchCreateResponse> {
    const res = await apiClient.post<ApiResponse<RosterBatchCreateResponse>>('/teacher/roster/batch', {
      names,
      year,
    })
    return unwrapApi(res)
  },
}

import apiClient, { unwrapApi } from '@/api/client'
import type { ApiResponse } from '@/types/auth'
import type {
  HomeworkCreatePayload,
  HomeworkDetail,
  HomeworkListItem,
  HomeworkSubmissionReport,
  HomeworkUpdatePayload,
  StudentHomeworkItem,
  TeacherSubmissionDetail,
} from '@/types/homework'

export const homeworkApi = {
  async list(status?: string): Promise<HomeworkListItem[]> {
    const res = await apiClient.get<ApiResponse<HomeworkListItem[]>>('/homework', {
      params: status && status !== 'all' ? { status } : undefined,
    })
    return unwrapApi(res)
  },

  async get(homeworkId: number): Promise<HomeworkDetail> {
    const res = await apiClient.get<ApiResponse<HomeworkDetail>>(`/homework/${homeworkId}`)
    return unwrapApi(res)
  },

  async getSubmissionReport(homeworkId: number): Promise<HomeworkSubmissionReport> {
    const res = await apiClient.get<ApiResponse<HomeworkSubmissionReport>>(
      `/homework/${homeworkId}/submission-report`,
    )
    return unwrapApi(res)
  },

  async getSubmissionForTeacher(
    homeworkId: number,
    submissionId: number,
  ): Promise<TeacherSubmissionDetail> {
    const res = await apiClient.get<ApiResponse<TeacherSubmissionDetail>>(
      `/homework/${homeworkId}/submissions/${submissionId}`,
    )
    return unwrapApi(res)
  },

  async create(payload: HomeworkCreatePayload): Promise<{ data: HomeworkDetail; message: string }> {
    const res = await apiClient.post<ApiResponse<HomeworkDetail>>('/homework', payload)
    return { data: unwrapApi(res), message: res.data.message }
  },

  async update(
    homeworkId: number,
    payload: HomeworkUpdatePayload,
  ): Promise<{ data: HomeworkDetail; message: string }> {
    const res = await apiClient.put<ApiResponse<HomeworkDetail>>(`/homework/${homeworkId}`, payload)
    return { data: unwrapApi(res), message: res.data.message }
  },

  async delete(homeworkId: number): Promise<string> {
    const res = await apiClient.delete<ApiResponse<null>>(`/homework/${homeworkId}`)
    return res.data.message
  },

  async withdraw(homeworkId: number): Promise<HomeworkDetail> {
    const res = await apiClient.post<ApiResponse<HomeworkDetail>>(`/homework/${homeworkId}/withdraw`)
    return unwrapApi(res)
  },

  async setAllowLate(
    homeworkId: number,
    allow: boolean,
  ): Promise<{ data: HomeworkDetail; message: string }> {
    const res = await apiClient.patch<ApiResponse<HomeworkDetail>>(`/homework/${homeworkId}/allow-late`, {
      allow_late_submission: allow,
    })
    return { data: unwrapApi(res), message: res.data.message }
  },

  async listMy(): Promise<StudentHomeworkItem[]> {
    const res = await apiClient.get<ApiResponse<StudentHomeworkItem[]>>('/homework/my')
    return unwrapApi(res)
  },

  async ackUpdate(homeworkId: number): Promise<void> {
    const res = await apiClient.post<ApiResponse<null>>(`/homework/my/${homeworkId}/ack-update`)
    unwrapApi(res)
  },
}

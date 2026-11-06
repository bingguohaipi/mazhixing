import apiClient, { unwrapApi } from '@/api/client'
import type { ApiResponse } from '@/types/auth'
import type {
  BindParentPayload,
  BindParentResponse,
  ClassCreatePayload,
  ClassDetail,
  ClassListItem,
  ClassStudentItem,
  ClassUpdatePayload,
  ParentBindingItem,
  StudentCreatePayload,
  StudentCreateResponse,
  AssignStudentGroupPayload,
  StudentGroupCreatePayload,
  StudentGroupItem,
  StudentUpdatePayload,
} from '@/types/class'

export interface ClassListQuery {
  keyword?: string
  weekday?: string
  course_type?: string
}

export const classApi = {
  async list(query?: ClassListQuery): Promise<ClassListItem[]> {
    const params: ClassListQuery = {}
    if (query?.keyword?.trim()) params.keyword = query.keyword.trim()
    if (query?.weekday?.trim()) params.weekday = query.weekday.trim()
    if (query?.course_type?.trim()) params.course_type = query.course_type.trim()
    const res = await apiClient.get<ApiResponse<ClassListItem[]>>('/classes', {
      params: Object.keys(params).length ? params : undefined,
    })
    return unwrapApi(res)
  },

  async get(classId: number): Promise<ClassDetail> {
    const res = await apiClient.get<ApiResponse<ClassDetail>>(`/classes/${classId}`)
    return unwrapApi(res)
  },

  async create(payload: ClassCreatePayload): Promise<ClassDetail> {
    const res = await apiClient.post<ApiResponse<ClassDetail>>('/classes', payload)
    return unwrapApi(res)
  },

  async update(classId: number, payload: ClassUpdatePayload): Promise<ClassDetail> {
    const res = await apiClient.put<ApiResponse<ClassDetail>>(`/classes/${classId}`, payload)
    return unwrapApi(res)
  },

  async remove(classId: number): Promise<void> {
    const res = await apiClient.delete<ApiResponse<null>>(`/classes/${classId}`)
    unwrapApi(res)
  },

  async listStudents(classId: number, keyword?: string): Promise<ClassStudentItem[]> {
    const res = await apiClient.get<ApiResponse<ClassStudentItem[]>>(`/classes/${classId}/students`, {
      params: keyword ? { keyword } : undefined,
    })
    return unwrapApi(res)
  },

  async addStudent(classId: number, payload: StudentCreatePayload): Promise<StudentCreateResponse> {
    const res = await apiClient.post<ApiResponse<StudentCreateResponse>>(
      `/classes/${classId}/students`,
      payload,
    )
    return unwrapApi(res)
  },

  async enrollStudents(classId: number, studentIds: number[]): Promise<ClassStudentItem[]> {
    const res = await apiClient.post<ApiResponse<ClassStudentItem[]>>(
      `/classes/${classId}/students/enroll`,
      { student_ids: studentIds },
    )
    return unwrapApi(res)
  },

  async updateStudent(
    classId: number,
    studentId: number,
    payload: StudentUpdatePayload,
  ): Promise<ClassStudentItem> {
    const res = await apiClient.put<ApiResponse<ClassStudentItem>>(
      `/classes/${classId}/students/${studentId}`,
      payload,
    )
    return unwrapApi(res)
  },

  async removeStudent(classId: number, studentId: number): Promise<void> {
    const res = await apiClient.delete<ApiResponse<null>>(`/classes/${classId}/students/${studentId}`)
    unwrapApi(res)
  },

  async resetPassword(classId: number, studentId: number): Promise<string> {
    const res = await apiClient.post<ApiResponse<{ default_password: string }>>(
      `/classes/${classId}/students/${studentId}/reset-password`,
    )
    const data = unwrapApi(res)
    return data.default_password
  },

  async listParentBindings(classId: number, studentId: number): Promise<ParentBindingItem[]> {
    const res = await apiClient.get<ApiResponse<ParentBindingItem[]>>(
      `/classes/${classId}/students/${studentId}/parent-bindings`,
    )
    return unwrapApi(res)
  },

  async bindParent(
    classId: number,
    studentId: number,
    payload: BindParentPayload,
  ): Promise<BindParentResponse> {
    const res = await apiClient.post<ApiResponse<BindParentResponse>>(
      `/classes/${classId}/students/${studentId}/bind-parent`,
      payload,
    )
    return unwrapApi(res)
  },

  async unbindParent(classId: number, studentId: number, parentId: number): Promise<void> {
    const res = await apiClient.delete<ApiResponse<null>>(
      `/classes/${classId}/students/${studentId}/bind-parent/${parentId}`,
    )
    unwrapApi(res)
  },

  async listGroups(classId: number): Promise<StudentGroupItem[]> {
    const res = await apiClient.get<ApiResponse<StudentGroupItem[]>>(`/classes/${classId}/groups`)
    return unwrapApi(res)
  },

  async createGroup(classId: number, payload: StudentGroupCreatePayload): Promise<StudentGroupItem> {
    const res = await apiClient.post<ApiResponse<StudentGroupItem>>(`/classes/${classId}/groups`, payload)
    return unwrapApi(res)
  },

  async deleteGroup(classId: number, groupId: number): Promise<void> {
    const res = await apiClient.delete<ApiResponse<null>>(`/classes/${classId}/groups/${groupId}`)
    unwrapApi(res)
  },

  async assignStudentGroup(
    classId: number,
    studentId: number,
    payload: AssignStudentGroupPayload,
  ): Promise<ClassStudentItem> {
    const res = await apiClient.put<ApiResponse<ClassStudentItem>>(
      `/classes/${classId}/students/${studentId}/group`,
      payload,
    )
    return unwrapApi(res)
  },
}

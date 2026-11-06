export interface AdminUserListItem {
  id: number
  account: string
  role: string
  display_name: string | null
  real_name?: string | null
  nickname?: string | null
  class_names?: string[]
  phone: string | null
  is_active: boolean
  student_no: string | null
  created_at: string
  relation_summary: string[]
}

export interface AdminUserListResponse {
  items: AdminUserListItem[]
  total: number
  page: number
  page_size: number
}

export interface AdminUserCreatePayload {
  account?: string
  password?: string
  role: 'teacher' | 'student' | 'parent'
  display_name?: string
  phone?: string
  student_no?: string
  created_by_teacher_id?: number
}

export interface AdminUserUpdatePayload {
  account?: string
  display_name?: string
  nickname?: string
  phone?: string
  student_no?: string
  is_active?: boolean
  password?: string
  created_by_teacher_id?: number | null
}

export interface AdminParentBindingItem {
  id: number
  parent_id: number
  parent_account: string
  parent_name: string | null
  student_id: number
  student_name: string | null
}

export interface AdminTeacherBrief {
  id: number
  display_name: string | null
  account: string
}

export interface AdminUserRelationsResponse {
  user_id: number
  role: string
  parent_bindings: AdminParentBindingItem[]
  bound_children: AdminParentBindingItem[]
  teacher: AdminTeacherBrief | null
  teaching_classes: string[]
  student_teacher_lines: string[]
}

export interface PublicProblemListItem {
  id: number
  public_group_id: number
  version: number
  title: string
  language: string
  difficulty: string
  publish_status: string
  test_case_count: number
  arena_enabled: boolean
  created_at: string
}

export interface EventSummaryItem {
  event_name: string
  count: number
}

export interface EventSummaryResponse {
  period_days: number
  total_events: number
  error_events: number
  judge_success_rate: number | null
  top_events: EventSummaryItem[]
}

export interface PublicProblemListResponse {
  items: PublicProblemListItem[]
  total: number
  page: number
  page_size: number
}

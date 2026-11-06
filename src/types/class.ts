export interface StudentBrief {
  id: number
  account: string
  real_name: string | null
  nickname: string | null
  display_name: string
}

export interface ClassListItem {
  id: number
  name: string
  course_type: string
  schedule: string
  expected_student_count: number
  lesson_count: number
  description: string | null
  student_count: number
  students_preview: StudentBrief[]
}

export interface ClassDetail extends ClassListItem {
  created_at: string
  updated_at: string
}

export interface ClassCreatePayload {
  name: string
  course_type: string
  schedule: string
  expected_student_count: number
  lesson_count: number
  description?: string
}

export interface ClassUpdatePayload {
  name?: string
  course_type?: string
  schedule?: string
  expected_student_count?: number
  lesson_count?: number
  description?: string
}

export interface StudentGroupItem {
  id: number
  name: string
  student_count: number
}

export interface ClassStudentItem {
  id: number
  account: string
  real_name: string | null
  nickname: string | null
  display_name: string
  completed_problems: number
  accuracy: number
  last_active: string | null
  is_active: boolean
  group_id: number | null
  group_name: string | null
}

export interface StudentCreatePayload {
  display_name: string
  account?: string
  student_no?: string
}

export interface StudentCreateResponse {
  student: ClassStudentItem
  default_password: string
}

export interface ParentBindingItem {
  id: number
  parent_id: number
  parent_phone: string
  parent_name: string
  student_id: number
  created_at: string
}

export interface BindParentPayload {
  parent_phone: string
  parent_name?: string
}

export interface BindParentResponse {
  binding: ParentBindingItem
  default_password: string | null
}

export interface StudentUpdatePayload {
  display_name?: string
  student_no?: string
}

export interface StudentGroupCreatePayload {
  name: string
}

export interface AssignStudentGroupPayload {
  group_id: number | null
}

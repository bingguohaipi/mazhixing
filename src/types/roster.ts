export interface RosterStudentItem {
  id: number
  account: string
  real_name: string | null
  nickname: string | null
  /** 对外展示名（昵称优先） */
  display_name: string
  class_names: string[]
}

export interface RosterListResponse {
  items: RosterStudentItem[]
  total: number
}

export interface RosterBatchCreateResultItem {
  display_name: string
  account: string
  student_id: number
}

export interface RosterBatchCreateResponse {
  created: RosterBatchCreateResultItem[]
  default_password: string
}

export interface RosterStudentUpdatePayload {
  display_name?: string
  student_no?: string
}

export interface StudentProfileTeacherItem {
  id: number
  display_name: string
  class_names: string[]
}

export interface StudentProfileParentItem {
  id: number
  display_name: string
}

export interface StudentProfile {
  account: string
  real_name: string | null
  display_name: string | null
  nickname: string | null
  class_names: string[]
  avatar_url: string | null
  student_no: string | null
  teachers: StudentProfileTeacherItem[]
  parents: StudentProfileParentItem[]
}

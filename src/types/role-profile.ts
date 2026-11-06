export interface TeacherProfile {
  account: string
  real_name: string | null
  nickname: string | null
  class_names: string[]
  phone: string | null
}

export interface ParentProfileChild {
  id: number
  real_name: string | null
  account: string
  class_names: string[]
}

export interface ParentProfile {
  account: string
  real_name: string | null
  nickname: string | null
  class_names: string[]
  children: ParentProfileChild[]
}

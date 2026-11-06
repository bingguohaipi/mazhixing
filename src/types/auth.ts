export type UserRole = 'admin' | 'teacher' | 'student' | 'parent'

export interface ApiResponse<T> {
  code: number
  message: string
  data: T | null
}

export type CodingLanguage = 'Python' | 'C++'

export interface UserInfo {
  id: number
  account: string
  role: UserRole
  /** 对外展示名（昵称优先） */
  display_name: string | null
  real_name?: string | null
  nickname?: string | null
  phone: string | null
  avatar_url?: string | null
  /** 学生所在班级的默认编程语言 */
  default_coding_language?: CodingLanguage | null
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface LoginResponse {
  tokens: TokenPair
  user: UserInfo
}

export interface LoginPayload {
  account: string
  password: string
  role: UserRole
}

export interface RegisterPayload {
  phone: string
  code: string
  password: string
  role: 'teacher' | 'parent'
  display_name?: string
}

export interface SendCodePayload {
  phone: string
  purpose: 'register' | 'reset_password'
  role?: UserRole
}

export interface ResetPasswordPayload {
  phone: string
  code: string
  new_password: string
  role: 'teacher' | 'parent'
}

export interface ChangePasswordPayload {
  old_password: string
  new_password: string
}

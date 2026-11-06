import type { UserRole } from '@/types/auth'

const ROLE_ZH: Record<UserRole, string> = {
  admin: '管理员',
  teacher: '教师',
  student: '学生',
  parent: '家长',
}

export function userRoleLabel(role: string): string {
  if (role === 'admin' || role === 'teacher' || role === 'student' || role === 'parent') {
    return ROLE_ZH[role]
  }
  return role
}

/** 教师端名单展示：优先真实姓名，无则回退登录账号 */
export type TeacherStudentNameSource = {
  real_name?: string | null
  account?: string
}

export function formatTeacherStudentRealName(student: TeacherStudentNameSource): string {
  const real = (student.real_name ?? '').trim()
  if (real) return real
  return (student.account ?? '').trim() || '—'
}

export function teacherStudentNameInitial(student: TeacherStudentNameSource): string {
  const label = formatTeacherStudentRealName(student)
  return label === '—' ? '?' : label.charAt(0)
}

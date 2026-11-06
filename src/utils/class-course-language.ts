import type { CodingLanguage } from '@/types/auth'

/** 与后端 course_type_to_coding_language 一致，用于展示历史班级数据 */
export function courseTypeToCodingLanguage(courseType: string | null | undefined): CodingLanguage | null {
  const raw = (courseType ?? '').trim()
  if (!raw) return null
  if (raw === 'Python' || raw === 'C++') return raw
  const lower = raw.toLowerCase()
  if (lower.includes('c++') || lower.includes('cpp')) return 'C++'
  if (lower.includes('python')) return 'Python'
  return null
}

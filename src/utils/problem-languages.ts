import type { ProblemLanguage } from '@/types/problem'

export function resolveProblemLanguages(
  languages: ProblemLanguage[] | undefined,
  fallback?: ProblemLanguage | null,
): ProblemLanguage[] {
  if (languages?.length) return languages
  if (fallback) return [fallback]
  return ['Python']
}

export function formatProblemLanguages(languages: ProblemLanguage[] | undefined, fallback?: ProblemLanguage | null): string {
  return resolveProblemLanguages(languages, fallback).join(' / ')
}

/** 做题页默认语言：URL 参数 > 班级默认 > 题目首选 */
export function pickInitialCodingLanguage(
  allowed: ProblemLanguage[],
  options?: {
    queryLang?: string | null
    classDefault?: ProblemLanguage | null
  },
): ProblemLanguage {
  const queryLang = options?.queryLang
  if (typeof queryLang === 'string' && allowed.includes(queryLang as ProblemLanguage)) {
    return queryLang as ProblemLanguage
  }
  const classDefault = options?.classDefault
  if (classDefault && allowed.includes(classDefault)) {
    return classDefault
  }
  return allowed[0]
}

import type { ProblemDetail, ProblemListItem } from '@/types/problem'

export const problemDetailToListItem = (detail: ProblemDetail): ProblemListItem => {
  const testCaseCount = detail.test_cases?.length ?? 0
  return {
    id: detail.id,
    private_no: detail.private_no ?? null,
    title: detail.title,
    language: detail.languages?.[0] ?? detail.language,
    languages: detail.languages?.length ? detail.languages : [detail.language],
    difficulty: detail.difficulty,
    gesp_level: detail.gesp_level,
    knowledge_point: detail.knowledge_point,
    knowledge_points: detail.knowledge_points ?? [],
    test_case_count: testCaseCount,
    is_publishable: detail.is_publishable ?? testCaseCount > 0,
    pass_rate: detail.pass_rate ?? 0,
    submission_count: detail.submission_count ?? 0,
    created_at: detail.created_at ?? new Date().toISOString(),
  }
}

export const mergeProblemLists = (...lists: ProblemListItem[][]): ProblemListItem[] => {
  const map = new Map<number, ProblemListItem>()
  lists.flat().forEach((item) => map.set(item.id, item))
  return Array.from(map.values())
}

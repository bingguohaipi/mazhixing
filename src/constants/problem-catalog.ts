/** 搜索或筛选后无匹配题目时的统一提示 */
export const PROBLEM_FILTER_EMPTY_MESSAGE = '暂无对应条件的题目，敬请期待~'

export type ProblemCatalogQueryInput = {
  keyword?: string
  difficulty?: string
  knowledgePoint?: string
  language?: string
  statusFilter?: string
  myPassed?: string
}

export function hasProblemCatalogQuery(input: ProblemCatalogQueryInput): boolean {
  return Boolean(
    input.keyword?.trim() ||
      input.difficulty ||
      input.knowledgePoint?.trim() ||
      input.language ||
      input.statusFilter ||
      input.myPassed,
  )
}

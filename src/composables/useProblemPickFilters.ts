import { computed, reactive } from 'vue'
import type { ProblemDifficulty } from '@/types/problem'

export type ProblemPickFilterState = {
  difficulty: '' | ProblemDifficulty
  knowledgePoint: string
}

export function useProblemPickFilters() {
  const filters = reactive<ProblemPickFilterState>({
    difficulty: '',
    knowledgePoint: '',
  })

  const activeFilterCount = computed(() => {
    let n = 0
    if (filters.difficulty) n += 1
    if (filters.knowledgePoint) n += 1
    return n
  })

  const hasFilterOrKeyword = (keyword: string) =>
    Boolean(keyword.trim()) || activeFilterCount.value > 0

  const resetFilters = () => {
    filters.difficulty = ''
    filters.knowledgePoint = ''
  }

  const apiFilterParams = () => ({
    difficulty: filters.difficulty || undefined,
    knowledge_point: filters.knowledgePoint.trim() || undefined,
  })

  return {
    filters,
    activeFilterCount,
    hasFilterOrKeyword,
    resetFilters,
    apiFilterParams,
  }
}

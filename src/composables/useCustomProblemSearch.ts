import { computed, ref, watch, type Ref } from 'vue'
import { useDebouncedWatch } from '@/composables/useDebouncedWatch'
import { useProblemPickFilters } from '@/composables/useProblemPickFilters'
import { problemApi } from '@/api/problems'
import type { ProblemListItem } from '@/types/problem'

export function useCustomProblemSearch(selectedIds: Ref<number[]>) {
  const keyword = ref('')
  const loading = ref(false)
  const results = ref<ProblemListItem[]>([])
  const cache = ref(new Map<number, ProblemListItem>())
  const { filters, activeFilterCount, hasFilterOrKeyword, resetFilters, apiFilterParams } =
    useProblemPickFilters()

  const syncCacheFromSelection = () => {
    const merged = [...results.value]
    cache.value.forEach((item) => {
      if (selectedIds.value.includes(item.id) && !merged.some((p) => p.id === item.id)) {
        merged.push(item)
      }
    })
    for (const item of merged) {
      if (selectedIds.value.includes(item.id)) {
        cache.value.set(item.id, item)
      }
    }
  }

  const search = async () => {
    const q = keyword.value.trim()
    if (!hasFilterOrKeyword(q)) {
      results.value = []
      return
    }
    loading.value = true
    try {
      const data = await problemApi.listCustom({
        keyword: q || undefined,
        page: 1,
        page_size: 50,
        ...apiFilterParams(),
      })
      results.value = data.items.filter((item) => item.is_publishable)
      syncCacheFromSelection()
    } finally {
      loading.value = false
    }
  }

  useDebouncedWatch(keyword, () => {
    void search()
  })

  const applyFilters = () => {
    void search()
  }

  const onResetFilters = () => {
    resetFilters()
    void search()
  }

  watch(selectedIds, () => syncCacheFromSelection(), { deep: true })

  const displayed = computed(() => {
    const map = new Map<number, ProblemListItem>()
    for (const id of selectedIds.value) {
      const cached = cache.value.get(id)
      if (cached) map.set(id, cached)
    }
    for (const item of results.value) {
      map.set(item.id, item)
    }
    return Array.from(map.values())
  })

  const customProblemIdSet = computed(() => new Set(cache.value.keys()))

  const seedCache = (items: ProblemListItem[]) => {
    for (const item of items) {
      cache.value.set(item.id, item)
    }
  }

  const mergeItem = (item: ProblemListItem) => {
    cache.value.set(item.id, item)
    results.value = [item, ...results.value.filter((p) => p.id !== item.id)]
  }

  const hasSearchCriteria = computed(() => hasFilterOrKeyword(keyword.value))

  return {
    keyword,
    filters,
    activeFilterCount,
    hasSearchCriteria,
    loading,
    results,
    displayed,
    customProblemIdSet,
    search,
    applyFilters,
    onResetFilters,
    seedCache,
    mergeItem,
  }
}

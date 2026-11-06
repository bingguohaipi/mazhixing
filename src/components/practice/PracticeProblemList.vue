<template>
  <div class="practice-problem-list bg-white rounded-xl border border-gray-200">
    <div v-if="showToolbar" class="relative z-20 px-4 py-3 border-b border-gray-100 space-y-2">
      <ListQueryToolbar
        :keyword="keyword"
        placeholder="搜索题目"
        :sort-value="sortValue"
        :sort-options="sortOptions"
        :filter-active="activeFilterCount > 0"
        @update:keyword="onKeywordUpdate"
        @update:sort-value="onSortValueChange"
        @toggle-filter="toggleFilter"
      >
        <template v-if="showFilterControl" #filter>
          <PracticeProblemFilterPopover
            :open="filterOpen"
            :difficulty="difficulty"
            :knowledge-point="knowledgePoint"
            :language="language"
            :show-knowledge-point="showKnowledgePointFilter"
            :knowledge-point-options="knowledgePointOptions"
            @update:difficulty="emit('update:difficulty', $event)"
            @update:knowledge-point="emit('update:knowledgePoint', $event)"
            @update:language="emit('update:language', $event)"
            @apply="onFilterApply"
            @reset="onFilterReset"
          />
        </template>
      </ListQueryToolbar>
      <div v-if="solvedSummary !== null" class="text-sm text-gray-500 text-right">
        {{ solvedSummary.solved }} / {{ solvedSummary.total }} 已解答
      </div>
    </div>

    <div v-if="loading" class="py-16 text-center text-gray-500 text-sm">加载中...</div>
    <div v-else-if="items.length === 0" class="py-16 text-center text-gray-500 text-sm">
      {{ listEmptyText }}
    </div>
    <ul v-else class="divide-y divide-gray-100">
      <li
        v-for="q in items"
        :key="q.id"
        class="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 cursor-pointer group"
        @click="emit('select', q.id)"
      >
        <span class="w-5 shrink-0 text-center text-sm" :class="statusIconClass(q.my_status)">
          {{ statusIcon(q.my_status) }}
        </span>
        <div class="flex-1 min-w-0 flex items-center gap-2">
          <span class="text-gray-400 text-sm shrink-0">{{ q.id }}.</span>
          <span class="text-sm font-medium text-gray-900 truncate group-hover:text-indigo-600">
            {{ q.title }}
          </span>
        </div>
        <span class="text-xs text-gray-400 w-14 text-right shrink-0">{{ q.pass_rate }}%</span>
        <span class="text-xs font-medium w-12 text-right shrink-0" :class="difficultyTextClass(q.difficulty)">
          {{ q.difficulty }}
        </span>
      </li>
    </ul>

    <div
      v-if="totalPages > 1"
      class="flex items-center justify-center gap-2 px-4 py-3 border-t border-gray-100 text-sm"
    >
      <button
        type="button"
        class="px-3 py-1 rounded border border-gray-200 disabled:opacity-40"
        :disabled="page <= 1"
        @click="emit('update:page', page - 1)"
      >
        上一页
      </button>
      <span class="text-gray-500">{{ page }} / {{ totalPages }}</span>
      <button
        type="button"
        class="px-3 py-1 rounded border border-gray-200 disabled:opacity-40"
        :disabled="page >= totalPages"
        @click="emit('update:page', page + 1)"
      >
        下一页
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import ListQueryToolbar from '@/components/ListQueryToolbar.vue'
import PracticeProblemFilterPopover from '@/components/practice/PracticeProblemFilterPopover.vue'
import type {
  KnowledgePointOptionItem,
  PracticeProblemListItem,
  PracticeProblemSortBy,
  PracticeProblemSortOrder,
} from '@/types/practice'
import {
  hasProblemCatalogQuery,
  PROBLEM_FILTER_EMPTY_MESSAGE,
} from '@/constants/problem-catalog'
import { difficultyTextClass, statusIcon, statusIconClass } from '@/utils/practice-ui'

const props = withDefaults(
  defineProps<{
    items: PracticeProblemListItem[]
    loading?: boolean
    page?: number
    total?: number
    pageSize?: number
    keyword?: string
    difficulty?: string
    knowledgePoint?: string
    language?: string
    knowledgePointOptions?: KnowledgePointOptionItem[]
    showToolbar?: boolean
    showFilterControl?: boolean
    showKnowledgePointFilter?: boolean
    showSortControl?: boolean
    sortBy?: PracticeProblemSortBy
    sortOrder?: PracticeProblemSortOrder
    emptyText?: string
    filterEmptyText?: string
    solvedSummary?: { solved: number; total: number } | null
  }>(),
  {
    loading: false,
    page: 1,
    total: 0,
    pageSize: 20,
    keyword: '',
    difficulty: '',
    knowledgePoint: '',
    language: '',
    knowledgePointOptions: () => [],
    showToolbar: true,
    showFilterControl: true,
    showKnowledgePointFilter: true,
    showSortControl: true,
    sortBy: 'id',
    sortOrder: 'asc',
    emptyText: '暂无题目',
    filterEmptyText: PROBLEM_FILTER_EMPTY_MESSAGE,
    solvedSummary: null,
  },
)

const hasActiveQuery = computed(() =>
  hasProblemCatalogQuery({
    keyword: props.keyword,
    difficulty: props.difficulty,
    knowledgePoint: props.showKnowledgePointFilter ? props.knowledgePoint : '',
    language: props.language,
  }),
)

const listEmptyText = computed(() =>
  hasActiveQuery.value ? props.filterEmptyText : props.emptyText,
)

const emit = defineEmits<{
  'update:keyword': [value: string]
  'update:difficulty': [value: string]
  'update:knowledgePoint': [value: string]
  'update:language': [value: string]
  'update:sortBy': [value: PracticeProblemSortBy]
  'update:sortOrder': [value: PracticeProblemSortOrder]
  'update:page': [page: number]
  search: []
  select: [problemId: number]
}>()

const filterOpen = ref(false)

const sortOptions = computed(() => {
  const opts = [
    { value: 'id:asc', label: '序号 ↑' },
    { value: 'id:desc', label: '序号 ↓' },
    { value: 'difficulty:asc', label: '难度 ↑' },
    { value: 'difficulty:desc', label: '难度 ↓' },
  ]
  return props.showSortControl ? opts : []
})

const activeFilterCount = computed(() => {
  let n = 0
  if (props.difficulty) n += 1
  if (props.showKnowledgePointFilter && props.knowledgePoint) n += 1
  if (props.language) n += 1
  return n
})

const sortValue = computed(() => `${props.sortBy}:${props.sortOrder}`)

function toggleFilter() {
  filterOpen.value = !filterOpen.value
}

function onFilterApply() {
  filterOpen.value = false
  emit('search')
}

function onFilterReset() {
  emit('update:difficulty', '')
  emit('update:knowledgePoint', '')
  emit('update:language', '')
  filterOpen.value = false
  emit('search')
}

function onSortValueChange(raw: string) {
  const [by, order] = raw.split(':') as [PracticeProblemSortBy, PracticeProblemSortOrder]
  emit('update:sortBy', by)
  emit('update:sortOrder', order)
  emit('search')
}

const totalPages = computed(() =>
  Math.max(1, Math.ceil(props.total / props.pageSize)),
)

let keywordDebounceTimer: ReturnType<typeof setTimeout> | null = null

function onKeywordUpdate(value: string) {
  emit('update:keyword', value)
  if (keywordDebounceTimer) clearTimeout(keywordDebounceTimer)
  keywordDebounceTimer = setTimeout(() => emit('search'), 300)
}
</script>

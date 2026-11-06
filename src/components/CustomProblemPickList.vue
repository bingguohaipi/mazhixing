<template>
  <div>
    <div class="text-xs text-gray-500 mb-1">自有题库</div>
    <ProblemPickSearchToolbar
      :keyword="keyword"
      placeholder="自有题号或题目关键词（输入即搜索）"
      :difficulty="difficulty"
      :knowledge-point="knowledgePoint"
      :active-filter-count="activeFilterCount"
      :knowledge-point-options="knowledgePointOptions"
      @update:keyword="emit('update:keyword', $event)"
      @update:difficulty="emit('update:difficulty', $event)"
      @update:knowledge-point="emit('update:knowledgePoint', $event)"
      @apply="emit('applyFilters')"
      @reset="emit('resetFilters')"
    />
    <p class="text-xs text-gray-400 mb-1">点击题目标题可编辑；也可在侧栏「自有题库」统一管理</p>
    <div v-if="loading" class="text-sm text-gray-400 py-1">搜索中...</div>
    <div v-else-if="!hasSearchCriteria && displayed.length === 0" class="text-xs text-gray-500 py-2">
      输入自有题号/关键词，或使用右侧筛选；也可「自行出题」新建
    </div>
    <div v-else-if="hasSearchCriteria && displayed.length === 0" class="text-xs text-gray-500 py-2">
      {{ PROBLEM_FILTER_EMPTY_MESSAGE }}
    </div>
    <div
      v-else
      class="notice-class-list"
      style="max-height: 120px; overflow-y: auto;"
    >
      <div
        v-for="q in displayed"
        :key="'c-' + q.id"
        class="notice-class-item flex items-start gap-2"
      >
        <input
          type="checkbox"
          class="mt-0.5 shrink-0"
          :checked="selectedIds.includes(q.id)"
          @change="toggle(q.id, ($event.target as HTMLInputElement).checked)"
        >
        <button
          type="button"
          class="text-left flex-1 min-w-0 text-sm text-indigo-300 hover:text-indigo-200 hover:underline"
          @click="emit('edit', q.id)"
        >
          #{{ q.private_no ?? '—' }} {{ q.title }}（{{ q.language }}·{{ q.difficulty }}）
          <span v-if="!q.is_publishable" class="text-amber-400"> · 需用例</span>
        </button>
      </div>
    </div>
    <p v-if="selectedCustomCount > 0" class="text-xs text-gray-500 mt-1">已选自有题 {{ selectedCustomCount }} 道</p>
  </div>
</template>

<script setup lang="ts">
import ProblemPickSearchToolbar from '@/components/ProblemPickSearchToolbar.vue'
import { PROBLEM_FILTER_EMPTY_MESSAGE } from '@/constants/problem-catalog'
import type { KnowledgePointOptionItem } from '@/types/practice'
import type { ProblemListItem } from '@/types/problem'

const props = defineProps<{
  keyword: string
  difficulty: string
  knowledgePoint: string
  activeFilterCount: number
  hasSearchCriteria: boolean
  knowledgePointOptions: KnowledgePointOptionItem[]
  loading: boolean
  displayed: ProblemListItem[]
  selectedIds: number[]
  selectedCustomCount: number
}>()

const emit = defineEmits<{
  edit: [problemId: number]
  'update:keyword': [value: string]
  'update:difficulty': [value: string]
  'update:knowledgePoint': [value: string]
  applyFilters: []
  resetFilters: []
  'update:selectedIds': [ids: number[]]
}>()

function toggle(id: number, checked: boolean) {
  const set = new Set(props.selectedIds)
  if (checked) set.add(id)
  else set.delete(id)
  emit('update:selectedIds', [...set])
}
</script>

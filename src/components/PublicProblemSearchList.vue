<template>
  <div>
    <div class="text-xs text-gray-500 mb-1">公共题库</div>
    <ProblemPickSearchToolbar
      :keyword="keyword"
      placeholder="题号或题目关键词（输入即搜索）"
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
    <div v-if="loading" class="text-sm text-gray-400 py-1">搜索中...</div>
    <div v-else-if="!hasSearchCriteria && displayed.length === 0" class="text-xs text-gray-500 py-2">
      输入题号/关键词，或使用右侧筛选（难度、知识点）查找题目
    </div>
    <div v-else-if="hasSearchCriteria && displayed.length === 0" class="text-xs text-gray-500 py-2">
      {{ PROBLEM_FILTER_EMPTY_MESSAGE }}
    </div>
    <div v-else class="notice-class-list" style="max-height: 160px; overflow-y: auto;">
      <label v-for="q in displayed" :key="'pub-' + q.id" class="notice-class-item">
        <input type="checkbox" :checked="selectedIds.includes(q.id)" @change="toggle(q.id, ($event.target as HTMLInputElement).checked)">
        <span>#{{ q.id }} {{ q.title }}（{{ q.language }}·{{ q.difficulty }}）</span>
      </label>
    </div>
    <p v-if="selectedPublicCount > 0" class="text-xs text-gray-500 mt-1">已选公共题 {{ selectedPublicCount }} 道</p>
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
  selectedPublicCount: number
}>()

const emit = defineEmits<{
  'update:keyword': [value: string]
  'update:difficulty': [value: string]
  'update:knowledgePoint': [value: string]
  applyFilters: []
  resetFilters: []
  'update:selectedIds': [ids: number[]]
}>()

const toggle = (id: number, checked: boolean) => {
  const next = new Set(props.selectedIds)
  if (checked) next.add(id)
  else next.delete(id)
  emit('update:selectedIds', Array.from(next))
}
</script>

<template>
  <div>
    <div class="bg-white border-b border-gray-200 px-6 py-3">
      <h1 class="text-lg font-semibold text-gray-900">公共题库</h1>
      <p class="text-sm text-gray-500 mt-0.5">平台统一题目，仅供浏览与布置作业选题；自行创建的题目请见「自有题库」</p>
    </div>

    <div class="p-6 space-y-4">
      <ListQueryToolbar
        v-model:keyword="filters.keyword"
        :sort-value="sortValue"
        :sort-options="sortOptions"
        placeholder="搜索题目"
        :filter-active="activeFilterCount > 0"
        @update:sort-value="onSortValueChange"
        @toggle-filter="toggleFilter"
      >
        <template #filter>
          <PracticeProblemFilterPopover
            :open="filterOpen"
            :show-knowledge-point="true"
            :show-my-passed="true"
            :difficulty="filters.difficulty"
            :knowledge-point="filters.knowledgePoint"
            :language="filters.language"
            :my-passed="filters.myPassed"
            :knowledge-point-options="knowledgePointOptions"
            @update:difficulty="filters.difficulty = $event"
            @update:knowledge-point="filters.knowledgePoint = $event"
            @update:language="filters.language = $event"
            @update:my-passed="filters.myPassed = $event"
            @apply="onFilterApply"
            @reset="onFilterReset"
          />
        </template>
      </ListQueryToolbar>

      <div v-if="loading" class="text-center py-16 text-gray-500">加载中...</div>

      <div v-else-if="problems.length === 0" class="bg-white rounded-xl border border-gray-100 p-12 text-center">
        <div v-if="!hasActiveQuery" class="text-4xl mb-3">📚</div>
        <p class="text-gray-500">
          {{ hasActiveQuery ? PROBLEM_FILTER_EMPTY_MESSAGE : '暂无已上架的公共题目，请等待管理员发布' }}
        </p>
      </div>

      <div v-else class="bg-white rounded-xl border border-gray-100 overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-gray-500">
            <tr class="text-left">
              <th class="px-4 py-3 font-medium">编号</th>
              <th class="px-4 py-3 font-medium">题目名称</th>
              <th class="px-4 py-3 font-medium">语言</th>
              <th class="px-4 py-3 font-medium">难度</th>
              <th class="px-4 py-3 font-medium">知识点</th>
              <th class="px-4 py-3 font-medium">用例数</th>
              <th class="px-4 py-3 font-medium">通过率</th>
              <th class="px-4 py-3 font-medium">通过者</th>
              <th class="px-4 py-3 font-medium">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="problem in problems" :key="problem.id" class="hover:bg-gray-50">
              <td class="px-4 py-3 text-gray-400">#{{ problem.id }}</td>
              <td class="px-4 py-3 font-medium text-gray-900">{{ problem.title }}</td>
              <td class="px-4 py-3">
                <span class="badge bg-gray-100 text-gray-700">
                  {{ formatLanguages(problem) }}
                </span>
              </td>
              <td class="px-4 py-3">
                <span class="badge" :class="getDifficultyClass(problem.difficulty)">{{ problem.difficulty }}</span>
              </td>
              <td class="px-4 py-3 text-gray-500">{{ formatKnowledgePoints(problem) }}</td>
              <td class="px-4 py-3 text-gray-500">{{ problem.test_case_count }}</td>
              <td class="px-4 py-3 text-gray-500">{{ problem.pass_rate != null ? `${problem.pass_rate}%` : '-' }}</td>
              <td class="px-4 py-3">
                <button
                  type="button"
                  class="text-indigo-600 hover:underline"
                  @click="openAcSolvers(problem)"
                >
                  查看名单
                </button>
              </td>
              <td class="px-4 py-3">
                <button class="text-indigo-600 hover:underline" @click="openView(problem.id)">查看</button>
              </td>
            </tr>
          </tbody>
        </table>

        <div class="px-4 py-3 border-t border-gray-100 flex items-center justify-between text-sm text-gray-500">
          <span>共 {{ total }} 条</span>
          <div class="flex items-center gap-1">
            <button class="px-2 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-40" :disabled="page <= 1" @click="loadProblems(page - 1)">上一页</button>
            <span class="px-2">第 {{ page }} / {{ totalPages }} 页</span>
            <button class="px-2 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-40" :disabled="page >= totalPages" @click="loadProblems(page + 1)">下一页</button>
          </div>
        </div>
      </div>
    </div>

    <ProblemAcSolversModal
      v-if="acSolversTarget"
      :problem-id="acSolversTarget.id"
      :title="acSolversTarget.title"
      @close="acSolversTarget = null"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import ProblemAcSolversModal from '@/components/ProblemAcSolversModal.vue'
import ListQueryToolbar from '@/components/ListQueryToolbar.vue'
import PracticeProblemFilterPopover from '@/components/practice/PracticeProblemFilterPopover.vue'
import { useDebouncedWatch } from '@/composables/useDebouncedWatch'
import { usePageDwell } from '@/composables/usePageDwell'
import { practiceApi } from '@/api/practice'
import { problemApi } from '@/api/problems'
import { toast } from '@/utils/toast'
import { trackEvent } from '@/utils/tracker'
import type { KnowledgePointOptionItem } from '@/types/practice'
import type {
  ProblemCatalogSortBy,
  ProblemCatalogSortOrder,
  ProblemDifficulty,
  ProblemLanguage,
  ProblemListItem,
} from '@/types/problem'
import {
  hasProblemCatalogQuery,
  PROBLEM_FILTER_EMPTY_MESSAGE,
} from '@/constants/problem-catalog'
import { formatProblemLanguages } from '@/utils/problem-languages'

const router = useRouter()

const problems = ref<ProblemListItem[]>([])
const acSolversTarget = ref<ProblemListItem | null>(null)
const loading = ref(true)
const total = ref(0)
const page = ref(1)
const pageSize = 20
const knowledgePointOptions = ref<KnowledgePointOptionItem[]>([])
const filterOpen = ref(false)
const sortOptions = [
  { value: 'id:asc', label: '序号 ↑' },
  { value: 'id:desc', label: '序号 ↓' },
  { value: 'difficulty:asc', label: '难度 ↑' },
  { value: 'difficulty:desc', label: '难度 ↓' },
]

const filters = reactive({
  keyword: '',
  language: '' as '' | ProblemLanguage,
  difficulty: '' as '' | ProblemDifficulty,
  knowledgePoint: '',
  myPassed: '' as '' | 'passed',
  sortBy: 'id' as ProblemCatalogSortBy,
  sortOrder: 'asc' as ProblemCatalogSortOrder,
})

const sortValue = computed(() => `${filters.sortBy}:${filters.sortOrder}`)

const activeFilterCount = computed(() => {
  let n = 0
  if (filters.difficulty) n += 1
  if (filters.knowledgePoint) n += 1
  if (filters.language) n += 1
  if (filters.myPassed) n += 1
  return n
})

const hasActiveQuery = computed(() =>
  hasProblemCatalogQuery({
    keyword: filters.keyword,
    difficulty: filters.difficulty,
    knowledgePoint: filters.knowledgePoint,
    language: filters.language,
  }),
)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

const getDifficultyClass = (difficulty: ProblemDifficulty) => {
  const map: Record<ProblemDifficulty, string> = {
    '入门': 'bg-green-100 text-green-700',
    '简单': 'bg-yellow-100 text-yellow-700',
    '中等': 'bg-orange-100 text-orange-700',
    '困难': 'bg-red-100 text-red-700',
  }
  return map[difficulty]
}

const loadProblems = async (targetPage = page.value) => {
  loading.value = true
  try {
    const result = await problemApi.listPublicCatalog({
      page: targetPage,
      page_size: pageSize,
      keyword: filters.keyword.trim() || undefined,
      language: filters.language || undefined,
      difficulty: filters.difficulty || undefined,
      knowledge_point: filters.knowledgePoint || undefined,
      sort_by: filters.sortBy,
      sort_order: filters.sortOrder,
      my_passed: filters.myPassed === 'passed',
    })
    problems.value = result.items
    total.value = result.total
    page.value = result.page
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '加载题目失败')
  } finally {
    loading.value = false
  }
}

const onSortValueChange = (raw: string) => {
  const [by, order] = raw.split(':') as [ProblemCatalogSortBy, ProblemCatalogSortOrder]
  filters.sortBy = by
  filters.sortOrder = order
  void loadProblems(1)
}

function toggleFilter() {
  filterOpen.value = !filterOpen.value
}

function onFilterApply() {
  filterOpen.value = false
  void loadProblems(1)
}

function onFilterReset() {
  filters.difficulty = ''
  filters.knowledgePoint = ''
  filters.language = ''
  filters.myPassed = ''
  filterOpen.value = false
  void loadProblems(1)
}

function onDocumentClick(event: MouseEvent) {
  if (!filterOpen.value) return
  const target = event.target as HTMLElement
  if (target.closest('.practice-filter-popover')) return
  if (target.closest('.list-query-toolbar-filter-btn')) return
  filterOpen.value = false
}

watch(filterOpen, (open) => {
  document.removeEventListener('click', onDocumentClick)
  if (open) {
    void nextTick(() => {
      document.addEventListener('click', onDocumentClick)
    })
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
})

const formatLanguages = (problem: ProblemListItem) =>
  formatProblemLanguages(problem.languages, problem.language)

const formatKnowledgePoints = (problem: ProblemListItem) => {
  const tags = problem.knowledge_points?.length
    ? problem.knowledge_points
    : problem.knowledge_point
      ? [problem.knowledge_point]
      : []
  return tags.length ? tags.join('、') : '-'
}

const openAcSolvers = (problem: ProblemListItem) => {
  acSolversTarget.value = problem
}

const openView = (problemId: number) => {
  trackEvent({
    event_name: 'problem_view',
    page: '/teacher/questions',
    module: 'teacher',
    detail: `problem=${problemId}`,
  })
  router.push(`/teacher/coding/${problemId}`)
}

usePageDwell('teacher_questions_dwell', '/teacher/questions', 'teacher')

useDebouncedWatch(
  () => filters.keyword,
  () => {
    void loadProblems(1)
  },
)

onMounted(async () => {
  try {
    knowledgePointOptions.value = await practiceApi.listKnowledgePointOptions()
  } catch {
    knowledgePointOptions.value = []
  }
  await loadProblems(1)
})
</script>

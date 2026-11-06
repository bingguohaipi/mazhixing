<template>
  <div>
    <div class="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between gap-3 flex-wrap">
      <div>
        <h1 class="text-lg font-semibold text-gray-900">自有题库</h1>
        <p class="text-sm text-gray-500 mt-0.5">
          自行出题会保存在此处；编号为自有题库独立序号（与公共题库题号无关）
        </p>
      </div>
      <button
        type="button"
        class="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 shrink-0"
        @click="openCreate"
      >
        + 新建题目
      </button>
    </div>

    <div class="p-6 space-y-4">
      <ListQueryToolbar
        v-model:keyword="filters.keyword"
        :sort-value="sortValue"
        :sort-options="sortOptions"
        @update:sort-value="onSortValueChange"
        placeholder="搜索自有编号或标题"
        :filter-active="activeFilterCount > 0"
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
        <template v-if="hasActiveQuery">
          <p class="text-gray-500">{{ PROBLEM_FILTER_EMPTY_MESSAGE }}</p>
        </template>
        <template v-else>
          <div class="text-4xl mb-3">📝</div>
          <p class="text-gray-500 mb-4">还没有自有题目，点击「新建题目」或在布置作业时使用「自行出题」</p>
          <button type="button" class="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg" @click="openCreate">
            新建题目
          </button>
        </template>
      </div>

      <div v-else class="bg-white rounded-xl border border-gray-100 overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-gray-500">
            <tr class="text-left">
              <th class="px-4 py-3 font-medium">自有编号</th>
              <th class="px-4 py-3 font-medium">题目名称</th>
              <th class="px-4 py-3 font-medium">语言</th>
              <th class="px-4 py-3 font-medium">难度</th>
              <th class="px-4 py-3 font-medium">知识点</th>
              <th class="px-4 py-3 font-medium">用例</th>
              <th class="px-4 py-3 font-medium">状态</th>
              <th class="px-4 py-3 font-medium">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="problem in problems" :key="problem.id" class="hover:bg-gray-50">
              <td class="px-4 py-3 text-gray-400 font-medium">#{{ formatPrivateProblemNo(problem.private_no) }}</td>
              <td class="px-4 py-3 font-medium text-gray-900">{{ problem.title }}</td>
              <td class="px-4 py-3">
                <span class="badge bg-gray-100 text-gray-700">{{ formatLanguages(problem) }}</span>
              </td>
              <td class="px-4 py-3">
                <span class="badge" :class="getDifficultyClass(problem.difficulty)">{{ problem.difficulty }}</span>
              </td>
              <td class="px-4 py-3 text-gray-500">{{ formatKnowledgePoints(problem) }}</td>
              <td class="px-4 py-3 text-gray-500">{{ problem.test_case_count }}</td>
              <td class="px-4 py-3">
                <span
                  v-if="problem.is_publishable"
                  class="text-xs text-green-600"
                >可布置</span>
                <span v-else class="text-xs text-amber-600">需补充用例</span>
              </td>
              <td class="px-4 py-3 space-x-3 whitespace-nowrap">
                <button type="button" class="text-indigo-600 hover:underline" @click="openPreview(problem.id)">
                  查看
                </button>
                <button type="button" class="text-indigo-600 hover:underline" @click="openEdit(problem.id)">
                  编辑
                </button>
                <button type="button" class="text-red-600 hover:underline" @click="removeProblem(problem)">
                  删除
                </button>
              </td>
            </tr>
          </tbody>
        </table>

        <div class="px-4 py-3 border-t border-gray-100 flex items-center justify-between text-sm text-gray-500">
          <span>共 {{ total }} 道</span>
          <div class="flex items-center gap-1">
            <button
              type="button"
              class="px-2 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-40"
              :disabled="page <= 1"
              @click="loadProblems(page - 1)"
            >
              上一页
            </button>
            <span class="px-2">第 {{ page }} / {{ totalPages }} 页</span>
            <button
              type="button"
              class="px-2 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-40"
              :disabled="page >= totalPages"
              @click="loadProblems(page + 1)"
            >
              下一页
            </button>
          </div>
        </div>
      </div>
    </div>

    <ProblemFormModal
      v-if="showForm"
      :problem="editingProblem"
      @close="closeForm"
      @success="onSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import ListQueryToolbar from '@/components/ListQueryToolbar.vue'
import ProblemFormModal from '@/components/ProblemFormModal.vue'
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
  ProblemDetail,
  ProblemDifficulty,
  ProblemLanguage,
  ProblemListItem,
} from '@/types/problem'
import { formatProblemLanguages } from '@/utils/problem-languages'
import {
  hasProblemCatalogQuery,
  PROBLEM_FILTER_EMPTY_MESSAGE,
} from '@/constants/problem-catalog'
import { formatPrivateProblemNo } from '@/utils/private-problem'

usePageDwell('teacher_my_questions_dwell', '/teacher/my-questions', 'teacher')

const router = useRouter()
const problems = ref<ProblemListItem[]>([])
const loading = ref(true)
const total = ref(0)
const page = ref(1)
const pageSize = 20
const showForm = ref(false)
const editingProblem = ref<ProblemDetail | null>(null)
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
    myPassed: filters.myPassed,
  }),
)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

const getDifficultyClass = (difficulty: ProblemDifficulty) => {
  const map: Record<ProblemDifficulty, string> = {
    入门: 'bg-green-100 text-green-700',
    简单: 'bg-yellow-100 text-yellow-700',
    中等: 'bg-orange-100 text-orange-700',
    困难: 'bg-red-100 text-red-700',
  }
  return map[difficulty]
}

const formatLanguages = (problem: ProblemListItem) =>
  formatProblemLanguages(problem.languages, problem.language)

const formatKnowledgePoints = (problem: ProblemListItem) => {
  const tags = problem.knowledge_points?.length
    ? problem.knowledge_points
    : problem.knowledge_point
      ? [problem.knowledge_point]
      : []
  return tags.length ? tags.join('、') : '—'
}

const loadProblems = async (targetPage = page.value) => {
  loading.value = true
  try {
    const result = await problemApi.listCustom({
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
    toast.error(err instanceof Error ? err.message : '加载失败')
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

useDebouncedWatch(
  () => filters.keyword,
  () => {
    void loadProblems(1)
  },
)

const openCreate = () => {
  editingProblem.value = null
  showForm.value = true
}

const openEdit = async (problemId: number) => {
  try {
    editingProblem.value = await problemApi.get(problemId)
    showForm.value = true
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '加载题目失败')
  }
}

const openPreview = (problemId: number) => {
  trackEvent({
    event_name: 'problem_view',
    page: '/teacher/my-questions',
    module: 'teacher',
    detail: `problem=${problemId},scope=private`,
  })
  void router.push(`/teacher/coding/${problemId}`)
}

const closeForm = () => {
  showForm.value = false
  editingProblem.value = null
}

const onSaved = () => {
  closeForm()
  void loadProblems(page.value)
}

const removeProblem = async (problem: ProblemListItem) => {
  const label = formatPrivateProblemNo(problem.private_no)
  if (!confirm(`确定删除自有题 #${label}「${problem.title}」？删除后不可恢复。`)) return
  try {
    await problemApi.remove(problem.id)
    toast.success('题目已删除')
    void loadProblems(page.value)
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '删除失败')
  }
}

onMounted(async () => {
  try {
    knowledgePointOptions.value = await practiceApi.listKnowledgePointOptions()
  } catch {
    knowledgePointOptions.value = []
  }
  await loadProblems(1)
})
</script>

<template>
  <div class="student-questions min-h-full">
    <div class="bg-white border-b border-gray-200 px-6 py-4">
      <h1 class="text-lg font-semibold text-gray-900">题库</h1>
      <p class="text-xs text-gray-500 mt-1">按知识点分类练习，或在下方搜索、浏览全部公共题目</p>
    </div>

    <div class="w-full px-3 sm:px-4 py-3 sm:py-4 space-y-5">
      <section class="bg-white rounded-xl border border-gray-200 p-4">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-sm font-semibold text-gray-900">知识点</h2>
          <button
            v-if="tags.length > tagCollapseLimit"
            type="button"
            class="text-xs text-gray-500 hover:text-indigo-600 flex items-center gap-1"
            @click="tagsExpanded = !tagsExpanded"
          >
            {{ tagsExpanded ? '收起' : '展开全部' }}
            <span>{{ tagsExpanded ? '∧' : '∨' }}</span>
          </button>
        </div>
        <div v-if="loadingTags" class="text-sm text-gray-400 py-6 text-center">加载知识点...</div>
        <div v-else-if="visibleTags.length === 0" class="text-sm text-gray-500 py-4">暂无知识点标签</div>
        <div v-else class="flex flex-wrap gap-2">
          <RouterLink
            v-for="tag in visibleTags"
            :key="tag.name"
            :to="`/student/questions/topic/${encodeTopicSlug(tag.name)}`"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-gray-200 bg-gray-50 hover:border-indigo-300 hover:bg-indigo-50 text-sm text-gray-800 transition"
          >
            <span>{{ tag.name }}</span>
            <span class="text-xs text-gray-400 bg-white px-1.5 py-0.5 rounded-full border border-gray-100">
              {{ tag.problem_count }}
            </span>
          </RouterLink>
        </div>
      </section>

      <section>
        <div class="flex items-center gap-2 mb-3">
          <span class="text-sm font-semibold px-3 py-1 rounded-full bg-gray-900 text-white">
            全部题目
          </span>
        </div>
        <PracticeProblemList
          :items="questions"
          :loading="loadingList"
          :page="page"
          :total="total"
          :page-size="pageSize"
          :keyword="keyword"
          :difficulty="difficulty"
          :knowledge-point="knowledgePoint"
          :language="language"
          :knowledge-point-options="knowledgePointOptions"
          :sort-by="sortBy"
          :sort-order="sortOrder"
          :solved-summary="solvedSummary"
          empty-text="暂无公共题目，请等待管理员上架"
          @update:keyword="keyword = $event"
          @update:difficulty="difficulty = $event"
          @update:knowledge-point="knowledgePoint = $event"
          @update:language="language = $event"
          @update:sort-by="sortBy = $event"
          @update:sort-order="sortOrder = $event"
          @update:page="onPageChange"
          @search="reloadList"
          @select="goCoding"
        />
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { practiceApi } from '@/api/practice'
import PracticeProblemList from '@/components/practice/PracticeProblemList.vue'
import type {
  KnowledgePointOptionItem,
  KnowledgePointTagItem,
  PracticeProblemListItem,
  PracticeProblemSortBy,
  PracticeProblemSortOrder,
} from '@/types/practice'
import { encodeTopicSlug } from '@/utils/practice-ui'
import { trackEvent } from '@/utils/tracker'

const router = useRouter()

const tags = ref<KnowledgePointTagItem[]>([])
const solvedSummary = ref<{ solved: number; total: number } | null>(null)
const loadingTags = ref(true)
const tagsExpanded = ref(false)
const tagCollapseLimit = 24

const questions = ref<PracticeProblemListItem[]>([])
const loadingList = ref(true)
const keyword = ref('')
const difficulty = ref('')
const knowledgePoint = ref('')
const language = ref('')
const knowledgePointOptions = ref<KnowledgePointOptionItem[]>([])
const sortBy = ref<PracticeProblemSortBy>('id')
const sortOrder = ref<PracticeProblemSortOrder>('asc')
const page = ref(1)
const total = ref(0)
const pageSize = 20

const visibleTags = computed(() =>
  tagsExpanded.value ? tags.value : tags.value.slice(0, tagCollapseLimit),
)

async function loadTags() {
  loadingTags.value = true
  try {
    const data = await practiceApi.listKnowledgePoints()
    tags.value = data.items
    solvedSummary.value = { solved: data.solved_count, total: data.total_problems }
  } catch {
    tags.value = []
    solvedSummary.value = null
  } finally {
    loadingTags.value = false
  }
}

async function loadList() {
  loadingList.value = true
  try {
    const result = await practiceApi.listProblems({
      page: page.value,
      page_size: pageSize,
      keyword: keyword.value.trim() || undefined,
      difficulty: difficulty.value || undefined,
      knowledge_point: knowledgePoint.value || undefined,
      language: language.value || undefined,
      sort_by: sortBy.value,
      sort_order: sortOrder.value,
    })
    questions.value = result.items
    total.value = result.total
  } catch {
    questions.value = []
    total.value = 0
  } finally {
    loadingList.value = false
  }
}

async function reloadList() {
  page.value = 1
  await loadList()
}

function onPageChange(p: number) {
  page.value = p
  void loadList()
}

const goCoding = (problemId: number) => {
  trackEvent({
    event_name: 'problem_view',
    page: '/student/questions',
    module: 'student',
    detail: `problem=${problemId}`,
  })
  router.push(`/student/coding/${problemId}`)
}

async function loadKnowledgePointOptions() {
  try {
    knowledgePointOptions.value = await practiceApi.listKnowledgePointOptions()
  } catch {
    knowledgePointOptions.value = []
  }
}

onMounted(async () => {
  await Promise.all([loadTags(), loadKnowledgePointOptions(), loadList()])
})
</script>

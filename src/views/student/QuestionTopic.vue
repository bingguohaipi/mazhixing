<template>
  <div class="question-topic min-h-full">
    <div v-if="loadingMeta" class="py-24 text-center text-gray-500">加载中...</div>
    <div v-else-if="!detail" class="py-24 text-center text-gray-500">知识点不存在</div>
    <div v-else class="w-full pb-10">
      <div class="px-3 sm:px-4 pt-3 sm:pt-4">
        <RouterLink
          to="/student/questions"
          class="inline-flex items-center text-sm text-gray-500 hover:text-indigo-600"
        >
          ← 返回题库
        </RouterLink>
      </div>

      <div class="pt-6 px-5 sm:px-8 lg:px-12">
        <div class="max-w-5xl mx-auto">
          <div class="flex flex-col lg:flex-row gap-5 lg:gap-6 items-stretch justify-center">
        <aside class="w-full lg:w-[300px] shrink-0 flex">
          <div
            class="bg-white rounded-xl border border-gray-200 p-5 lg:sticky lg:top-4 flex flex-col w-full min-h-[340px] lg:min-h-[460px]"
          >
            <div class="flex items-start gap-3 mb-4">
              <div
                class="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center text-xl shrink-0"
              >
                📚
              </div>
              <div>
                <h1 class="text-xl font-bold text-gray-900">{{ detail.name }}</h1>
                <p class="text-xs text-gray-500 mt-1">码智星 · {{ detail.problem_count }} 题</p>
              </div>
            </div>
            <button
              type="button"
              class="w-full text-left text-sm text-gray-600 leading-relaxed mb-4 p-3 rounded-lg border border-gray-200 hover:border-indigo-300 hover:bg-indigo-50/30 transition group"
              @click="drawerOpen = true"
            >
              <span class="line-clamp-3">{{ detail.description }}</span>
              <span class="block text-xs text-indigo-600 mt-2 group-hover:underline">点击查看详细说明 →</span>
            </button>
            <button
              type="button"
              class="w-full py-2.5 rounded-lg bg-gray-900 text-white text-sm font-medium hover:bg-gray-800 disabled:opacity-40"
              :disabled="detail.problem_count === 0"
              @click="startPractice"
            >
              ▶ 开始练习
            </button>

            <div class="mt-auto pt-6 border-t border-gray-100">
              <h2 class="text-sm font-semibold text-gray-900 mb-3">进度</h2>
              <div class="flex items-center gap-4">
                <div
                  class="w-16 h-16 rounded-full border-4 border-indigo-100 flex items-center justify-center text-xs text-center text-gray-600 leading-tight"
                >
                  {{ detail.solved_count }}/{{ detail.problem_count }}<br>已解答
                </div>
                <div class="flex-1 text-xs text-gray-500 space-y-1">
                  <div>尝试中 {{ detail.attempting_count }}</div>
                  <div
                    v-for="row in detail.difficulty_progress"
                    :key="row.label"
                    class="flex justify-between"
                  >
                    <span :class="difficultyTextClass(row.label === '简单' ? '简单' : row.label)">
                      {{ row.label }}
                    </span>
                    <span>{{ row.solved }}/{{ row.total }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </aside>

        <div class="w-full lg:flex-1 lg:max-w-2xl min-w-0">
          <PracticeProblemList
            :items="questions"
            :loading="loadingList"
            :page="page"
            :total="total"
            :page-size="pageSize"
            :keyword="keyword"
            :difficulty="difficulty"
            :language="language"
            :sort-by="sortBy"
            :sort-order="sortOrder"
            :show-knowledge-point-filter="false"
            :solved-summary="{ solved: detail.solved_count, total: detail.problem_count }"
            empty-text="该知识点下暂无题目"
            @update:keyword="keyword = $event"
            @update:difficulty="difficulty = $event"
            @update:language="language = $event"
            @update:sort-by="sortBy = $event"
            @update:sort-order="sortOrder = $event"
            @search="reloadList"
            @update:page="onPageChange"
            @select="goCoding"
          />
        </div>
          </div>
        </div>
      </div>
    </div>

    <KnowledgePointDrawer
      :open="drawerOpen"
      :content-markdown="detail?.content_markdown || ''"
      @close="drawerOpen = false"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { practiceApi } from '@/api/practice'
import KnowledgePointDrawer from '@/components/knowledge/KnowledgePointDrawer.vue'
import PracticeProblemList from '@/components/practice/PracticeProblemList.vue'
import type {
  KnowledgePointDetailResponse,
  PracticeProblemListItem,
  PracticeProblemSortBy,
  PracticeProblemSortOrder,
} from '@/types/practice'
import { decodeTopicSlug, difficultyTextClass, encodeTopicSlug, resolveTopicName } from '@/utils/practice-ui'
import { trackEvent } from '@/utils/tracker'

const route = useRoute()
const router = useRouter()

const rawTopicSlug = computed(() => decodeTopicSlug(String(route.params.slug ?? '')))
const topicName = computed(() => resolveTopicName(rawTopicSlug.value))

const detail = ref<KnowledgePointDetailResponse | null>(null)
const questions = ref<PracticeProblemListItem[]>([])
const loadingMeta = ref(true)
const loadingList = ref(true)
const keyword = ref('')
const difficulty = ref('')
const language = ref('')
const sortBy = ref<PracticeProblemSortBy>('id')
const sortOrder = ref<PracticeProblemSortOrder>('asc')
const page = ref(1)
const total = ref(0)
const pageSize = 20
const drawerOpen = ref(false)

async function loadMeta() {
  loadingMeta.value = true
  try {
    detail.value = await practiceApi.getKnowledgePoint(topicName.value)
  } catch {
    detail.value = null
  } finally {
    loadingMeta.value = false
  }
}

async function loadList() {
  if (!detail.value) return
  loadingList.value = true
  try {
    const result = await practiceApi.listProblems({
      page: page.value,
      page_size: pageSize,
      keyword: keyword.value.trim() || undefined,
      difficulty: difficulty.value || undefined,
      language: language.value || undefined,
      knowledge_point: topicName.value,
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

function goCoding(problemId: number) {
  trackEvent({
    event_name: 'problem_view',
    page: route.path,
    module: 'student',
    detail: `topic=${topicName.value}&problem=${problemId}`,
  })
  router.push(`/student/coding/${problemId}`)
}

function startPractice() {
  const id = detail.value?.first_problem_id
  if (id) goCoding(id)
}

function ensureCanonicalTopicRoute(): boolean {
  const raw = rawTopicSlug.value
  const canonical = resolveTopicName(raw)
  if (raw !== canonical) {
    void router.replace(`/student/questions/topic/${encodeTopicSlug(canonical)}`)
    return true
  }
  return false
}

async function bootstrapTopic() {
  if (ensureCanonicalTopicRoute()) return
  page.value = 1
  keyword.value = ''
  difficulty.value = ''
  language.value = ''
  sortBy.value = 'id'
  sortOrder.value = 'asc'
  await loadMeta()
  await loadList()
}

watch(() => route.params.slug, () => {
  void bootstrapTopic()
})

onMounted(async () => {
  await bootstrapTopic()
})
</script>

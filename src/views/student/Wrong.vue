<template>
  <div>
    <div class="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
      <h1 class="text-lg font-semibold text-gray-900">我的错题本</h1>
      <div class="flex items-center gap-2">
        <button
          class="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
          :disabled="loading || items.length === 0"
          @click="handleClearAll"
        >
          清空记录
        </button>
      </div>
    </div>

    <div v-if="loading" class="p-6 text-center text-gray-500">加载中...</div>

    <div v-else class="p-6 space-y-4">
      <div class="grid grid-cols-3 gap-4">
        <div class="bg-white rounded-xl p-5 border border-gray-100 text-center">
          <div class="text-3xl font-bold text-red-500">{{ summary.pending_count }}</div>
          <div class="text-sm text-gray-500 mt-1">待复习错题</div>
        </div>
        <div class="bg-white rounded-xl p-5 border border-gray-100 text-center">
          <div class="text-3xl font-bold text-amber-500">{{ summary.reviewing_count }}</div>
          <div class="text-sm text-gray-500 mt-1">复习中（答对1次）</div>
        </div>
        <div class="bg-white rounded-xl p-5 border border-gray-100 text-center">
          <div class="text-3xl font-bold text-green-500">{{ summary.mastered_count }}</div>
          <div class="text-sm text-gray-500 mt-1">已掌握（连续答对2次）</div>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-gray-100 p-4">
        <div class="flex items-center gap-3 flex-wrap">
          <select v-model="filterStatus" class="px-3 py-2 border border-gray-300 rounded-lg text-sm" @change="loadWrongBook">
            <option value="">全部状态</option>
            <option value="pending">待复习</option>
            <option value="reviewing">复习中</option>
            <option value="mastered">已掌握</option>
          </select>
          <select v-model="filterKnowledge" class="px-3 py-2 border border-gray-300 rounded-lg text-sm" @change="loadWrongBook">
            <option value="">全部知识点</option>
            <option v-for="point in knowledgeOptions" :key="point" :value="point">{{ point }}</option>
          </select>
          <select v-model="sortBy" class="px-3 py-2 border border-gray-300 rounded-lg text-sm" @change="loadWrongBook">
            <option value="error_count">按错误次数</option>
            <option value="last_error">按最近错误</option>
            <option value="difficulty">按难度</option>
          </select>
        </div>
      </div>

      <div v-if="items.length === 0" class="bg-white rounded-xl border border-gray-100 p-12 text-center">
        <div class="text-4xl mb-3">🎉</div>
        <p class="text-gray-500">太棒了，暂无错题</p>
      </div>

      <div v-else class="space-y-3">
        <div v-for="wrong in items" :key="wrong.problem_id" class="surface-dark-card rounded-xl p-5 card-hover">
          <div class="flex items-start justify-between mb-3">
            <div class="flex items-center gap-3">
              <span class="badge" :class="getStatusClass(wrong.review_status)">{{ getStatusLabel(wrong.review_status) }}</span>
              <span class="text-gray-400 text-sm">#{{ wrong.problem_id }}</span>
              <h3 class="font-semibold text-gray-900">{{ wrong.title }}</h3>
            </div>
            <span class="badge bg-yellow-100 text-yellow-700">{{ wrong.difficulty }}</span>
          </div>
          <div class="flex items-center gap-6 text-sm text-gray-500 mb-3">
            <span>错误次数：<span class="text-red-500 font-medium">{{ wrong.error_count }}次</span></span>
            <span>最近错误：{{ formatTime(wrong.last_error_at) }}</span>
            <span>知识点：{{ wrong.knowledge_point || '未分类' }}</span>
          </div>
          <div v-if="wrong.error_reason" class="surface-dark-inset wrong-error-block mb-3">
            <div class="text-xs text-red-600 font-medium mb-1">错误原因</div>
            <div class="text-sm text-gray-700">{{ wrong.error_reason }}</div>
          </div>
          <div v-if="expandedAi === wrong.problem_id && wrong.ai_analysis" class="surface-dark-inset mb-3">
            <div class="text-xs text-indigo-600 font-medium mb-1">AI 解析</div>
            <div class="text-sm text-gray-700 whitespace-pre-wrap">{{ wrong.ai_analysis }}</div>
          </div>
          <div class="flex gap-2 flex-wrap">
            <button class="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700" @click="goRetry(wrong.problem_id)">
              重新做题
            </button>
            <button
              v-if="wrong.ai_analysis"
              class="px-4 py-2 border border-gray-300 text-sm rounded-lg hover:bg-gray-50"
              @click="toggleAi(wrong.problem_id)"
            >
              {{ expandedAi === wrong.problem_id ? '收起解析' : '查看 AI 解析' }}
            </button>
            <button
              class="px-4 py-2 border border-gray-300 text-sm rounded-lg hover:bg-gray-50"
              @click="handleClearOne(wrong.problem_id)"
            >
              移出错题本
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { wrongBookApi } from '@/api/wrong-book'
import { toast } from '@/utils/toast'
import { trackEvent } from '@/utils/tracker'
import type { WrongBookItem, WrongBookSummary, WrongReviewStatus, WrongSortBy } from '@/types/wrong-book'

const router = useRouter()

const loading = ref(true)
const summary = ref<WrongBookSummary>({ pending_count: 0, reviewing_count: 0, mastered_count: 0 })
const items = ref<WrongBookItem[]>([])
const filterStatus = ref<WrongReviewStatus | ''>('')
const filterKnowledge = ref('')
const sortBy = ref<WrongSortBy>('error_count')
const expandedAi = ref<number | null>(null)

const knowledgeOptions = computed(() => {
  const set = new Set<string>()
  items.value.forEach((item) => {
    if (item.knowledge_point) set.add(item.knowledge_point)
  })
  return [...set]
})

const loadWrongBook = async () => {
  loading.value = true
  try {
    const data = await wrongBookApi.list({
      review_status: filterStatus.value,
      knowledge_point: filterKnowledge.value,
      sort_by: sortBy.value,
    })
    summary.value = data.summary
    items.value = data.items
    trackEvent({ event_name: 'wrong_book_view', page: '/student/wrong', module: 'student' })
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '加载错题本失败')
    summary.value = { pending_count: 0, reviewing_count: 0, mastered_count: 0 }
    items.value = []
  } finally {
    loading.value = false
  }
}

const handleClearAll = async () => {
  if (!confirm('确定清空全部错题记录？清空后可从做题记录中重新积累。')) return
  try {
    await wrongBookApi.clear()
    trackEvent({ event_name: 'wrong_book_clear_all', page: '/student/wrong', module: 'student' })
    toast.success('错题记录已清空')
    await loadWrongBook()
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '清空失败')
  }
}

const handleClearOne = async (problemId: number) => {
  if (!confirm('确定将此题移出错题本？')) return
  try {
    await wrongBookApi.clear(problemId)
    trackEvent({ event_name: 'wrong_book_clear_one', page: '/student/wrong', module: 'student', detail: `problem=${problemId}` })
    toast.success('已移出错题本')
    await loadWrongBook()
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '操作失败')
  }
}

const goRetry = (problemId: number) => {
  router.push(`/student/coding/${problemId}`)
}

const toggleAi = (problemId: number) => {
  expandedAi.value = expandedAi.value === problemId ? null : problemId
}

const formatTime = (iso: string) =>
  new Date(iso).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })

const getStatusLabel = (status: WrongReviewStatus) => {
  if (status === 'pending') return '待复习'
  if (status === 'reviewing') return '复习中'
  return '已掌握'
}

const getStatusClass = (status: WrongReviewStatus) => {
  if (status === 'pending') return 'bg-red-100 text-red-700'
  if (status === 'reviewing') return 'bg-amber-100 text-amber-700'
  return 'bg-green-100 text-green-700'
}

onMounted(loadWrongBook)
</script>

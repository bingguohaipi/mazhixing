<template>
  <div>
    <div class="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
      <div class="flex items-center gap-3 min-w-0">
        <button class="text-gray-400 hover:text-gray-600 shrink-0" @click="goBack">← 返回</button>
        <template v-if="problem">
          <h1 class="text-lg font-semibold text-gray-900 truncate">#{{ problem.id }} {{ problem.title }}</h1>
          <span class="badge shrink-0" :class="getDifficultyClass(problem.difficulty)">{{ problem.difficulty }}</span>
          <span v-if="isTeacherPreview" class="badge shrink-0 bg-violet-100 text-violet-700">
            {{ auth.role === 'admin' ? '管理员预览' : '教师预览' }}
          </span>
          <span v-if="isArenaMode" class="badge shrink-0 bg-red-100 text-red-700">擂台模式</span>
        </template>
        <span v-else-if="loading" class="text-gray-500 text-sm">加载中...</span>
      </div>
      <div class="flex items-center gap-2 shrink-0">
        <button
          v-if="problem?.hint"
          class="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
          @click="showHint = !showHint"
        >
          💡 提示
        </button>
        <button
          v-if="hasJudgedResult"
          class="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
          :class="
            canTriggerAi
              ? 'border-indigo-300 text-indigo-600 hover:bg-indigo-50'
              : 'border-gray-300 text-gray-400'
          "
          :disabled="!canTriggerAi || aiLoading"
          :title="aiBlockedReason || undefined"
          @click="handleAiAnalysis"
        >
          {{ aiLoading ? '解析中...' : '🤖 AI解析' }}
        </button>
        <button
          v-if="isArenaMode"
          class="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
          :disabled="submitting || arenaSubmitted"
          @click="handleArenaExit"
        >
          退出擂台
        </button>
        <button
          class="px-4 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
          :disabled="submitting || !code.trim() || arenaSubmitted"
          @click="handleSubmit"
        >
          {{ submitting ? '判题中...' : isArenaMode ? '▶ 提交（唯一一次）' : '▶ 提交' }}
        </button>
      </div>
    </div>

    <div v-if="error" class="px-6 py-2 bg-red-50 text-red-600 text-sm flex items-center justify-between gap-3">
      <span>{{ error }}</span>
      <button
        v-if="canRetrySubmit && !isArenaMode"
        class="px-3 py-1 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 shrink-0"
        @click="handleSubmit"
      >
        重新提交
      </button>
      <button
        v-if="canRetrySubmit && isArenaMode"
        class="px-3 py-1 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 shrink-0"
        @click="retryArenaSubmit"
      >
        再次提交
      </button>
    </div>

    <div class="flex h-[calc(100vh-57px)]">
      <!-- 左侧题目描述 -->
      <div class="w-[58%] min-w-0 border-r border-gray-200 overflow-y-auto scrollbar-thin p-6">
        <div v-if="loading" class="text-center py-16 text-gray-500">加载题目...</div>
        <div v-else-if="problem" class="prose prose-sm max-w-none">
          <div v-if="showHint && problem.hint" class="bg-amber-50 border border-amber-100 rounded-lg p-3 mb-4">
            <p class="text-sm text-amber-800"><strong>提示：</strong>{{ problem.hint }}</p>
          </div>
          <h2 class="text-lg font-bold text-gray-900 mb-3">题目描述</h2>
          <p class="text-gray-700 leading-relaxed mb-4 whitespace-pre-wrap">{{ problem.description }}</p>
          <div v-if="problemImages.length" class="flex flex-wrap gap-3 mb-4">
            <img
              v-for="(url, idx) in problemImages"
              :key="idx"
              :src="url"
              alt="题目插图"
              class="max-w-full max-h-64 rounded-lg border border-gray-200 cursor-pointer object-contain"
              @click="openProblemImage(url)"
            />
          </div>
          <template v-if="problem.input_format">
            <h3 class="font-bold text-gray-900 mb-2">输入格式</h3>
            <p class="text-gray-700 mb-4 whitespace-pre-wrap">{{ problem.input_format }}</p>
          </template>
          <template v-if="problem.output_format">
            <h3 class="font-bold text-gray-900 mb-2">输出格式</h3>
            <p class="text-gray-700 mb-4 whitespace-pre-wrap">{{ problem.output_format }}</p>
          </template>
          <h3 class="font-bold text-gray-900 mb-2">样例输入</h3>
          <pre class="bg-gray-900 text-gray-100 p-3 rounded-lg text-sm mb-2 whitespace-pre-wrap">{{ displaySample(problem.sample_input || sampleCase?.input_data) }}</pre>
          <h3 class="font-bold text-gray-900 mb-2">样例输出</h3>
          <pre class="bg-gray-900 text-gray-100 p-3 rounded-lg text-sm mb-4 whitespace-pre-wrap">{{ displaySample(problem.sample_output || sampleCase?.expected_output) }}</pre>
          <div class="text-xs text-gray-400">时间限制 {{ problem.time_limit_ms }}ms · 内存限制 {{ problem.memory_limit_mb }}MB</div>
          <div v-if="showProblemFeedback" class="mt-8 flex justify-center">
            <button
              type="button"
              class="px-4 py-2 text-sm text-gray-600 rounded-lg border border-gray-200 bg-white hover:bg-gray-50"
              @click="showFeedbackModal = true"
            >
              我要反馈
            </button>
          </div>
        </div>
      </div>

      <!-- 右侧代码编辑器 -->
      <div class="w-[42%] min-w-0 flex flex-col">
        <div class="bg-gray-800 px-4 py-2 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <select
              v-if="allowedLanguages.length > 1 && !isArenaMode"
              v-model="selectedLanguage"
              class="bg-gray-700 text-white text-xs px-2 py-1 rounded border border-gray-600 outline-none cursor-pointer"
            >
              <option v-for="lang in allowedLanguages" :key="lang" :value="lang">{{ lang }}</option>
            </select>
            <span v-else class="text-white text-xs px-2 py-1 rounded bg-gray-700">{{ selectedLanguage }}</span>
            <span class="text-gray-400 text-xs">{{ selectedLanguage === 'Python' ? 'main.py' : 'main.cpp' }}</span>
          </div>
          <div class="flex items-center gap-2 text-xs text-gray-400">
            <span v-if="draftSaved" class="text-green-400">已保存草稿</span>
            <button class="hover:text-white" @click="resetCode">重置</button>
          </div>
        </div>

        <div class="flex-1 min-h-0">
          <CodeEditor
            v-if="!loading"
            :key="`${problemId}-${selectedLanguage}`"
            v-model="code"
            :language="selectedLanguage"
            :highlight-line-numbers="aiHighlightLines"
          />
        </div>

        <!-- 底部结果区 -->
        <div class="border-t border-gray-200 bg-white">
          <div class="flex border-b border-gray-100">
            <button
              class="px-4 py-2 text-sm"
              :class="activeTab === 'result' ? 'font-medium text-indigo-600 border-b-2 border-indigo-600' : 'text-gray-500 hover:text-gray-700'"
              @click="activeTab = 'result'"
            >
              运行结果
            </button>
            <button
              class="px-4 py-2 text-sm"
              :class="activeTab === 'history' ? 'font-medium text-indigo-600 border-b-2 border-indigo-600' : 'text-gray-500 hover:text-gray-700'"
              @click="activeTab = 'history'; loadHistory()"
            >
              提交记录
            </button>
            <button
              class="px-4 py-2 text-sm"
              :class="activeTab === 'ai' ? 'font-medium text-indigo-600 border-b-2 border-indigo-600' : 'text-gray-500 hover:text-gray-700'"
              @click="openAiTab"
            >
              AI 解析
            </button>
          </div>

          <div class="p-4 max-h-48 overflow-y-auto">
            <!-- 运行结果 -->
            <template v-if="activeTab === 'result'">
              <div v-if="submitting || lastResult?.status === 'PENDING'" class="text-sm text-gray-500 text-center py-4">
                判题中，请稍候...
              </div>
              <div v-else-if="!lastResult" class="text-sm text-gray-400 text-center py-4">提交代码后将在此显示判题结果</div>
              <template v-else>
                <div class="flex items-center gap-3 mb-3 flex-wrap">
                  <span class="badge" :class="getStatusBadgeClass(lastResult.status)">{{ getStatusLabel(lastResult.status) }}</span>
                  <span v-if="lastResult.is_late" class="badge bg-amber-100 text-amber-700">补交</span>
                  <span v-if="lastResult.runtime_ms" class="text-sm text-gray-500">用时: {{ lastResult.runtime_ms }}ms</span>
                  <span
                    v-if="lastResult.points_awarded && !isTeacherPreview"
                    class="text-sm font-medium text-green-600"
                  >
                    🎉 首次通过，+{{ lastResult.points_awarded }} 积分
                  </span>
                </div>

                <div v-if="lastResult.status === 'CE' && lastResult.compile_output" class="mb-3">
                  <pre class="bg-orange-50 text-orange-800 p-3 rounded-lg text-xs overflow-x-auto whitespace-pre-wrap">{{ lastResult.compile_output }}</pre>
                </div>

                <div v-if="lastResult.error_message" class="mb-3 text-sm text-red-600">{{ lastResult.error_message }}</div>

                <div v-if="lastResult.case_results.length" class="grid grid-cols-5 gap-2">
                  <div
                    v-for="c in lastResult.case_results"
                    :key="c.case_index"
                    class="text-center p-2 rounded"
                    :class="getCaseBgClass(c.status)"
                  >
                    <div class="text-xs text-gray-500">用例{{ c.case_index + 1 }}</div>
                    <div class="text-sm font-medium" :class="getCaseTextClass(c.status)">{{ getCaseIcon(c.status) }}</div>
                    <div v-if="c.is_sample && c.actual_output" class="text-xs text-gray-400 mt-1 truncate" :title="c.actual_output">输出: {{ c.actual_output }}</div>
                  </div>
                </div>
              </template>
            </template>

            <!-- 提交记录 -->
            <template v-else-if="activeTab === 'history'">
              <div v-if="historyLoading" class="text-sm text-gray-400 text-center py-4">加载中...</div>
              <div v-else-if="history.length === 0" class="text-sm text-gray-400 text-center py-4">还没有提交记录</div>
              <div v-else class="space-y-2">
                <div
                  v-for="item in history"
                  :key="item.id"
                  class="flex items-center justify-between text-sm p-2 rounded-lg hover:bg-gray-50 cursor-pointer"
                  @click="loadSubmissionDetail(item.id)"
                >
                  <div class="flex items-center gap-2">
                    <span class="badge text-xs" :class="getStatusBadgeClass(item.status)">{{ item.status }}</span>
                    <span class="text-gray-500">{{ formatTime(item.created_at) }}</span>
                    <span v-if="item.is_late" class="text-xs text-amber-600">补交</span>
                  </div>
                  <span class="text-gray-400">{{ item.runtime_ms ? `${item.runtime_ms}ms` : '-' }}</span>
                </div>
              </div>
            </template>

            <!-- AI 解析 -->
            <template v-else-if="activeTab === 'ai'">
              <div v-if="!hasJudgedResult" class="text-sm text-gray-400 text-center py-4">
                请先提交代码并等待判题完成
              </div>
              <div v-else-if="!canTriggerAi" class="text-sm text-gray-500 text-center py-4 leading-relaxed">
                {{ aiBlockedReason }}
              </div>
              <div v-else-if="aiLoading" class="text-sm text-gray-500 text-center py-4">AI 正在分析中...</div>
              <div v-else-if="aiContent.trim()" class="space-y-3">
                <div
                  v-if="aiHighlightLines.length > 0"
                  class="text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2"
                >
                  重点关注第 {{ aiHighlightLines.join('、') }} 行（已在编辑器高亮）
                </div>
                <div class="text-sm text-gray-700 ai-analysis-body whitespace-pre-wrap leading-relaxed">{{ aiContent }}</div>
              </div>
              <div v-else class="text-center py-4">
                <p class="text-sm text-gray-500 mb-3">
                  {{ aiFetchFailed ? '解析未成功展示，可重试（已成功解析的提交不会重复扣次）' : '点击下方按钮获取 AI 错题解析' }}
                </p>
                <button
                  class="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                  :disabled="aiLoading"
                  @click="handleAiAnalysis"
                >
                  🤖 {{ aiLoading ? '解析中...' : '开始 AI 解析' }}
                </button>
              </div>
              <div v-if="aiRemaining !== null" class="text-xs text-gray-400 mt-3 text-right">
                今日剩余 {{ aiRemaining }} 次
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>
    <ProblemFeedbackModal
      v-if="showFeedbackModal && problem"
      :problem-id="problemId"
      :problem-title="problem.title"
      @close="showFeedbackModal = false"
    />
    <ImageLightbox :src="problemPreviewSrc" @close="problemPreviewSrc = null" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { usePageDwell } from '@/composables/usePageDwell'
import { useRoute, useRouter } from 'vue-router'
import CodeEditor from '@/components/CodeEditor.vue'
import ImageLightbox from '@/components/ImageLightbox.vue'
import ProblemFeedbackModal from '@/components/ProblemFeedbackModal.vue'
import { arenaApi } from '@/api/arena'
import { practiceApi } from '@/api/practice'
import { submissionApi } from '@/api/submission'
import { useAuthStore } from '@/stores/auth'
import { usePetStore } from '@/stores/pet'
import type { PracticeProblemDetail } from '@/types/practice'
import type { SubmissionDetail, SubmissionListItem, SubmissionStatus } from '@/types/submission'
import {
  clearDraft,
  draftForLanguage,
  getDefaultCode,
  loadDraft,
  migrateLegacyDraft,
  saveDraft,
} from '@/utils/draft'
import { pickInitialCodingLanguage, resolveProblemLanguages } from '@/utils/problem-languages'
import type { ProblemLanguage } from '@/types/problem'
import { validateSubmissionCodeClient } from '@/utils/submission-code'
import { displayIoSample } from '@/utils/io-sample'
import { toast } from '@/utils/toast'
import { trackError, trackEvent } from '@/utils/tracker'
import { formatShanghaiDateTime } from '@/utils/datetime'

const displaySample = (text: string | null | undefined) => displayIoSample(text)

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const petStore = usePetStore()

const problemId = computed(() => Number(route.params.problemId))
const homeworkId = computed(() => {
  const raw = route.query.homeworkId
  return raw ? Number(raw) : null
})

const arenaSessionId = computed(() => {
  const raw = route.query.arenaSessionId
  return raw ? Number(raw) : null
})

const isStaffPreview = computed(() => auth.role === 'teacher' || auth.role === 'admin')
const isTeacherPreview = isStaffPreview

const showProblemFeedback = computed(() => {
  if (!isTeacherPreview.value) return true
  return Boolean(problem.value?.is_public_catalog)
})
const isArenaMode = computed(() => !isTeacherPreview.value && arenaSessionId.value != null && !homeworkId.value)
const arenaSubmitted = ref(false)
const codingPage = computed(() => (isTeacherPreview.value ? '/teacher/coding' : '/student/coding'))
const codingModule = computed(() => (isTeacherPreview.value ? 'teacher' : 'student'))

const problem = ref<PracticeProblemDetail | null>(null)
const allowedLanguages = computed((): ProblemLanguage[] => {
  if (!problem.value) return ['Python', 'C++']
  return resolveProblemLanguages(problem.value.languages, problem.value.language)
})
const loading = ref(true)
const error = ref('')
const canRetrySubmit = ref(false)
const code = ref('')
const selectedLanguage = ref<'Python' | 'C++'>('Python')
const submitting = ref(false)
const lastResult = ref<SubmissionDetail | null>(null)
const activeTab = ref<'result' | 'history' | 'ai'>('result')
const history = ref<SubmissionListItem[]>([])
const historyLoading = ref(false)
const showHint = ref(false)
const draftSaved = ref(false)
const aiLoading = ref(false)
const aiContent = ref('')
const aiHighlightLines = ref<number[]>([])
const aiRemaining = ref<number | null>(null)
const aiFetchFailed = ref(false)
const showFeedbackModal = ref(false)

let draftTimer: ReturnType<typeof setTimeout> | null = null
const codingStartedAt = ref(Date.now())
const draftSaveTracked = ref(false)

usePageDwell('coding_dwell', codingPage.value, codingModule.value)

const sampleCase = computed(() => problem.value?.test_cases.find((tc) => tc.is_sample))

const hasJudgedResult = computed(() => {
  const status = lastResult.value?.status
  return Boolean(status && status !== 'PENDING')
})

/** 仅答案错误 / 运行异常可调用 AI（与后端一致） */
const canTriggerAi = computed(() => {
  const status = lastResult.value?.status
  return status === 'WA' || status === 'RE'
})

const aiBlockedReason = computed((): string => {
  const status = lastResult.value?.status
  if (!status || status === 'PENDING') {
    return '请先提交代码并等待判题完成'
  }
  if (status === 'AC') {
    return '本题已通过，无需 AI 错题解析'
  }
  if (status === 'CE') {
    return '当前为编译错误（CE）：请先根据上方编译信息改到能运行。AI 解析仅支持「答案错误 WA」和「运行异常 RE」'
  }
  if (status === 'TLE') {
    return '当前为运行超时（TLE）：请优化逻辑或复杂度。AI 解析仅支持 WA / RE'
  }
  if (status === 'WA' || status === 'RE') {
    return ''
  }
  return '仅 WA / RE 可触发 AI 解析'
})

watch(lastResult, (result) => {
  if (result?.ai_analysis) {
    aiContent.value = result.ai_analysis
    aiHighlightLines.value = result.ai_highlight_lines ?? []
  } else if (!result || (result.status !== 'WA' && result.status !== 'RE')) {
    aiContent.value = ''
    aiRemaining.value = null
  }
})

const mediaUrl = (url: string) => {
  if (url.startsWith('http') || url.startsWith('blob:')) return url
  const base = import.meta.env.VITE_API_BASE ?? ''
  return `${base}${url.startsWith('/') ? url : `/${url}`}`
}

const problemPreviewSrc = ref<string | null>(null)
const problemImages = computed(() =>
  (problem.value?.image_urls ?? []).map((u) => mediaUrl(u)),
)
const openProblemImage = (url: string) => {
  problemPreviewSrc.value = url
}

const goBack = () => {
  if (auth.role === 'admin') {
    router.push('/admin/public-problems')
    return
  }
  if (isTeacherPreview.value) {
    router.push('/teacher/questions')
    return
  }
  if (isArenaMode.value) {
    router.push(`/student/arena/problems/${problemId.value}`)
    return
  }
  if (homeworkId.value) {
    router.push(`/student/homework/${homeworkId.value}`)
  } else {
    router.push('/student/questions')
  }
}

const handleArenaExit = async () => {
  if (!arenaSessionId.value) return
  if (!window.confirm('退出后本次不计成绩，确定退出擂台？')) return
  try {
    await arenaApi.exitSession(arenaSessionId.value)
    router.push(`/student/arena/problems/${problemId.value}`)
  } catch (err) {
    error.value = err instanceof Error ? err.message : '退出失败'
  }
}

const loadProblem = async () => {
  loading.value = true
  error.value = ''
  try {
    problem.value = await practiceApi.getProblem(problemId.value)
    const langs = resolveProblemLanguages(problem.value.languages, problem.value.language)
    const classDefault =
      !isTeacherPreview.value && auth.user?.role === 'student'
        ? auth.user.default_coding_language ?? null
        : null
    selectedLanguage.value = pickInitialCodingLanguage(langs, {
      queryLang: route.query.lang,
      classDefault,
    })
    codingStartedAt.value = Date.now()
    trackEvent({
      event_name: 'problem_open',
      page: codingPage.value,
      module: codingModule.value,
      detail: `problem=${problemId.value}`,
    })
    initCode()
    await loadHistory()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载失败'
  } finally {
    loading.value = false
  }
}

const applyEditorForLanguage = (lang: ProblemLanguage) => {
  const userId = auth.user?.id
  if (!userId || !problem.value) return
  migrateLegacyDraft(userId, problemId.value, lang)
  const saved = draftForLanguage(loadDraft(userId, problemId.value, lang), lang)
  code.value = saved ?? getDefaultCode(lang)
}

const initCode = () => {
  applyEditorForLanguage(selectedLanguage.value)
}

const flushDraftTimer = () => {
  if (draftTimer) {
    clearTimeout(draftTimer)
    draftTimer = null
  }
}

const persistDraft = () => {
  const userId = auth.user?.id
  if (!userId) return
  saveDraft(userId, problemId.value, selectedLanguage.value, code.value)
  if (!draftSaveTracked.value) {
    draftSaveTracked.value = true
    trackEvent({
      event_name: 'draft_save',
      page: '/student/coding',
      module: 'student',
      detail: `problem=${problemId.value}`,
    })
  }
  draftSaved.value = true
  setTimeout(() => { draftSaved.value = false }, 1500)
}

watch(code, () => {
  if (draftTimer) clearTimeout(draftTimer)
  draftTimer = setTimeout(persistDraft, 500)
})

watch(selectedLanguage, (lang, prev) => {
  if (prev === undefined || lang === prev || !problem.value) return
  const userId = auth.user?.id
  if (!userId) return
  flushDraftTimer()
  saveDraft(userId, problemId.value, prev, code.value)
  applyEditorForLanguage(lang)
})

const resetCode = () => {
  if (!confirm('确定重置代码？草稿将被清除。')) return
  const userId = auth.user?.id
  if (userId) clearDraft(userId, problemId.value, selectedLanguage.value)
  trackEvent({
    event_name: 'draft_clear',
    page: '/student/coding',
    module: 'student',
    detail: `problem=${problemId.value}`,
  })
  code.value = getDefaultCode(selectedLanguage.value)
}

const retryArenaSubmit = () => {
  void handleSubmit()
}

const handleSubmit = async () => {
  const validationError = validateSubmissionCodeClient(code.value, selectedLanguage.value)
  if (validationError) {
    error.value = validationError
    canRetrySubmit.value = false
    return
  }
  submitting.value = true
  error.value = ''
  canRetrySubmit.value = false
  activeTab.value = 'result'
  try {
    if (isArenaMode.value && arenaSessionId.value) {
      const arenaRes = await arenaApi.submitSession(arenaSessionId.value, code.value)
      arenaSubmitted.value = true
      lastResult.value = await submissionApi.poll(arenaRes.submission_id)
      const lang = selectedLanguage.value
      trackEvent({
        event_name: 'code_submit',
        page: '/student/coding',
        module: 'student',
        detail: `problem=${problemId.value},status=${lastResult.value.status},arena=1`,
      })
      if (lastResult.value.status === 'AC') {
        await router.push({
          path: `/student/arena/problems/${problemId.value}`,
          query: { lang, submitted: 'AC' },
        })
        return
      }
      toast.info('未通过全部测例，不计入擂台榜；可在运行结果中查看详情')
    } else {
      lastResult.value = await submissionApi.submit({
        problem_id: problemId.value,
        homework_id: homeworkId.value,
        code: code.value,
        language: selectedLanguage.value,
      })
    }
    aiContent.value = ''
    aiHighlightLines.value = []
    aiRemaining.value = null
    aiFetchFailed.value = false
    syncAiFromLastResult()
    const codingSeconds = Math.round((Date.now() - codingStartedAt.value) / 1000)
    trackEvent({
      event_name: 'code_submit',
      page: '/student/coding',
      module: 'student',
      detail: `problem=${problemId.value},status=${lastResult.value.status},seconds=${codingSeconds}`,
    })
    trackEvent({
      event_name: 'problem_solve_duration',
      page: '/student/coding',
      module: 'student',
      detail: `problem=${problemId.value},seconds=${codingSeconds},status=${lastResult.value.status}`,
    })
    aiHighlightLines.value = lastResult.value.ai_highlight_lines ?? []
    if (lastResult.value.status === 'TLE') {
      trackEvent({ event_name: 'judge_timeout', page: '/student/coding', module: 'student', detail: `problem=${problemId.value}` })
    } else if (lastResult.value.status !== 'AC') {
      trackEvent({ event_name: 'judge_fail', page: '/student/coding', module: 'student', detail: `status=${lastResult.value.status}` })
    }
    await loadHistory()
    if (canTriggerAi.value) {
      toast.info('判题完成，可点击「AI 解析」查看错题提示')
    }
    if (lastResult.value.points_awarded && !isTeacherPreview.value) {
      toast.success(`首次通过，+${lastResult.value.points_awarded} 积分！`)
      if (lastResult.value.points_balance != null) {
        petStore.setPointsBalance(lastResult.value.points_balance)
      } else {
        void petStore.refreshPoints()
      }
    }
  } catch (err) {
    const msg = err instanceof Error ? err.message : '提交失败，已为你保存草稿，网络恢复后可重新提交'
    error.value = msg
    canRetrySubmit.value = true
    if (isArenaMode.value && msg.includes('请勿重复提交')) {
      arenaSubmitted.value = true
      canRetrySubmit.value = false
    }
    const detail = err instanceof Error ? err.message : 'unknown'
    trackEvent({
      event_name: 'code_submit_fail',
      page: '/student/coding',
      module: 'student',
      detail,
    })
    trackError('code_submit_fail', detail, '/student/coding')
  } finally {
    submitting.value = false
  }
}

const loadHistory = async () => {
  historyLoading.value = true
  try {
    history.value = await submissionApi.list(problemId.value, homeworkId.value)
  } catch {
    history.value = []
  } finally {
    historyLoading.value = false
  }
}

const loadSubmissionDetail = async (submissionId: number) => {
  try {
    lastResult.value = await submissionApi.get(submissionId)
    syncAiFromLastResult()
    activeTab.value = 'result'
  } catch {
    /* ignore */
  }
}

function syncAiFromLastResult() {
  const analysis = lastResult.value?.ai_analysis?.trim()
  if (!analysis) return
  aiContent.value = lastResult.value!.ai_analysis ?? ''
  aiHighlightLines.value = lastResult.value!.ai_highlight_lines ?? []
  aiFetchFailed.value = false
}

function openAiTab() {
  activeTab.value = 'ai'
  syncAiFromLastResult()
}

const handleAiAnalysis = async () => {
  if (!lastResult.value || !canTriggerAi.value || aiLoading.value) return
  activeTab.value = 'ai'
  syncAiFromLastResult()
  if (aiContent.value.trim()) return

  aiLoading.value = true
  aiFetchFailed.value = false
  error.value = ''
  const submissionId = lastResult.value.id
  try {
    const result = await submissionApi.analyzeAi(submissionId)
    aiRemaining.value = result.remaining_today
    if (!result.content.trim()) {
      aiFetchFailed.value = true
      toast.info('解析完成但内容为空，请稍后重试')
      return
    }
    aiContent.value = result.content
    aiHighlightLines.value = result.highlight_lines ?? []
    lastResult.value = {
      ...lastResult.value,
      ai_analysis: result.content,
      ai_highlight_lines: result.highlight_lines ?? [],
    }
    trackEvent({
      event_name: 'ai_analysis_view',
      page: codingPage.value,
      module: codingModule.value,
      detail: `submission=${submissionId}`,
    })
  } catch (err) {
    const detail = err instanceof Error ? err.message : '解析暂时失败，请稍后刷新重试'
    aiFetchFailed.value = true
    error.value = detail
    toast.error(detail)
    trackError('ai_analysis_fail', detail, codingPage.value)
  } finally {
    aiLoading.value = false
  }
}

const formatTime = (iso: string) => formatShanghaiDateTime(iso)

const getDifficultyClass = (d: string) => {
  if (d === '入门') return 'bg-green-100 text-green-700'
  if (d === '简单') return 'bg-yellow-100 text-yellow-700'
  if (d === '中等') return 'bg-orange-100 text-orange-700'
  return 'bg-red-100 text-red-700'
}

const getStatusLabel = (status: SubmissionStatus) => {
  const map: Record<SubmissionStatus, string> = {
    AC: '✓ 通过',
    WA: '✗ 答案错误',
    CE: '⚠ 编译错误',
    TLE: '⏱ 运行超时',
    RE: '✗ 运行异常',
    PENDING: '判题中',
  }
  return map[status] ?? status
}

const getStatusBadgeClass = (status: SubmissionStatus) => {
  if (status === 'AC') return 'bg-green-100 text-green-700'
  if (status === 'CE') return 'bg-orange-100 text-orange-700'
  if (status === 'TLE') return 'bg-gray-100 text-gray-600'
  return 'bg-red-100 text-red-700'
}

const getCaseIcon = (status: SubmissionStatus) => {
  if (status === 'AC') return '✓'
  if (status === 'TLE') return '⏱'
  return '✗'
}

const getCaseBgClass = (status: SubmissionStatus) => {
  if (status === 'AC') return 'bg-green-50'
  if (status === 'TLE') return 'bg-gray-50'
  return 'bg-red-50'
}

const getCaseTextClass = (status: SubmissionStatus) => {
  if (status === 'AC') return 'text-green-600'
  if (status === 'TLE') return 'text-gray-500'
  return 'text-red-600'
}

onMounted(loadProblem)
</script>

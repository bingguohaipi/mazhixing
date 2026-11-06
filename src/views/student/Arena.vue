<template>
  <div>
    <div class="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between flex-wrap gap-3">
      <div>
        <h1 class="text-lg font-semibold text-gray-900">擂台</h1>
        <p class="text-sm text-gray-500 mt-0.5">与公共题库同一套题，挑战时在编辑器中选择语言</p>
      </div>
      <div class="flex items-center gap-2 text-sm">
        <span v-if="overview?.unread_notifications" class="text-indigo-600">
          通知 {{ overview.unread_notifications }} 条未读
        </span>
        <button class="px-3 py-1.5 border border-gray-300 rounded-lg hover:bg-gray-50" @click="showNotifications = true">
          消息
        </button>
      </div>
    </div>

    <div v-if="overview?.active_session" class="mx-6 mt-4 bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-center justify-between">
      <span class="text-sm text-amber-900">
        进行中的擂台：题目 #{{ overview.active_session.problem_id }}（{{ overview.active_session.language }}）
      </span>
      <button
        class="px-3 py-1.5 text-sm bg-amber-600 text-white rounded-lg"
        @click="continueSession(overview.active_session)"
      >
        继续挑战
      </button>
    </div>

    <div class="p-6 space-y-4">
      <div class="flex gap-1 border-b border-gray-200">
        <button
          type="button"
          class="px-4 py-2 text-sm font-medium border-b-2 -mb-px transition"
          :class="mainTab === 'problems' ? 'border-indigo-600 text-indigo-700' : 'border-transparent text-gray-500 hover:text-gray-800'"
          @click="switchTab('problems')"
        >
          题目
        </button>
        <button
          type="button"
          class="px-4 py-2 text-sm font-medium border-b-2 -mb-px transition"
          :class="mainTab === 'leaderboard' ? 'border-indigo-600 text-indigo-700' : 'border-transparent text-gray-500 hover:text-gray-800'"
          @click="switchTab('leaderboard')"
        >
          全站总榜
        </button>
      </div>

      <template v-if="mainTab === 'leaderboard'">
        <div class="flex items-center gap-2 flex-wrap">
          <span class="text-sm text-gray-500">赛道：</span>
          <button
            v-for="lang in ARENA_LANGUAGES"
            :key="lang"
            type="button"
            class="px-3 py-1 text-sm rounded-lg border transition"
            :class="
              leaderboardLanguage === lang
                ? 'border-indigo-600 bg-indigo-50 text-indigo-800'
                : 'border-gray-200 text-gray-600 hover:border-gray-300'
            "
            @click="pickLeaderboardLanguage(lang)"
          >
            {{ lang }}
          </button>
        </div>
        <p class="text-sm text-gray-500">
          {{ leaderboardLanguage }} 赛道 · 参与 {{ globalBoard?.total_participants ?? 0 }} 人
          · 通过题数优先，相同再比综合分与总耗时（综合分：通过题数 40% + 正确率 42% + 相对耗时 18%）
        </p>
        <div v-if="globalLoading" class="text-center py-16 text-gray-500">加载中...</div>
        <div v-else class="bg-white rounded-xl border overflow-hidden">
          <table class="w-full text-sm">
            <thead class="bg-gray-50 text-gray-500">
              <tr class="text-left">
                <th class="px-4 py-3">排名</th>
                <th class="px-4 py-3">姓名</th>
                <th class="px-4 py-3">通过题数</th>
                <th class="px-4 py-3">正确率</th>
                <th class="px-4 py-3">总耗时</th>
                <th class="px-4 py-3">综合分</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr
                v-for="e in globalBoard?.entries ?? []"
                :key="e.user_id"
                :class="e.is_me ? 'arena-board-row-me bg-indigo-50' : ''"
              >
                <td class="px-4 py-3">{{ e.rank }}</td>
                <td class="px-4 py-3 font-medium">
                  {{ e.display_name }}
                  <span v-if="e.student_no_suffix" class="arena-board-row-me-suffix text-xs">({{ e.student_no_suffix }})</span>
                </td>
                <td class="px-4 py-3">{{ e.problems_passed }}</td>
                <td class="px-4 py-3">{{ e.accuracy_rate }}%（{{ e.ac_count }}/{{ e.attempt_count }}）</td>
                <td class="px-4 py-3">{{ formatMs(e.total_duration_ms) }}</td>
                <td class="px-4 py-3">{{ e.composite_score }}</td>
              </tr>
            </tbody>
          </table>
          <div v-if="!globalBoard?.entries.length" class="py-12 text-center text-gray-500">暂无总榜数据，完成挑战后即可上榜</div>
        </div>
        <p v-if="globalBoard?.my_entry && !globalBoard.entries.some((x) => x.is_me)" class="text-sm text-gray-600">
          我的名次：第 {{ globalBoard.my_entry.rank }} 名 · 通过 {{ globalBoard.my_entry.problems_passed }} 题
        </p>
      </template>

      <template v-else>
      <div class="flex items-center gap-3 flex-wrap">
        <input
          v-model="keyword"
          type="search"
          placeholder="搜索题目"
          class="input-light-bg px-3 py-2 border border-gray-300 rounded-lg text-sm w-48"
        />
        <select v-model="difficulty" class="px-3 py-2 border border-gray-300 rounded-lg text-sm" @change="load(1)">
          <option value="">全部难度</option>
          <option value="入门">入门</option>
          <option value="简单">简单</option>
          <option value="中等">中等</option>
          <option value="困难">困难</option>
        </select>
      </div>

      <div v-if="loading" class="text-center py-16 text-gray-500">加载中...</div>
      <div v-else-if="problems.length === 0" class="text-center py-16 text-gray-500">
        {{ hasListQuery ? PROBLEM_FILTER_EMPTY_MESSAGE : '暂无公共题目，请等待管理员上架' }}
      </div>
      <div v-else class="grid gap-3">
        <div
          v-for="p in problems"
          :key="p.id"
          class="bg-white border border-gray-100 rounded-xl p-4 flex items-center justify-between hover:border-indigo-200"
        >
          <div>
            <div class="font-medium text-gray-900">#{{ p.id }} {{ p.title }}</div>
            <div class="text-xs text-gray-500 mt-1">
              {{ p.difficulty }}
              <span v-if="problemLanguages(p).length"> · {{ problemLanguages(p).join(' / ') }}</span>
              <span v-if="p.champion_name"> · 榜主 {{ p.champion_name }}（{{ p.champion_score }} 分）</span>
            </div>
          </div>
          <button
            type="button"
            class="px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            :disabled="challengingId === p.id"
            @click="startChallenge(p)"
          >
            {{ challengingId === p.id ? '准备中...' : '挑战' }}
          </button>
        </div>
      </div>
      </template>
    </div>

    <div v-if="showAgreement" class="modal-mask">
      <div class="modal-card max-w-md">
        <h3 class="modal-title">擂台规则</h3>
        <p class="text-sm text-gray-600 leading-relaxed">
          题目与公共题库一致；每次挑战仅可提交一次代码；成绩全站排名并展示真实姓名；
          请独立作答，抄袭或粘贴他人/AI 代码可能被判无效并需人工审核。
        </p>
        <div class="flex justify-end gap-2 mt-6">
          <button class="px-4 py-2 text-sm border rounded-lg" @click="$router.push('/student/dashboard')">暂不参与</button>
          <button class="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg" @click="acceptAgreement">同意并继续</button>
        </div>
      </div>
    </div>

    <div v-if="showNotifications" class="modal-mask" @click.self="showNotifications = false">
      <div class="modal-card max-w-lg max-h-[80vh] overflow-y-auto">
        <h3 class="modal-title">擂台通知</h3>
        <div v-if="notifications.length === 0" class="text-sm text-gray-500 py-6 text-center">暂无通知</div>
        <ul v-else class="space-y-3">
          <li v-for="n in notifications" :key="n.id" class="text-sm border-b border-gray-100 pb-2">
            <div class="font-medium">{{ n.title }}</div>
            <div class="text-gray-600 mt-1">{{ n.body }}</div>
          </li>
        </ul>
        <button class="mt-4 text-sm text-indigo-600" @click="closeNotifications">全部标为已读并关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useDebouncedWatch } from '@/composables/useDebouncedWatch'
import { useRoute, useRouter } from 'vue-router'
import { arenaApi } from '@/api/arena'
import type {
  ArenaGlobalLeaderboardResponse,
  ArenaOverviewResponse,
  ArenaProblemListItem,
  ArenaSessionBrief,
  ArenaNotificationItem,
} from '@/types/arena'
import {
  ARENA_LANGUAGES,
  getStoredArenaLanguage,
  setStoredArenaLanguage,
  type ArenaLanguage,
} from '@/utils/arena-language'
import {
  hasProblemCatalogQuery,
  PROBLEM_FILTER_EMPTY_MESSAGE,
} from '@/constants/problem-catalog'
import { toast } from '@/utils/toast'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const route = useRoute()
type ArenaMainTab = 'problems' | 'leaderboard'
const mainTab = ref<ArenaMainTab>(route.query.tab === 'leaderboard' ? 'leaderboard' : 'problems')
const globalBoard = ref<ArenaGlobalLeaderboardResponse | null>(null)
const globalLoading = ref(false)
const overview = ref<ArenaOverviewResponse | null>(null)
const problems = ref<ArenaProblemListItem[]>([])
const loading = ref(false)
const keyword = ref('')
const difficulty = ref('')
const leaderboardLanguage = ref<ArenaLanguage>(
  getStoredArenaLanguage() ?? auth.user?.default_coding_language ?? 'Python',
)
const showAgreement = ref(false)
const showNotifications = ref(false)
const notifications = ref<ArenaNotificationItem[]>([])
const challengingId = ref<number | null>(null)
const pendingChallengeProblem = ref<ArenaProblemListItem | null>(null)

const hasListQuery = computed(() =>
  hasProblemCatalogQuery({
    keyword: keyword.value,
    difficulty: difficulty.value,
  }),
)

const loadOverview = async () => {
  overview.value = await arenaApi.getOverview()
}

const formatMs = (ms: number): string => {
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

const problemLanguages = (p: ArenaProblemListItem): string[] => {
  if (p.languages?.length) return p.languages
  return p.language ? [p.language] : []
}

const resolveChallengeLanguage = (p: ArenaProblemListItem): ArenaLanguage => {
  const langs = problemLanguages(p)
  const classDefault = auth.user?.default_coding_language
  if (classDefault && langs.includes(classDefault)) return classDefault
  const stored = getStoredArenaLanguage()
  if (stored && langs.includes(stored)) return stored
  if (langs[0] === 'Python' || langs[0] === 'C++') return langs[0]
  return 'Python'
}

const loadGlobalBoard = async () => {
  globalLoading.value = true
  try {
    globalBoard.value = await arenaApi.getGlobalLeaderboard(leaderboardLanguage.value)
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '总榜加载失败')
  } finally {
    globalLoading.value = false
  }
}

const switchTab = (tab: ArenaMainTab) => {
  mainTab.value = tab
  void router.replace({
    path: '/student/arena',
    query: tab === 'leaderboard' ? { tab: 'leaderboard' } : {},
  })
  if (tab === 'leaderboard') {
    void loadGlobalBoard()
  }
}

useDebouncedWatch(keyword, () => {
  void load(1)
})

const load = async (page = 1) => {
  loading.value = true
  try {
    await loadOverview()
    const list = await arenaApi.listProblems({
      page,
      keyword: keyword.value.trim() || undefined,
      difficulty: difficulty.value || undefined,
    })
    problems.value = list.items
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '加载失败')
  } finally {
    loading.value = false
  }
}

const pickLeaderboardLanguage = (lang: ArenaLanguage) => {
  leaderboardLanguage.value = lang
  setStoredArenaLanguage(lang)
  void loadGlobalBoard()
}

const acceptAgreement = async () => {
  try {
    await arenaApi.agreeTerms()
    showAgreement.value = false
    const pending = pendingChallengeProblem.value
    pendingChallengeProblem.value = null
    if (pending != null) {
      await startChallenge(pending)
    }
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '操作失败')
  }
}

const startChallenge = async (problem: ArenaProblemListItem) => {
  const problemId = problem.id
  const lang = resolveChallengeLanguage(problem)
  setStoredArenaLanguage(lang)

  const active = overview.value?.active_session
  if (active?.problem_id === problemId && active.language === lang) {
    continueSession(active)
    return
  }
  if (active != null) {
    toast.error('你有进行中的擂台，请先继续或退出后再挑战新题')
    return
  }

  challengingId.value = problemId
  try {
    await arenaApi.agreeTerms().catch(() => {
      /* 已同意则忽略 */
    })
    const session = await arenaApi.createSession(problemId, lang)
    await router.push({
      path: `/student/coding/${problemId}`,
      query: { arenaSessionId: String(session.id) },
    })
  } catch (err) {
    const msg = err instanceof Error ? err.message : '无法开始挑战'
    if (msg.includes('擂台规则')) {
      pendingChallengeProblem.value = problem
      showAgreement.value = true
      return
    }
    if (msg.includes('进行中的擂台')) {
      await loadOverview()
      const again = overview.value?.active_session
      if (again?.problem_id === problemId) {
        continueSession(again)
        return
      }
    }
    toast.error(msg)
  } finally {
    challengingId.value = null
  }
}

const continueSession = (session: ArenaSessionBrief) => {
  if (session.language === 'Python' || session.language === 'C++') {
    setStoredArenaLanguage(session.language)
  }
  router.push({
    path: `/student/coding/${session.problem_id}`,
    query: { arenaSessionId: String(session.id) },
  })
}

const closeNotifications = async () => {
  await arenaApi.markNotificationsRead(true)
  showNotifications.value = false
  if (overview.value) overview.value.unread_notifications = 0
}

onMounted(async () => {
  try {
    if (mainTab.value === 'leaderboard') {
      await loadGlobalBoard()
    } else {
      await load(1)
    }
    const notes = await arenaApi.listNotifications(1)
    notifications.value = notes.items
  } catch (err) {
    const msg = err instanceof Error ? err.message : ''
    if (msg.includes('擂台规则')) {
      showAgreement.value = true
    }
  }
})
</script>

<template>
  <div>
    <div class="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-3">
      <RouterLink :to="backLink" class="text-gray-400 hover:text-gray-600">← 擂台</RouterLink>
      <h1 class="text-lg font-semibold text-gray-900">#{{ problemId }} 全站榜</h1>
      <span v-if="language" class="text-xs px-2 py-0.5 rounded bg-indigo-100 text-indigo-800">{{ language }}</span>
      <RouterLink
        :to="{ path: '/student/arena', query: { tab: 'leaderboard' } }"
        class="ml-auto text-sm text-indigo-600 hover:text-indigo-800"
      >
        全站总榜
      </RouterLink>
    </div>

    <div v-if="loading" class="p-6 text-center text-gray-500">加载中...</div>
    <div v-else class="p-6 space-y-6">
      <div
        v-if="justSubmittedStatus"
        class="rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-3 text-sm text-indigo-900"
      >
        本次提交结果：<strong>{{ justSubmittedStatus }}</strong>
        <span class="text-indigo-700"> · 下方为全站排名，黑色高亮行为你的名次</span>
      </div>

      <div v-if="canStartArena" class="flex items-center gap-2">
        <button
          class="ml-auto px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
          :disabled="starting || board?.my_status === 'in_progress'"
          @click="startArena"
        >
          {{ starting ? '准备中...' : '再打一局' }}
        </button>
      </div>

      <p v-if="board" class="text-sm text-gray-500">
        参与人数 {{ board.total_participants }} · 我的状态：
        <span class="font-medium text-gray-800">{{ statusLabel(board.my_status) }}</span>
        <span v-if="board.my_status === 'pending_review'" class="text-amber-600">（审核中，暂不上榜）</span>
      </p>

      <div class="bg-white rounded-xl border overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-gray-500">
            <tr class="text-left">
              <th class="px-4 py-3">排名</th>
              <th class="px-4 py-3">姓名</th>
              <th class="px-4 py-3">擂台分</th>
              <th class="px-4 py-3">耗时</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr
              v-for="e in board?.entries ?? []"
              :key="e.user_id"
              :class="e.is_me ? 'arena-board-row-me bg-indigo-50' : ''"
            >
              <td class="px-4 py-3">{{ e.rank }}</td>
              <td class="px-4 py-3 font-medium">
                {{ e.display_name }}
                <span v-if="e.student_no_suffix" class="arena-board-row-me-suffix text-xs">({{ e.student_no_suffix }})</span>
              </td>
              <td class="px-4 py-3">{{ e.arena_score }}</td>
              <td class="px-4 py-3">{{ formatMs(e.duration_ms) }}</td>
            </tr>
          </tbody>
        </table>
        <div v-if="!board?.entries.length" class="py-12 text-center text-gray-500">暂无上榜记录，来做第一个守擂者</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { arenaApi } from '@/api/arena'
import type { ArenaBoardResponse, ArenaMyStatus } from '@/types/arena'
import { toast } from '@/utils/toast'
import { practiceApi } from '@/api/practice'
import {
  getStoredArenaLanguage,
  parseArenaLanguage,
  setStoredArenaLanguage,
  type ArenaLanguage,
} from '@/utils/arena-language'

const route = useRoute()
const router = useRouter()
const problemId = computed(() => Number(route.params.problemId))
const language = ref<ArenaLanguage | null>(null)
const board = ref<ArenaBoardResponse | null>(null)
const loading = ref(true)
const starting = ref(false)
const justSubmittedStatus = ref<string | null>(null)

const backLink = computed(() => '/student/arena')

const canStartArena = computed(() => {
  const status = board.value?.my_status
  return status === 'none' || status === 'in_progress' || status === undefined
})

const statusLabel = (s: ArenaMyStatus): string => {
  const map: Record<ArenaMyStatus, string> = {
    none: '未参与',
    in_progress: '进行中',
    pending_review: '审核中',
    rejected: '未通过审核',
    on_board: '已上榜',
  }
  return map[s]
}

const formatMs = (ms: number): string => {
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

const resolveLanguage = (): ArenaLanguage | null => {
  return parseArenaLanguage(route.query.lang) ?? getStoredArenaLanguage()
}

const loadBoard = async () => {
  if (!language.value) return
  loading.value = true
  try {
    board.value = await arenaApi.getBoard(problemId.value, language.value)
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '加载失败')
  } finally {
    loading.value = false
  }
}

const startArena = async () => {
  if (!language.value) return
  starting.value = true
  try {
    await arenaApi.agreeTerms().catch(() => {
      /* 已同意则忽略 */
    })
    const detail = await practiceApi.getProblem(problemId.value)
    if (detail.language !== language.value) {
      toast.error('该题不属于当前语言赛道，请返回擂台重新选择语言')
      await router.push('/student/arena')
      return
    }
    const session = await arenaApi.createSession(problemId.value, language.value)
    await router.push({
      path: `/student/coding/${problemId.value}`,
      query: { arenaSessionId: String(session.id) },
    })
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '无法开始擂台')
  } finally {
    starting.value = false
  }
}

const bootstrap = async () => {
  const lang = resolveLanguage()
  if (!lang) {
    toast.error('请先选择语言')
    await router.replace('/student/arena')
    return
  }
  language.value = lang
  setStoredArenaLanguage(lang)

  try {
    const detail = await practiceApi.getProblem(problemId.value)
    if (detail.language !== lang) {
      toast.error('该题不属于当前语言赛道')
      await router.replace('/student/arena')
      return
    }
  } catch {
    await router.replace('/student/arena')
    return
  }
  await loadBoard()

  const submitted = route.query.submitted
  if (typeof submitted === 'string' && submitted.length > 0) {
    justSubmittedStatus.value = submitted
    toast.success(`擂台提交完成：${submitted}`)
    await router.replace({ query: { lang } })
  }
}

onMounted(() => void bootstrap())

watch(problemId, () => void bootstrap())
watch(
  () => route.query.lang,
  () => void bootstrap(),
)
</script>

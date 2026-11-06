<template>
  <div>
    <div class="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
      <div>
        <h1 class="text-lg font-semibold text-gray-900">班级排行榜</h1>
        <p v-if="leaderboard?.class_name" class="text-sm text-gray-500 mt-0.5">{{ leaderboard.class_name }}</p>
      </div>
      <div v-if="leaderboard?.my_rank != null" class="text-sm text-gray-500">
        我的排名：<span class="font-bold text-indigo-600">第 {{ leaderboard.my_rank }} 名</span>
      </div>
      <div v-else-if="leaderboard && leaderboard.entries.length" class="text-sm text-gray-500">
        完成至少一题后可上榜
      </div>
    </div>

    <div v-if="loading" class="p-6 text-center text-gray-500">加载中...</div>

    <div v-else-if="!leaderboard || leaderboard.entries.length === 0" class="p-12 text-center">
      <p class="text-gray-500">暂无排名数据，快去做题吧</p>
    </div>

    <div v-else class="p-6 space-y-6">
      <div v-if="leaderboard.my_score" class="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl p-5 text-white">
        <div class="grid grid-cols-4 gap-4 text-center">
          <div>
            <div class="text-2xl font-bold">{{ leaderboard.my_score.total_score }}</div>
            <div class="text-xs opacity-80 mt-1">综合得分</div>
          </div>
          <div>
            <div class="text-2xl font-bold">{{ leaderboard.my_score.accuracy_rate }}%</div>
            <div class="text-xs opacity-80 mt-1">正确率（70%）</div>
          </div>
          <div>
            <div class="text-2xl font-bold">{{ leaderboard.my_score.time_score }}</div>
            <div class="text-xs opacity-80 mt-1">耗时得分（30%）</div>
          </div>
          <div>
            <div class="text-2xl font-bold">{{ leaderboard.my_score.avg_runtime_ms ?? '-' }}</div>
            <div class="text-xs opacity-80 mt-1">平均用时(ms)</div>
          </div>
        </div>
        <p class="text-xs opacity-70 mt-3 text-center">
          补交与错题不计入排名；{{ refreshHint }}
        </p>
      </div>

      <div class="bg-white rounded-xl border border-gray-100 overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-gray-500">
            <tr class="text-left">
              <th class="px-4 py-3 font-medium">排名</th>
              <th class="px-4 py-3 font-medium">学生</th>
              <th class="px-4 py-3 font-medium">完成题数</th>
              <th class="px-4 py-3 font-medium">正确率</th>
              <th class="px-4 py-3 font-medium">综合得分</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr
              v-for="entry in leaderboard.entries"
              :key="entry.student_id"
              :class="entry.is_me ? 'leaderboard-me-row' : ''"
            >
              <td class="px-4 py-3">
                <span class="font-bold" :class="entry.rank <= 3 ? 'text-amber-500' : 'text-gray-500'">
                  {{ entry.rank }}
                </span>
              </td>
              <td class="px-4 py-3 font-medium">
                {{ entry.display_name }}
                <span v-if="entry.is_me" class="text-xs text-indigo-600 ml-1">（我）</span>
              </td>
              <td class="px-4 py-3 text-gray-600">{{ entry.completed_problems }}</td>
              <td class="px-4 py-3 text-gray-600">{{ entry.accuracy_rate }}%</td>
              <td class="px-4 py-3 font-semibold text-indigo-600">{{ entry.total_score }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { leaderboardApi } from '@/api/leaderboard'
import { usePageDwell } from '@/composables/usePageDwell'
import { toast } from '@/utils/toast'
import { trackEvent } from '@/utils/tracker'
import type { LeaderboardResponse } from '@/types/leaderboard'

const loading = ref(true)
const leaderboard = ref<LeaderboardResponse | null>(null)

usePageDwell('leaderboard_dwell', '/student/leaderboard', 'student')

const refreshHint = computed(() => {
  if (!leaderboard.value?.refreshed_at) return '每日凌晨刷新'
  const time = new Date(leaderboard.value.refreshed_at).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
  return leaderboard.value.source === 'snapshot'
    ? `数据更新于 ${time}（每日凌晨刷新）`
    : `实时计算，下次快照于凌晨刷新`
})

const loadLeaderboard = async () => {
  loading.value = true
  try {
    leaderboard.value = await leaderboardApi.getMyClass()
    trackEvent({
      event_name: 'leaderboard_view',
      page: '/student/leaderboard',
      module: 'student',
      detail: `source=${leaderboard.value.source ?? 'live'}`,
    })
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '加载排行榜失败')
    leaderboard.value = null
  } finally {
    loading.value = false
  }
}

onMounted(loadLeaderboard)
</script>

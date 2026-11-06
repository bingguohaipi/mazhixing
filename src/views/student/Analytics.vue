<template>
  <div>
    <div class="bg-white border-b border-gray-200 px-6 py-3">
      <h1 class="text-lg font-semibold text-gray-900">个人学情中心</h1>
      <p class="text-sm text-gray-500 mt-0.5">查看做题进度、正确率与知识点掌握情况</p>
    </div>

    <div v-if="loading" class="p-6 text-center text-gray-500">加载中...</div>
    <div v-else-if="!overview" class="p-12 text-center text-gray-500">还没有做题记录，快去完成作业吧</div>
    <div v-else class="p-6 space-y-6">
      <div class="grid grid-cols-4 gap-4">
        <div class="bg-white rounded-xl border border-gray-100 p-5">
          <div class="text-sm text-gray-500">已完成题目</div>
          <div class="text-2xl font-bold text-gray-900 mt-1">{{ overview.completed_problems }}</div>
        </div>
        <div class="bg-white rounded-xl border border-gray-100 p-5">
          <div class="text-sm text-gray-500">正确率</div>
          <div class="text-2xl font-bold text-green-600 mt-1">{{ overview.accuracy }}%</div>
        </div>
        <div class="bg-white rounded-xl border border-gray-100 p-5">
          <div class="text-sm text-gray-500">班级平均正确率</div>
          <div class="text-2xl font-bold text-indigo-600 mt-1">{{ overview.class_avg_accuracy }}%</div>
        </div>
        <div class="bg-white rounded-xl border border-gray-100 p-5">
          <div class="text-sm text-gray-500">待复习错题</div>
          <div class="text-2xl font-bold text-amber-600 mt-1">{{ overview.wrong_pending_count }}</div>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-gray-100 p-5">
        <h3 class="font-semibold text-gray-900 mb-4">知识点掌握</h3>
        <div v-if="overview.knowledge_progress.length === 0" class="text-sm text-gray-500 py-6 text-center">
          还没有做题记录，快去完成作业吧
        </div>
        <div v-else class="space-y-3">
          <div v-for="progress in overview.knowledge_progress" :key="progress.name">
            <div class="flex justify-between text-sm mb-1">
              <span>{{ progress.name }}</span>
              <span class="text-gray-600">{{ progress.status }} · {{ progress.mastery_rate }}%</span>
            </div>
            <div class="student-kp-progress-track">
              <div class="student-kp-progress-fill" :style="{ width: `${progress.mastery_rate}%` }" />
            </div>
          </div>
        </div>
      </div>

      <div class="flex gap-3">
        <RouterLink to="/student/wrong" class="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg">
          前往错题本
        </RouterLink>
        <RouterLink to="/student/leaderboard" class="px-4 py-2 border border-gray-300 text-sm rounded-lg">
          查看排行榜
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { usePageDwell } from '@/composables/usePageDwell'
import { studentDashboardApi } from '@/api/student-dashboard'
import type { StudentDashboardOverview } from '@/types/student-dashboard'

usePageDwell('student_analytics_dwell', '/student/analytics', 'student')

const loading = ref(true)
const overview = ref<StudentDashboardOverview | null>(null)

onMounted(async () => {
  loading.value = true
  try {
    overview.value = await studentDashboardApi.getOverview()
  } catch {
    overview.value = null
  } finally {
    loading.value = false
  }
})
</script>

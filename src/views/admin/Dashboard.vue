<template>
  <div class="p-6 space-y-6">
    <h1 class="text-xl font-semibold">管理后台</h1>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <RouterLink to="/admin/public-problems" class="bg-white border rounded-xl p-5 hover:border-indigo-300">
        <div class="text-lg font-medium">公共题库</div>
        <p class="text-sm text-gray-500 mt-1">编辑保存即生效，历史版本可删除</p>
      </RouterLink>
      <RouterLink to="/admin/users" class="bg-white border rounded-xl p-5 hover:border-indigo-300">
        <div class="text-lg font-medium">用户管理</div>
        <p class="text-sm text-gray-500 mt-1">教师 / 学生 / 家长账号</p>
      </RouterLink>
      <RouterLink to="/admin/suggestions" class="bg-white border rounded-xl p-5 hover:border-indigo-300">
        <div class="text-lg font-medium">建议中心</div>
        <p class="text-sm text-gray-500 mt-1">全站反馈处理</p>
      </RouterLink>
    </div>

    <div class="bg-white border rounded-xl p-5">
      <div class="flex items-center justify-between mb-4">
        <h2 class="font-semibold text-gray-900">埋点概览（近 {{ eventSummary?.period_days ?? 7 }} 天）</h2>
        <button class="text-sm text-indigo-600" :disabled="eventsLoading" @click="loadEvents">
          {{ eventsLoading ? '刷新中...' : '刷新' }}
        </button>
      </div>
      <div v-if="eventsLoading" class="text-sm text-gray-500">加载中...</div>
      <div v-else-if="!eventSummary" class="text-sm text-gray-500">暂无埋点数据</div>
      <div v-else class="space-y-4">
        <div class="grid grid-cols-3 gap-4 text-sm">
          <div class="rounded-lg bg-gray-50 p-3">
            <div class="text-gray-500">事件总数</div>
            <div class="text-xl font-bold">{{ eventSummary.total_events }}</div>
          </div>
          <div class="rounded-lg bg-gray-50 p-3">
            <div class="text-gray-500">异常类事件</div>
            <div class="text-xl font-bold text-red-600">{{ eventSummary.error_events }}</div>
          </div>
          <div class="rounded-lg bg-gray-50 p-3">
            <div class="text-gray-500">判题成功率（埋点）</div>
            <div class="text-xl font-bold text-green-600">
              {{ eventSummary.judge_success_rate != null ? `${eventSummary.judge_success_rate}%` : '-' }}
            </div>
          </div>
        </div>
        <table class="w-full text-sm">
          <thead class="text-gray-500 text-left">
            <tr>
              <th class="py-2">事件名</th>
              <th class="py-2">次数</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in eventSummary.top_events" :key="row.event_name" class="border-t border-gray-100">
              <td class="py-2 font-mono text-xs">{{ row.event_name }}</td>
              <td class="py-2">{{ row.count }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <p class="text-xs text-gray-400">演示管理员：账号 admin · 密码 Admin123</p>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { adminApi } from '@/api/admin'
import type { EventSummaryResponse } from '@/types/admin'

const eventsLoading = ref(false)
const eventSummary = ref<EventSummaryResponse | null>(null)

const loadEvents = async () => {
  eventsLoading.value = true
  try {
    eventSummary.value = await adminApi.getEventsSummary(7)
  } catch {
    eventSummary.value = null
  } finally {
    eventsLoading.value = false
  }
}

onMounted(loadEvents)
</script>

<template>
  <div>
    <div v-if="loading" class="p-6 text-center text-gray-500">加载中...</div>
    <div v-else-if="children.length === 0" class="p-12 text-center">
      <div class="text-4xl mb-3">👨‍👩‍👧</div>
      <p class="text-gray-500 mb-2">暂无绑定的孩子</p>
      <p class="text-sm text-gray-400">请联系授课教师完成家长-学生账号绑定</p>
    </div>
    <div v-else-if="overview" class="p-6 space-y-6">
      <div class="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl p-6 text-white">
        <div class="flex items-center gap-4">
          <div class="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center text-2xl font-bold">
            {{ overview.display_name.charAt(0) }}
          </div>
          <div>
            <h2 class="text-2xl font-bold">{{ overview.display_name }}</h2>
            <p class="text-indigo-100 mt-1">
              {{ overview.class_names.join('、') || '未加入班级' }}
              <span v-if="overview.student_no"> · 学号 {{ overview.student_no }}</span>
            </p>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-4 gap-4">
        <div class="surface-dark-card rounded-xl p-5">
          <div class="text-sm text-gray-500 mb-1">近{{ overview.period_days }}天做题量</div>
          <div class="text-3xl font-bold text-gray-900">{{ overview.total_submissions }}</div>
          <div class="text-xs text-gray-400 mt-1">累计完成 {{ overview.completed_problems }} 题</div>
        </div>
        <div class="surface-dark-card rounded-xl p-5">
          <div class="text-sm text-gray-500 mb-1">整体正确率</div>
          <div class="text-3xl font-bold text-green-600">{{ overview.accuracy }}%</div>
          <div class="text-xs text-gray-400 mt-1">不含补交数据</div>
        </div>
        <div class="surface-dark-card rounded-xl p-5">
          <div class="text-sm text-gray-500 mb-1">近{{ overview.period_days }}天错题</div>
          <div class="text-3xl font-bold text-red-500">{{ overview.wrong_count }}</div>
          <div class="text-xs text-gray-400 mt-1">WA/TLE/RE 合计</div>
        </div>
        <div class="surface-dark-card rounded-xl p-5">
          <div class="text-sm text-gray-500 mb-1">薄弱知识点</div>
          <div class="text-3xl font-bold text-amber-500">{{ weakKnowledgeCount }}</div>
          <div class="text-xs text-gray-400 mt-1">掌握率低于 60%</div>
        </div>
      </div>

      <NoticeFeedPanel />

      <div class="surface-dark-card rounded-xl p-5">
        <h3 class="font-semibold text-gray-900 mb-4">近期作业表现</h3>
        <div v-if="overview.recent_homeworks.length === 0" class="text-sm text-gray-500 py-6 text-center">
          暂无作业，请等待老师布置
        </div>
        <table v-else class="w-full text-sm">
          <thead class="text-gray-500 border-b border-gray-100">
            <tr class="text-left">
              <th class="pb-2 font-medium">作业名称</th>
              <th class="pb-2 font-medium">截止时间</th>
              <th class="pb-2 font-medium">进度</th>
              <th class="pb-2 font-medium">状态</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-for="hw in overview.recent_homeworks" :key="hw.homework_id">
              <td class="py-3 font-medium">{{ hw.title }}</td>
              <td class="py-3 text-gray-500">{{ formatTime(hw.end_time) }}</td>
              <td class="py-3">{{ hw.progress }}</td>
              <td class="py-3">
                <span class="badge" :class="getStatusClass(hw.status)">{{ hw.status }}</span>
                <span v-if="hw.is_late_only" class="badge bg-amber-100 text-amber-700 ml-1">仅补交</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import NoticeFeedPanel from '@/components/NoticeFeedPanel.vue'
import { useParentContext } from '@/composables/useParentContext'

const { children, overview, loading, weakKnowledgeCount } = useParentContext()

const formatTime = (iso: string) =>
  new Date(iso).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })

const getStatusClass = (status: string) => {
  if (status === '进行中') return 'bg-amber-100 text-amber-700'
  if (status === '已截止') return 'bg-gray-100 text-gray-600'
  return 'bg-indigo-100 text-indigo-700'
}
</script>

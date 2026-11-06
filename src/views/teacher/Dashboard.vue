<template>
  <div>
    <div class="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <h1 class="text-lg font-semibold text-gray-900">工作台</h1>
        <span class="badge bg-indigo-100 text-indigo-700">教师端</span>
      </div>
      <button
        class="px-4 py-2 text-sm border border-indigo-300 text-indigo-600 rounded-lg hover:bg-indigo-50"
        @click="$emit('open-publish-notice')"
      >
        📢 发布通知
      </button>
    </div>

    <div v-if="loading" class="p-6 text-center text-gray-500">加载中...</div>

    <div v-else-if="overview" class="p-6 space-y-6">
      <div class="grid grid-cols-3 gap-4">
        <div class="bg-white rounded-xl p-5 border border-gray-100">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm text-gray-500">我的班级</span>
            <span class="text-2xl">🏫</span>
          </div>
          <div class="text-3xl font-bold text-gray-900">{{ overview.class_count }}</div>
          <div class="text-xs text-gray-400 mt-1">共 {{ overview.student_count }} 名学生</div>
        </div>
        <div class="bg-white rounded-xl p-5 border border-gray-100">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm text-gray-500">进行中作业</span>
            <span class="text-2xl">📝</span>
          </div>
          <div class="text-3xl font-bold text-amber-500">{{ overview.active_homework_count }}</div>
          <div class="text-xs text-gray-400 mt-1">实时统计</div>
        </div>
        <div class="bg-white rounded-xl p-5 border border-gray-100">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm text-gray-500">本周提交</span>
            <span class="text-2xl">⚡</span>
          </div>
          <div class="text-3xl font-bold text-gray-900">{{ overview.week_submission_count }}</div>
          <div class="text-xs text-green-500 mt-1">通过率 {{ overview.week_pass_rate }}%</div>
        </div>
      </div>

      <div class="grid grid-cols-3 gap-6">
        <div class="col-span-2 bg-white rounded-xl border border-gray-100 p-5">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-semibold text-gray-900">近期作业</h3>
            <RouterLink to="/teacher/homework" class="text-sm text-indigo-600 hover:underline">查看全部</RouterLink>
          </div>
          <div v-if="overview.recent_homeworks.length === 0" class="text-center py-10 text-gray-500">
            暂无作业，请等待布置
          </div>
          <table v-else class="w-full text-sm">
            <thead>
              <tr class="text-left text-gray-500 border-b border-gray-100">
                <th class="pb-2 font-medium">作业名称</th>
                <th class="pb-2 font-medium">班级</th>
                <th class="pb-2 font-medium">截止时间</th>
                <th class="pb-2 font-medium">提交率</th>
                <th class="pb-2 font-medium">状态</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-for="hw in overview.recent_homeworks" :key="hw.id">
                <td class="py-3">{{ hw.title }}</td>
                <td class="py-3 text-gray-500">{{ hw.class_names.join('、') || '-' }}</td>
                <td class="py-3 text-gray-500">{{ formatTime(hw.end_time) }}</td>
                <td class="py-3">
                  <div class="flex items-center gap-2">
                    <div class="w-16 h-1.5 bg-gray-100 rounded-full">
                      <div
                        class="h-full bg-indigo-500 rounded-full"
                        :style="{ width: `${hw.completion_rate}%` }"
                      ></div>
                    </div>
                    <span class="text-xs">{{ hw.completion_rate }}%</span>
                  </div>
                </td>
                <td class="py-3">
                  <span class="badge" :class="getStatusClass(hw.status)">{{ hw.status }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="bg-white rounded-xl border border-gray-100 p-5">
          <h3 class="font-semibold text-gray-900 mb-4">快捷入口</h3>
          <div class="space-y-3">
            <RouterLink
              to="/teacher/homework"
              class="flex items-start gap-3 p-3 bg-gray-50 rounded-lg hover:bg-indigo-50 card-hover"
            >
              <span class="mt-0.5">📝</span>
              <div class="flex-1">
                <div class="text-sm font-medium text-gray-900">布置作业</div>
                <div class="text-xs text-gray-500 mt-0.5">选择班级与题目发布练习</div>
              </div>
            </RouterLink>
            <RouterLink
              to="/teacher/analytics"
              class="flex items-start gap-3 p-3 bg-gray-50 rounded-lg hover:bg-indigo-50 card-hover"
            >
              <span class="mt-0.5">📊</span>
              <div class="flex-1">
                <div class="text-sm font-medium text-gray-900">查看学情分析</div>
                <div class="text-xs text-gray-500 mt-0.5">掌握班级整体学习情况</div>
              </div>
            </RouterLink>
            <RouterLink
              to="/teacher/classes"
              class="flex items-start gap-3 p-3 bg-gray-50 rounded-lg hover:bg-indigo-50 card-hover"
            >
              <span class="mt-0.5">👨‍🎓</span>
              <div class="flex-1">
                <div class="text-sm font-medium text-gray-900">管理班级学生</div>
                <div class="text-xs text-gray-500 mt-0.5">添加学生、绑定家长账号</div>
              </div>
            </RouterLink>
            <button
              type="button"
              class="w-full flex items-start gap-3 p-3 bg-gray-50 rounded-lg hover:bg-indigo-50 text-left card-hover"
              @click="$emit('open-publish-notice')"
            >
              <span class="mt-0.5">📢</span>
              <div class="flex-1">
                <div class="text-sm font-medium text-gray-900">发布班级通知</div>
                <div class="text-xs text-gray-500 mt-0.5">向学生和家长推送消息</div>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

defineEmits<{ 'open-publish-notice': [] }>()
import { analyticsApi } from '@/api/analytics'
import { toast } from '@/utils/toast'
import type { TeacherDashboardOverview } from '@/types/analytics'

const loading = ref(true)
const overview = ref<TeacherDashboardOverview | null>(null)

const formatTime = (iso: string) =>
  new Date(iso).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })

const getStatusClass = (status: string) => {
  if (status === '进行中') return 'bg-amber-100 text-amber-700'
  if (status === '已截止') return 'bg-green-100 text-green-700'
  if (status === '未开始') return 'bg-indigo-100 text-indigo-700'
  return 'bg-gray-100 text-gray-600'
}

const loadDashboard = async () => {
  loading.value = true
  try {
    overview.value = await analyticsApi.getDashboard()
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '加载工作台失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadDashboard)
</script>

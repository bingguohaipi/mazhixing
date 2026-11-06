<template>
  <div>
    <div class="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <button class="text-gray-400 hover:text-gray-600" @click="router.push('/student/dashboard')">← 返回</button>
        <h1 class="text-lg font-semibold text-gray-900">{{ detail?.title || '作业详情' }}</h1>
        <span v-if="detail" class="badge" :class="getStatusClass(detail.status)">{{ detail.status }}</span>
      </div>
    </div>

    <div class="p-6">
      <div v-if="loading" class="text-center py-16 text-gray-500">加载中...</div>
      <div v-else-if="error" class="text-center py-16 text-red-500">{{ error }}</div>
      <template v-else-if="detail">
        <div
          v-if="detail.update_notice"
          class="bg-indigo-50 border border-indigo-100 rounded-xl p-4 mb-4 text-sm text-indigo-800"
        >
          📢 {{ detail.update_notice }}
        </div>
        <div class="bg-white rounded-xl border border-gray-100 p-5 mb-6">
          <div class="flex items-center justify-between mb-3">
            <div>
              <p class="text-sm text-gray-500">{{ detail.class_name }} · {{ detail.problems.length }} 道题</p>
              <p v-if="detail.description" class="text-sm text-gray-600 mt-2">{{ detail.description }}</p>
            </div>
            <div class="text-right text-sm">
              <div class="text-gray-500">截止：{{ formatTime(detail.end_time) }}</div>
              <div class="font-medium text-indigo-600 mt-1">{{ detail.progress }}</div>
            </div>
          </div>
          <div v-if="detail.allow_late_submission" class="text-xs text-indigo-600">✓ 已开启补交</div>
        </div>

        <div class="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <div class="px-4 py-3 bg-gray-50 text-sm font-medium text-gray-700 border-b border-gray-100">题目列表</div>
          <div class="divide-y divide-gray-50">
            <div
              v-for="(p, idx) in detail.problems"
              :key="p.id"
              class="flex items-center justify-between px-4 py-3 hover:bg-gray-50 cursor-pointer"
              @click="goCoding(p.id)"
            >
              <div class="flex items-center gap-3">
                <span class="text-gray-400 w-6">{{ idx + 1 }}</span>
                <span class="font-medium text-gray-900">#{{ p.id }} {{ p.title }}</span>
                <span class="badge bg-gray-100 text-gray-600 text-xs">{{ p.difficulty }}</span>
              </div>
              <div class="flex items-center gap-3">
                <span v-if="p.best_status" class="badge text-xs" :class="getResultClass(p.best_status)">{{ p.best_status }}</span>
                <span v-else class="text-xs text-gray-400">未提交</span>
                <span class="text-indigo-600 text-sm">去做题 →</span>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { homeworkApi } from '@/api/homework'
import { practiceApi } from '@/api/practice'
import type { StudentHomeworkDetail } from '@/types/practice'

const route = useRoute()
const router = useRouter()

const detail = ref<StudentHomeworkDetail | null>(null)
const loading = ref(true)
const error = ref('')

const homeworkId = Number(route.params.id)

const loadDetail = async () => {
  loading.value = true
  error.value = ''
  try {
    detail.value = await practiceApi.getHomeworkDetail(homeworkId)
    if (detail.value?.has_unread_update) {
      await homeworkApi.ackUpdate(homeworkId)
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载失败'
  } finally {
    loading.value = false
  }
}

const goCoding = (problemId: number) => {
  router.push({ path: `/student/coding/${problemId}`, query: { homeworkId: String(homeworkId) } })
}

const formatTime = (iso: string) =>
  new Date(iso).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })

const getStatusClass = (status: string) => {
  if (status === '进行中') return 'bg-green-100 text-green-700'
  if (status === '未开始') return 'bg-gray-100 text-gray-600'
  if (status === '已截止') return 'bg-amber-100 text-amber-700'
  return 'bg-red-100 text-red-700'
}

const getResultClass = (status: string) => {
  if (status === 'AC') return 'bg-green-100 text-green-700'
  if (status === 'TLE') return 'bg-gray-100 text-gray-600'
  if (status === 'CE') return 'bg-orange-100 text-orange-700'
  return 'bg-red-100 text-red-700'
}

onMounted(loadDetail)
</script>

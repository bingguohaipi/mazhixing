<template>
  <div>
    <div class="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
      <h1 class="text-lg font-semibold text-gray-900">作业管理</h1>
      <button class="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700" @click="showAssignModal = true">+ 布置作业</button>
    </div>

    <div class="p-6 space-y-4">
      <div class="flex gap-2 flex-wrap">
        <button
          v-for="tab in statusTabs"
          :key="tab.value"
          class="px-4 py-2 text-sm bg-white border rounded-lg"
          :class="filterStatus === tab.value ? 'border-indigo-500 text-indigo-600 font-medium' : 'border-gray-200 text-gray-600 hover:bg-gray-50'"
          @click="filterStatus = tab.value; loadHomework()"
        >
          {{ tab.label }}
        </button>
      </div>

      <div v-if="loading" class="text-center py-16 text-gray-500">加载中...</div>

      <div v-else-if="homeworkList.length === 0" class="bg-white rounded-xl border border-gray-100 p-12 text-center">
        <div class="text-4xl mb-3">📋</div>
        <p class="text-gray-500 mb-4">暂无作业，请先布置作业</p>
        <button class="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700" @click="showAssignModal = true">+ 布置作业</button>
      </div>

      <div v-else class="grid grid-cols-2 gap-4">
        <div
          v-for="hw in homeworkList"
          :key="hw.id"
          class="bg-white rounded-xl border border-gray-100 p-5 card-hover cursor-pointer transition-shadow hover:shadow-md hover:border-indigo-200"
          @click="openDetail(hw.id)"
        >
          <div class="flex items-start justify-between mb-3">
            <div class="min-w-0">
              <h3 class="font-semibold text-gray-900">{{ hw.title }}</h3>
              <p class="text-sm text-gray-500 mt-1">{{ hw.class_names.join('、') }} · {{ hw.problem_count }}道题</p>
            </div>
            <span class="badge shrink-0 ml-2" :class="getStatusClass(hw.status)">{{ hw.status }}</span>
          </div>

          <div class="grid grid-cols-2 gap-3 mb-2 text-center">
            <div class="bg-gray-50 rounded-lg py-2">
              <div class="text-lg font-bold text-gray-900">{{ hw.submitted_count }}/{{ hw.total_students }}</div>
              <div class="text-xs text-gray-500">已完成人数</div>
            </div>
            <div class="bg-gray-50 rounded-lg py-2">
              <div class="text-lg font-bold text-green-600">{{ hw.correct_count }}</div>
              <div class="text-xs text-gray-500">全对人数</div>
            </div>
          </div>
          <p class="text-[11px] text-gray-400 mb-3 leading-snug">
            全对 = 每题都 AC 的学生数。仅改题目内容不会重判旧提交，需学生重新提交后才会变。
          </p>

          <div class="text-sm text-gray-500">
            <div>⏰ 开始：{{ formatTime(hw.start_time) }}</div>
            <div>⏰ 截止：{{ formatTime(hw.end_time) }}</div>
            <div v-if="hw.allow_late_submission" class="text-indigo-600 text-xs mt-1">✓ 已开启补交</div>
            <div v-if="(hw.late_submission_count ?? 0) > 0" class="text-amber-600 text-xs mt-1">
              补交 {{ hw.late_submission_count }} 人（不计入常规统计）
            </div>
          </div>

          <div class="mt-3 pt-3 border-t border-gray-50 text-xs text-indigo-500">点击查看详情 · 编辑 · 操作 →</div>
        </div>
      </div>
    </div>

    <AssignHomeworkModal
      v-if="showAssignModal"
      @close="showAssignModal = false"
      @success="onListChanged"
    />

    <HomeworkDetailModal
      v-if="detailHomeworkId !== null"
      :homework-id="detailHomeworkId"
      @close="onDetailClose"
      @changed="onListChanged"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { usePageDwell } from '@/composables/usePageDwell'
import { homeworkApi } from '@/api/homework'
import AssignHomeworkModal from '@/components/AssignHomeworkModal.vue'
import HomeworkDetailModal from '@/components/HomeworkDetailModal.vue'
import type { HomeworkListItem, HomeworkStatus } from '@/types/homework'

const homeworkList = ref<HomeworkListItem[]>([])
const loading = ref(true)
const filterStatus = ref('all')
const showAssignModal = ref(false)
const detailHomeworkId = ref<number | null>(null)

usePageDwell('teacher_homework_dwell', '/teacher/homework', 'teacher')

const statusTabs = [
  { label: '全部', value: 'all' },
  { label: '进行中', value: '进行中' },
  { label: '已截止', value: '已截止' },
  { label: '未开始', value: '未开始' },
  { label: '已撤回', value: '已撤回' },
]

const getStatusClass = (status: HomeworkStatus) => {
  if (status === '进行中') return 'bg-amber-100 text-amber-700'
  if (status === '已截止') return 'bg-gray-100 text-gray-600'
  if (status === '已撤回') return 'bg-red-100 text-red-700'
  return 'bg-indigo-100 text-indigo-700'
}

const formatTime = (iso: string) => {
  const date = new Date(iso)
  return date.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const loadHomework = async () => {
  loading.value = true
  try {
    homeworkList.value = await homeworkApi.list(filterStatus.value)
  } catch (err) {
    alert(err instanceof Error ? err.message : '加载作业失败')
  } finally {
    loading.value = false
  }
}

const openDetail = (id: number) => {
  detailHomeworkId.value = id
}

const onListChanged = () => {
  void loadHomework()
}

const onDetailClose = () => {
  detailHomeworkId.value = null
  void loadHomework()
}

onMounted(loadHomework)
</script>

<template>
  <div class="modal-mask" @click.self="$emit('close')">
    <div class="modal-box" style="width: 720px; max-height: 90vh; overflow-y: auto;">
      <div v-if="loading" class="py-12 text-center text-gray-500">加载中...</div>
      <template v-else-if="detail">
        <div class="flex items-start justify-between gap-3 mb-2">
          <div>
            <h3 class="modal-title" style="margin: 0">学生提交详情</h3>
            <p class="modal-sub mb-0">
              {{ detail.student_display_name }}（{{ detail.student_account }}）·
              题目 #{{ detail.problem_id }} · {{ detail.language }}
            </p>
          </div>
          <span class="badge shrink-0" :class="statusClass(detail.status)">{{ detail.status }}</span>
        </div>

        <div v-if="detail.is_late" class="text-xs text-amber-600 mb-2">本次为补交提交</div>

        <div v-if="detail.compile_output" class="mb-3 p-2 bg-amber-50 border border-amber-100 rounded-lg text-xs text-amber-900 whitespace-pre-wrap">
          {{ detail.compile_output }}
        </div>
        <div v-else-if="detail.error_message" class="mb-3 p-2 bg-red-50 border border-red-100 rounded-lg text-xs text-red-800 whitespace-pre-wrap">
          {{ detail.error_message }}
        </div>

        <div class="text-sm font-medium text-gray-700 mb-1">学生代码</div>
        <pre class="code-block mb-4">{{ detail.code }}</pre>

        <div v-if="detail.case_results.length" class="mb-4">
          <div class="text-sm font-medium text-gray-700 mb-2">用例结果</div>
          <div class="border border-gray-100 rounded-lg divide-y divide-gray-50 text-xs">
            <div
              v-for="c in detail.case_results"
              :key="c.case_index"
              class="px-3 py-2 flex items-center justify-between gap-2"
            >
              <span class="text-gray-600">
                用例 {{ c.case_index + 1 }}
                <span v-if="c.is_sample" class="text-gray-400">（样例）</span>
              </span>
              <span :class="statusTextClass(c.status)">{{ c.status }}</span>
            </div>
          </div>
        </div>

        <div class="modal-actions">
          <button class="modal-btn-cancel" type="button" @click="$emit('close')">关闭</button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { homeworkApi } from '@/api/homework'
import type { TeacherSubmissionDetail } from '@/types/homework'
import type { SubmissionStatus } from '@/types/submission'

const props = defineProps<{
  homeworkId: number
  submissionId: number
}>()

defineEmits<{ close: [] }>()

const loading = ref(true)
const detail = ref<TeacherSubmissionDetail | null>(null)

const statusClass = (status: SubmissionStatus) => {
  if (status === 'AC') return 'badge-success'
  if (status === 'CE') return 'badge-warning'
  if (status === 'TLE') return 'badge-muted'
  return 'badge-danger'
}

const statusTextClass = (status: SubmissionStatus) => {
  if (status === 'AC') return 'text-green-600 font-medium'
  if (status === 'CE') return 'text-amber-600'
  if (status === 'TLE') return 'text-gray-500'
  return 'text-red-600 font-medium'
}

onMounted(async () => {
  try {
    detail.value = await homeworkApi.getSubmissionForTeacher(props.homeworkId, props.submissionId)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.code-block {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px 14px;
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.5;
  overflow-x: auto;
  max-height: 320px;
  white-space: pre;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
</style>

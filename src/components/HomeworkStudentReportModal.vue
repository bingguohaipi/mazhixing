<template>
  <div class="modal-mask" @click.self="$emit('close')">
    <div class="modal-box" style="width: 900px; max-width: 96vw; max-height: 90vh; overflow-y: auto;">
      <div v-if="loading" class="py-16 text-center text-gray-500">加载中...</div>
      <template v-else-if="report">
        <h3 class="modal-title">学生作答情况</h3>
        <p class="modal-sub">{{ report.homework_title }} · 共 {{ report.problem_count }} 道题</p>

        <div class="mb-4 p-3 bg-green-50 border border-green-100 rounded-lg">
          <div class="text-sm font-medium text-green-800 mb-1">
            全对名单（{{ report.all_ac_students.length }} 人）
          </div>
          <p v-if="report.all_ac_students.length === 0" class="text-sm text-green-700/80">
            暂无全对学生
          </p>
          <p v-else class="text-sm text-green-900">{{ report.all_ac_students.join('、') }}</p>
        </div>

        <div class="overflow-x-auto border border-gray-100 rounded-lg">
          <table class="w-full text-sm">
            <thead class="bg-gray-50 text-gray-600">
              <tr>
                <th class="text-left px-3 py-2 font-medium min-w-[120px]">学生</th>
                <th class="text-center px-2 py-2 font-medium w-20">正确</th>
                <th
                  v-for="(p, idx) in report.problems"
                  :key="p.id"
                  class="text-left px-2 py-2 font-medium min-w-[140px]"
                  :title="p.title"
                >
                  题{{ idx + 1 }}
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-for="row in report.students" :key="row.student_id" class="align-top">
                <td class="px-3 py-2">
                  <div class="font-medium text-gray-900">{{ row.display_name }}</div>
                  <div class="text-xs text-gray-400">{{ row.student_no || row.account }}</div>
                </td>
                <td class="px-2 py-2 text-center">
                  <span :class="row.all_ac ? 'text-green-600 font-semibold' : 'text-gray-800'">
                    {{ row.ac_count }}/{{ row.problem_count }}
                  </span>
                </td>
                <td v-for="p in row.problems" :key="p.problem_id" class="px-2 py-2">
                  <div v-if="!p.status" class="text-gray-400 text-xs">未提交</div>
                  <div v-else class="space-y-1">
                    <div class="flex items-center gap-1 flex-wrap">
                      <span class="badge text-xs" :class="statusClass(p.status)">{{ p.status }}</span>
                      <span v-if="p.is_late" class="text-[10px] text-amber-600">补交</span>
                      <button
                        v-if="p.submission_id"
                        type="button"
                        class="text-[11px] text-indigo-600 hover:underline"
                        @click="openCode(p.submission_id)"
                      >
                        看代码
                      </button>
                    </div>
                    <p
                      v-if="p.status !== 'AC' && p.error_message"
                      class="text-[11px] text-red-600/90 line-clamp-2"
                      :title="p.error_message"
                    >
                      {{ p.error_message }}
                    </p>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <p class="text-xs text-gray-400 mt-3">
          每题展示该生最新一次有效提交（AC/WA/TLE/RE）；编译错误不计入。点击「看代码」可查看完整代码与用例结果。
        </p>

        <div class="modal-actions mt-4">
          <button class="modal-btn-cancel" type="button" @click="$emit('close')">关闭</button>
        </div>
      </template>

      <TeacherSubmissionCodeModal
        v-if="codeSubmissionId !== null"
        :homework-id="homeworkId"
        :submission-id="codeSubmissionId"
        @close="codeSubmissionId = null"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { homeworkApi } from '@/api/homework'
import type { HomeworkSubmissionReport } from '@/types/homework'
import type { SubmissionStatus } from '@/types/submission'
import TeacherSubmissionCodeModal from '@/components/TeacherSubmissionCodeModal.vue'

const props = defineProps<{ homeworkId: number }>()
defineEmits<{ close: [] }>()

const loading = ref(true)
const report = ref<HomeworkSubmissionReport | null>(null)
const codeSubmissionId = ref<number | null>(null)

const statusClass = (status: SubmissionStatus) => {
  if (status === 'AC') return 'badge-success'
  if (status === 'CE') return 'badge-warning'
  if (status === 'TLE') return 'badge-muted'
  return 'badge-danger'
}

const openCode = (submissionId: number) => {
  codeSubmissionId.value = submissionId
}

onMounted(async () => {
  try {
    report.value = await homeworkApi.getSubmissionReport(props.homeworkId)
  } finally {
    loading.value = false
  }
})
</script>

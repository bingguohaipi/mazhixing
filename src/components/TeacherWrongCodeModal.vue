<template>
  <div class="modal-mask" @click.self="$emit('close')">
    <div class="modal-box flex flex-col" style="width: 720px; max-height: 85vh;">
      <h3 class="modal-title">错题代码 · #{{ problemId }} {{ title }}</h3>
      <p class="modal-sub">仅展示尚未在该题 AC 的学生的最近一次错误提交</p>

      <div class="flex flex-wrap gap-2 mb-3 shrink-0">
        <button
          type="button"
          class="text-sm text-indigo-400 hover:text-indigo-300 underline"
          @click="openProblemPreview"
        >
          查看题目 #{{ problemId }}
        </button>
      </div>

      <div v-if="loading" class="py-10 text-center text-gray-500 text-sm">加载中...</div>
      <div v-else-if="loadError" class="py-10 text-center text-red-400 text-sm">{{ loadError }}</div>
      <div v-else-if="items.length === 0" class="py-10 text-center text-gray-500 text-sm leading-relaxed">
        暂无错误代码（学生在当前筛选周期内可能已全部订正 AC，或暂无未通过的 WA/RE/TLE 提交）
      </div>
      <div v-else class="overflow-y-auto flex-1 min-h-0 space-y-4 pr-1">
        <section
          v-for="row in items"
          :key="row.student_id"
          class="border border-gray-100 rounded-lg overflow-hidden"
        >
          <div class="bg-gray-50 px-3 py-2 flex flex-wrap items-center justify-between gap-2 text-sm">
            <span class="font-medium text-gray-900">{{ row.student_name }}</span>
            <span class="text-gray-500">
              {{ row.status }} · {{ row.language }} · {{ formatTime(row.submitted_at) }}
            </span>
          </div>
          <pre class="p-3 text-xs font-mono bg-white overflow-x-auto max-h-48">{{ row.code }}</pre>
        </section>
      </div>

      <div class="modal-actions mt-4 shrink-0">
        <button type="button" class="modal-btn-confirm w-full" @click="$emit('close')">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { analyticsApi } from '@/api/analytics'
import type { ClassProblemWrongCodeItem } from '@/types/analytics'
import { toast } from '@/utils/toast'

const props = defineProps<{
  classId: number
  problemId: number
  title: string
  period: string
  homeworkId: number | null
}>()

defineEmits<{ close: [] }>()

const router = useRouter()
const loading = ref(true)
const loadError = ref('')
const items = ref<ClassProblemWrongCodeItem[]>([])

const openProblemPreview = () => {
  void router.push(`/teacher/coding/${props.problemId}`)
}

const formatTime = (iso: string) =>
  new Date(iso).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })

onMounted(async () => {
  loadError.value = ''
  try {
    const data = await analyticsApi.getClassProblemWrongCodes(
      props.classId,
      props.problemId,
      props.period as 'week' | 'month' | 'semester',
      props.homeworkId ?? undefined,
    )
    items.value = data.items
  } catch (err) {
    const message = err instanceof Error ? err.message : '加载失败'
    loadError.value = message
    toast.error(message)
  } finally {
    loading.value = false
  }
})
</script>

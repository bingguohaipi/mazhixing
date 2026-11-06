<template>
  <div class="modal-mask" @click.self="emit('close')">
    <div class="modal-box" style="width: 480px; max-height: 80vh; overflow: hidden; display: flex; flex-direction: column;">
      <h3 class="modal-title" style="margin-bottom: 4px;">通过者</h3>
      <p class="modal-sub mb-3">#{{ problemId }} {{ title }}</p>

      <div v-if="loading" class="py-10 text-center text-gray-500 text-sm">加载中…</div>
      <div v-else-if="items.length === 0" class="py-10 text-center text-gray-500 text-sm">暂无通过记录</div>
      <ul v-else class="flex-1 overflow-y-auto divide-y divide-gray-100 border border-gray-100 rounded-lg">
        <li
          v-for="row in items"
          :key="row.user_id"
          class="px-3 py-2.5 flex items-center justify-between gap-2 text-sm"
        >
          <div class="min-w-0">
            <div class="font-medium text-gray-900 truncate">{{ row.display_name }}</div>
            <div v-if="row.student_no || row.account" class="text-xs text-gray-500 truncate">
              {{ row.student_no || row.account }}
            </div>
          </div>
          <time class="text-xs text-gray-400 shrink-0">{{ formatTime(row.first_ac_at) }}</time>
        </li>
      </ul>

      <div class="modal-actions mt-4">
        <button type="button" class="modal-btn-cancel" @click="emit('close')">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { problemApi } from '@/api/problems'
import type { ProblemAcSolverItem } from '@/types/problem'
import { toast } from '@/utils/toast'

const props = defineProps<{
  problemId: number
  title: string
}>()

const emit = defineEmits<{ close: [] }>()

const loading = ref(true)
const items = ref<ProblemAcSolverItem[]>([])

const formatTime = (iso: string) =>
  new Date(iso).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })

onMounted(async () => {
  try {
    items.value = await problemApi.listAcSolvers(props.problemId)
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '加载失败')
    emit('close')
  } finally {
    loading.value = false
  }
})
</script>

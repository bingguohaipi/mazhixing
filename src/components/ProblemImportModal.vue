<template>
  <div class="modal-mask">
    <div class="modal-box" style="width: 640px; max-height: 90vh; overflow-y: auto;">
      <h3 class="modal-title">批量导入题目</h3>
      <p class="modal-sub">
        上传 JSON 文件（最多 50 题），字段与新建题目一致。
        <a href="/problem-import-template.json" download class="text-indigo-600 hover:underline">下载模板</a>
      </p>

      <div class="modal-field">
        <input
          type="file"
          accept=".json,application/json"
          class="modal-input"
          @change="onFileChange"
        />
      </div>

      <div v-if="preview.length > 0" class="border border-gray-200 rounded-lg p-3 mb-4">
        <div class="text-sm font-medium text-gray-700 mb-2">预览（前 {{ preview.length }} 条 / 共 {{ totalCount }} 条）</div>
        <ul class="text-sm text-gray-600 space-y-1">
          <li v-for="(item, index) in preview" :key="index">
            {{ index + 1 }}. {{ item.title }}（{{ item.languages.join(' / ') }} · {{ item.difficulty }}）
          </li>
        </ul>
      </div>

      <div v-if="importResult" class="border border-gray-200 rounded-lg p-3 mb-4 text-sm">
        <p class="text-green-600 font-medium">成功导入 {{ importResult.success_count }} 题</p>
        <ul v-if="importResult.failed.length > 0" class="mt-2 text-red-600 space-y-1">
          <li v-for="row in importResult.failed" :key="row.row">
            第 {{ row.row }} 行「{{ row.title || '未命名' }}」：{{ row.reason }}
          </li>
        </ul>
      </div>

      <div v-if="formError" class="modal-error show" style="margin-bottom: 12px;">{{ formError }}</div>
      <div class="modal-actions">
        <button class="modal-btn-cancel" @click="$emit('close')">关闭</button>
        <button class="modal-btn-confirm" :disabled="submitting || parsedProblems.length === 0" @click="submit">
          {{ submitting ? '导入中...' : '开始导入' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { problemApi } from '@/api/problems'
import type { ProblemCreatePayload, ProblemImportResult } from '@/types/problem'

const props = defineProps<{
  importFn?: (problems: ProblemCreatePayload[]) => Promise<ProblemImportResult>
}>()

const emit = defineEmits<{ close: []; success: [] }>()

const submitting = ref(false)
const formError = ref('')
const parsedProblems = ref<ProblemCreatePayload[]>([])
const importResult = ref<ProblemImportResult | null>(null)

const totalCount = computed(() => parsedProblems.value.length)
const preview = computed(() => parsedProblems.value.slice(0, 5))

const onFileChange = async (event: Event) => {
  formError.value = ''
  importResult.value = null
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  try {
    const text = await file.text()
    const data = JSON.parse(text) as { problems?: ProblemCreatePayload[] }
    if (!Array.isArray(data.problems) || data.problems.length === 0) {
      formError.value = 'JSON 需包含 problems 数组且至少 1 道题'
      parsedProblems.value = []
      return
    }
    if (data.problems.length > 50) {
      formError.value = '单次最多导入 50 道题'
      parsedProblems.value = []
      return
    }
    parsedProblems.value = data.problems
  } catch {
    formError.value = 'JSON 格式无效，请检查后重试'
    parsedProblems.value = []
  }
}

const submit = async () => {
  if (parsedProblems.value.length === 0) return
  submitting.value = true
  formError.value = ''
  try {
    const runImport = props.importFn ?? problemApi.importProblems.bind(problemApi)
    importResult.value = await runImport(parsedProblems.value)
    if (importResult.value.success_count > 0) {
      emit('success')
    }
  } catch (err) {
    formError.value = err instanceof Error ? err.message : '导入失败'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="modal-mask">
    <div class="modal-box" style="width: 640px; max-height: 90vh; overflow-y: auto;">
      <h3 class="modal-title">{{ isEdit ? '编辑题目' : '新建题目' }}</h3>
      <p class="modal-sub">配置题目信息、测试用例与参考答案，至少一组有效用例方可用于布置作业</p>

      <div class="modal-field">
        <label class="modal-label">题目标题 <span style="color:#ef4444">*</span></label>
        <input type="text" class="modal-input" v-model="form.title" placeholder="例如：A+B Problem">
      </div>

      <div class="modal-field">
        <label class="modal-label">难度 <span style="color:#ef4444">*</span></label>
        <select class="modal-input" v-model="form.difficulty">
          <option value="入门">入门</option>
          <option value="简单">简单</option>
          <option value="中等">中等</option>
          <option value="困难">困难</option>
        </select>
        <p class="text-xs text-gray-500 mt-1">新建题目默认支持 Python 与 C++ 作答，无需单独选择语言。</p>
      </div>

      <div class="modal-field">
        <label class="modal-label">知识点 <span style="color:#ef4444">*</span>（可多选）</label>
        <input
          v-model="kpSearch"
          type="search"
          class="modal-input mb-2"
          placeholder="搜索知识点名称或简介…"
          autocomplete="off"
        />
        <div
          v-if="kpLoading"
          class="text-xs text-gray-500 py-2"
        >
          加载知识点…
        </div>
        <div
          v-else-if="filteredKnowledgePointOptions.length === 0"
          class="text-xs text-gray-500 py-2"
        >
          未找到匹配的知识点，请换个关键词
        </div>
        <div
          v-else
          class="border border-gray-200 rounded-lg max-h-40 overflow-y-auto p-2 space-y-1"
        >
          <label
            v-for="opt in filteredKnowledgePointOptions"
            :key="opt.name"
            class="flex items-start gap-2 text-sm cursor-pointer hover:bg-gray-50 rounded px-1 py-0.5"
          >
            <input v-model="form.knowledge_points" type="checkbox" :value="opt.name" class="mt-0.5">
            <span>
              <span class="font-medium">{{ opt.name }}</span>
              <span v-if="opt.summary" class="block text-xs text-gray-500 line-clamp-1">{{ opt.summary }}</span>
            </span>
          </label>
        </div>
        <p v-if="form.knowledge_points.length" class="text-xs text-gray-500 mt-1">
          已选 {{ form.knowledge_points.length }} 个：{{ form.knowledge_points.join('、') }}
        </p>
      </div>

      <div class="modal-field">
        <label class="modal-label">题目描述 <span style="color:#ef4444">*</span></label>
        <textarea class="modal-input" v-model="form.description" rows="3" placeholder="详细描述题目要求..." style="resize: vertical;"></textarea>
      </div>

      <div class="modal-field">
        <label class="modal-label">题目插图（可选，最多 5 张）</label>
        <label class="text-xs text-indigo-600 cursor-pointer hover:underline">
          上传图片
          <input type="file" accept="image/*" class="hidden" :disabled="form.image_urls.length >= 5" @change="onPickProblemImage" />
        </label>
        <div v-if="form.image_urls.length" class="flex gap-2 mt-2 flex-wrap">
          <div v-for="(url, idx) in form.image_urls" :key="idx" class="relative">
            <img :src="resolveMediaUrl(url)" alt="" class="w-16 h-16 object-cover rounded border" />
            <button
              type="button"
              class="absolute -top-1 -right-1 w-5 h-5 text-xs bg-red-500 text-white rounded-full"
              @click="removeProblemImage(idx)"
            >
              ×
            </button>
          </div>
        </div>
        <p class="text-xs text-gray-500 mt-1">支持 JPG/PNG/WebP/GIF，单张不超过 2MB</p>
      </div>

      <div class="modal-field mb-0">
        <div class="grid grid-cols-2 gap-3">
          <label class="modal-label">输入样例（可选）</label>
          <label class="modal-label">输出样例</label>
        </div>
        <p class="text-xs text-gray-500 mt-0.5 mb-1.5">无标准输入的题可留空</p>
        <div class="grid grid-cols-2 gap-3">
          <textarea class="modal-input" v-model="form.sample_input" rows="2" style="resize: vertical; font-family: monospace;"></textarea>
          <textarea class="modal-input" v-model="form.sample_output" rows="2" style="resize: vertical; font-family: monospace;"></textarea>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div class="modal-field">
          <label class="modal-label">时间限制（ms）</label>
          <input type="number" class="modal-input" v-model.number="form.time_limit_ms" min="100">
        </div>
        <div class="modal-field">
          <label class="modal-label">空间限制（MB）</label>
          <input type="number" class="modal-input" v-model.number="form.memory_limit_mb" min="1">
        </div>
      </div>

      <div class="modal-field">
        <label class="modal-label">参考答案（可选）</label>
        <textarea class="modal-input" v-model="form.reference_answer" rows="3" placeholder="教师参考代码..." style="resize: vertical; font-family: monospace;"></textarea>
      </div>

      <div class="modal-field">
        <div class="flex items-center justify-between mb-2">
          <label class="modal-label" style="margin:0">测试用例 <span style="color:#ef4444">*</span></label>
          <button type="button" class="text-xs text-indigo-600 hover:underline" @click="addTestCase">+ 添加用例</button>
        </div>
        <div v-for="(tc, index) in form.test_cases" :key="index" class="border border-gray-200 rounded-lg p-3 mb-2">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-medium text-gray-500">用例 {{ index + 1 }}</span>
            <div class="flex items-center gap-3">
              <label class="text-xs text-gray-500 flex items-center gap-1">
                <input type="checkbox" v-model="tc.is_sample"> 样例用例
              </label>
              <button v-if="form.test_cases.length > 1" type="button" class="text-xs text-red-500" @click="removeTestCase(index)">删除</button>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <textarea class="modal-input" v-model="tc.input_data" rows="2" placeholder="输入（可选）" style="resize: vertical; font-family: monospace;"></textarea>
            <textarea class="modal-input" v-model="tc.expected_output" rows="2" placeholder="期望输出 *" style="resize: vertical; font-family: monospace;"></textarea>
          </div>
        </div>
      </div>

      <div v-if="formError" class="modal-error show" style="margin-bottom: 12px;">{{ formError }}</div>
      <div class="modal-actions">
        <button class="modal-btn-cancel" @click="$emit('close')">取消</button>
        <button class="modal-btn-confirm" :disabled="submitting" @click="submit">
          {{ submitting ? '提交中...' : (isEdit ? '保存修改' : '创建题目') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useDebouncedWatch } from '@/composables/useDebouncedWatch'
import { practiceApi } from '@/api/practice'
import { problemApi } from '@/api/problems'
import { suggestionApi } from '@/api/suggestions'
import type { KnowledgePointOptionItem } from '@/types/practice'
import { formatZodErrors, problemFormSchema } from '@/schemas/problemSchema'
import type { ProblemCreatePayload, ProblemDetail, ProblemLanguage, ProblemDifficulty, TestCaseInput } from '@/types/problem'

const props = defineProps<{
  problem?: ProblemDetail | null
  onSave?: (
    payload: ProblemCreatePayload,
    isEdit: boolean,
    problemId?: number,
  ) => Promise<ProblemDetail | void>
}>()
const emit = defineEmits<{ close: []; success: [action: 'create' | 'update', detail?: ProblemDetail] }>()

const isEdit = computed(() => !!props.problem)
const submitting = ref(false)
const formError = ref('')
const knowledgePointOptions = ref<KnowledgePointOptionItem[]>([])
const kpLoading = ref(false)
const kpSearch = ref('')

const filteredKnowledgePointOptions = computed(() => {
  const selected = new Set(form.knowledge_points)
  const merged = [...knowledgePointOptions.value]
  for (const name of selected) {
    if (!merged.some((item) => item.name === name)) {
      merged.unshift({ name, summary: '（已选）' })
    }
  }
  return merged
})

const loadKnowledgePointOptions = async (search: string) => {
  kpLoading.value = true
  try {
    knowledgePointOptions.value = await practiceApi.listKnowledgePointOptions(search)
  } catch {
    knowledgePointOptions.value = []
  } finally {
    kpLoading.value = false
  }
}

useDebouncedWatch(kpSearch, (value) => {
  void loadKnowledgePointOptions(value)
})

onMounted(() => {
  void loadKnowledgePointOptions('')
})

const emptyTestCase = (): TestCaseInput => ({
  input_data: '',
  expected_output: '',
  is_sample: false,
  sort_order: 0,
})

const form = reactive({
  title: '',
  languages: ['Python', 'C++'] as ProblemLanguage[],
  difficulty: '入门' as ProblemDifficulty,
  knowledge_points: [] as string[],
  description: '',
  sample_input: '',
  sample_output: '',
  reference_answer: '',
  time_limit_ms: 1000,
  memory_limit_mb: 256,
  test_cases: [emptyTestCase()] as TestCaseInput[],
  image_urls: [] as string[],
})

const resetForm = () => {
  form.title = ''
  form.languages = ['Python', 'C++']
  form.difficulty = '入门'
  form.knowledge_points = []
  form.description = ''
  form.sample_input = ''
  form.sample_output = ''
  form.reference_answer = ''
  form.time_limit_ms = 1000
  form.memory_limit_mb = 256
  form.test_cases = [emptyTestCase()]
  form.image_urls = []
}

const resolveMediaUrl = (url: string) => {
  if (url.startsWith('http') || url.startsWith('blob:')) return url
  const base = import.meta.env.VITE_API_BASE ?? ''
  return `${base}${url.startsWith('/') ? url : `/${url}`}`
}

const onPickProblemImage = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file || form.image_urls.length >= 5) return
  try {
    const url = await suggestionApi.uploadImage(file)
    form.image_urls.push(url)
  } catch (err) {
    formError.value = err instanceof Error ? err.message : '图片上传失败'
  }
}

const removeProblemImage = (index: number) => {
  form.image_urls.splice(index, 1)
}

watch(
  () => props.problem,
  (problem) => {
    if (!problem) {
      resetForm()
      return
    }
    form.title = problem.title
    form.languages =
      problem.languages?.length > 0
        ? [...problem.languages]
        : [problem.language]
    form.difficulty = problem.difficulty
    form.knowledge_points =
      problem.knowledge_points?.length > 0
        ? [...problem.knowledge_points]
        : problem.knowledge_point
          ? [problem.knowledge_point]
          : []
    form.description = problem.description
    form.sample_input = problem.sample_input || ''
    form.sample_output = problem.sample_output || ''
    form.reference_answer = problem.reference_answer || ''
    form.time_limit_ms = problem.time_limit_ms
    form.memory_limit_mb = problem.memory_limit_mb
    form.test_cases = problem.test_cases.map((tc) => ({
      input_data: tc.input_data,
      expected_output: tc.expected_output,
      is_sample: tc.is_sample,
      sort_order: tc.sort_order,
    }))
    form.image_urls = problem.image_urls ? [...problem.image_urls] : []
  },
  { immediate: true },
)

const addTestCase = () => {
  form.test_cases.push(emptyTestCase())
}

const removeTestCase = (index: number) => {
  form.test_cases.splice(index, 1)
}

const buildPayload = () => ({
  title: form.title.trim(),
  description: form.description.trim(),
  languages: isEdit.value ? [...form.languages] : (['Python', 'C++'] as ProblemLanguage[]),
  difficulty: form.difficulty,
  knowledge_points: [...form.knowledge_points],
  sample_input: form.sample_input || undefined,
  sample_output: form.sample_output || undefined,
  reference_answer: form.reference_answer || undefined,
  time_limit_ms: form.time_limit_ms,
  memory_limit_mb: form.memory_limit_mb,
  test_cases: form.test_cases
    .map((tc, index) => ({
      input_data: tc.input_data.trim(),
      expected_output: tc.expected_output.trim(),
      is_sample: tc.is_sample,
      sort_order: index,
    }))
    .filter((tc) => tc.expected_output),
  image_urls: [...form.image_urls],
})

const submit = async () => {
  formError.value = ''
  const parsed = problemFormSchema.safeParse(buildPayload())
  if (!parsed.success) {
    formError.value = formatZodErrors(parsed.error)
    return
  }

  submitting.value = true
  try {
    const payload = parsed.data
    if (props.onSave) {
      const saved = await props.onSave(payload, isEdit.value, props.problem?.id)
      emit('success', isEdit.value ? 'update' : 'create', saved ?? props.problem ?? undefined)
    } else if (isEdit.value && props.problem) {
      const updated = await problemApi.update(props.problem.id, payload)
      emit('success', 'update', updated)
    } else {
      const created = await problemApi.create(payload)
      emit('success', 'create', created)
    }
    emit('close')
  } catch (err) {
    formError.value = err instanceof Error ? err.message : '提交失败'
  } finally {
    submitting.value = false
  }
}
</script>

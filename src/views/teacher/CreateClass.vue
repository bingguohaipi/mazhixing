<template>
  <div>
    <div class="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-3">
      <button @click="router.push('/teacher/classes')" class="p-1.5 rounded-lg hover:bg-gray-100 text-gray-600">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
      </button>
      <h1 class="text-lg font-semibold text-gray-900">创建班级</h1>
    </div>
    <div class="p-6">
      <div class="bg-white rounded-xl border border-gray-100 p-6 space-y-5 max-w-4xl mx-auto">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">班级名称 <span class="text-red-500">*</span></label>
          <input v-model="form.name" type="text" placeholder="例如：C++信奥A班" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent" />
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">课程类型 <span class="text-red-500">*</span></label>
            <select
              v-model="form.course_type"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-white"
            >
              <option disabled value="">请选择 Python 或 C++</option>
              <option v-for="lang in CLASS_COURSE_TYPES" :key="lang" :value="lang">{{ lang }}</option>
            </select>
            <p class="text-xs text-gray-500 mt-1">决定本班学生做题时的默认编程语言</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">上课时间 <span class="text-red-500">*</span></label>
            <input v-model="form.schedule" type="text" placeholder="例如：周六 14:00-16:00" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent" />
          </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">预计人数</label>
            <input v-model.number="form.expected_student_count" type="number" placeholder="30" min="1" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">总课时</label>
            <input v-model.number="form.lesson_count" type="number" placeholder="16" min="1" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent" />
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">班级简介</label>
          <textarea v-model="form.description" rows="3" placeholder="简要描述班级定位、适合人群等" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"></textarea>
        </div>
        <div v-if="formError" class="text-sm text-red-500">{{ formError }}</div>
        <div class="flex justify-end gap-3 pt-2">
          <button @click="router.push('/teacher/classes')" class="px-5 py-2 border border-gray-300 text-gray-700 text-sm rounded-lg hover:bg-gray-50">取消</button>
          <button @click="handleSubmit" :disabled="submitting" class="px-5 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-60">
            {{ submitting ? '创建中...' : '确认创建' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { classApi } from '@/api/classes'
import { trackEvent } from '@/utils/tracker'
import { CLASS_COURSE_TYPES } from '@/constants/class-course'

const router = useRouter()
const submitting = ref(false)
const formError = ref('')
const existingClassNames = ref<string[]>([])

onMounted(async () => {
  try {
    const list = await classApi.list()
    existingClassNames.value = list.map((item) => item.name.trim())
  } catch {
    /* 列表加载失败时仍依赖后端校验 */
  }
})

const form = ref({
  name: '',
  course_type: '',
  schedule: '',
  expected_student_count: 30,
  lesson_count: 16,
  description: '',
})

const handleSubmit = async () => {
  formError.value = ''
  const trimmedName = form.value.name.trim()
  if (!trimmedName) {
    formError.value = '请输入班级名称'
    return
  }
  if (existingClassNames.value.includes(trimmedName)) {
    formError.value = '班级名称已存在，请使用其他名称'
    return
  }
  if (!CLASS_COURSE_TYPES.includes(form.value.course_type as (typeof CLASS_COURSE_TYPES)[number])) {
    formError.value = '请选择课程类型（Python 或 C++）'
    return
  }
  if (!form.value.schedule.trim()) {
    formError.value = '请输入上课时间'
    return
  }

  submitting.value = true
  try {
    const created = await classApi.create({
      name: trimmedName,
      course_type: form.value.course_type.trim(),
      schedule: form.value.schedule.trim(),
      expected_student_count: form.value.expected_student_count,
      lesson_count: form.value.lesson_count,
      description: form.value.description.trim() || undefined,
    })
    trackEvent({ event_name: 'class_create', page: '/teacher/classes/create', module: 'teacher', detail: `id=${created.id}` })
    router.push(`/teacher/classes/${created.id}`)
  } catch (err) {
    formError.value = err instanceof Error ? err.message : '创建失败'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="modal-mask">
    <div class="modal-box" style="width: 520px; max-height: 85vh; overflow-y: auto;">
      <h3 class="modal-title">编辑班级</h3>
      <p class="modal-sub">修改班级基本信息</p>
      <div class="modal-field">
        <label class="modal-label">班级名称 <span style="color:#ef4444">*</span></label>
        <input type="text" class="modal-input" v-model="form.name">
      </div>
      <div class="modal-field">
        <label class="modal-label">课程类型 <span style="color:#ef4444">*</span></label>
        <select v-model="form.course_type" class="modal-input">
          <option v-for="lang in CLASS_COURSE_TYPES" :key="lang" :value="lang">{{ lang }}</option>
        </select>
        <p class="text-xs text-gray-500 mt-1">本班学生做题时的默认编程语言</p>
      </div>
      <div class="modal-field">
        <label class="modal-label">上课时间 <span style="color:#ef4444">*</span></label>
        <input type="text" class="modal-input" v-model="form.schedule">
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div class="modal-field">
          <label class="modal-label">预计人数</label>
          <input type="number" class="modal-input" v-model.number="form.expected_student_count" min="1">
        </div>
        <div class="modal-field">
          <label class="modal-label">总课时</label>
          <input type="number" class="modal-input" v-model.number="form.lesson_count" min="1">
        </div>
      </div>
      <div class="modal-field">
        <label class="modal-label">班级简介</label>
        <textarea class="modal-input" v-model="form.description" rows="2" style="resize: vertical;"></textarea>
      </div>
      <div v-if="formError" class="modal-error show" style="margin-bottom: 12px;">{{ formError }}</div>
      <div class="modal-actions">
        <button class="modal-btn-cancel" @click="$emit('close')">取消</button>
        <button class="modal-btn-confirm" :disabled="submitting" @click="submit">
          {{ submitting ? '保存中...' : '保存' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { classApi } from '@/api/classes'
import type { ClassDetail } from '@/types/class'
import { CLASS_COURSE_TYPES } from '@/constants/class-course'
import { courseTypeToCodingLanguage } from '@/utils/class-course-language'

const props = defineProps<{ classData: ClassDetail }>()
const emit = defineEmits<{ close: []; success: [] }>()

const form = reactive({
  name: '',
  course_type: '',
  schedule: '',
  expected_student_count: 30,
  lesson_count: 16,
  description: '',
})

const submitting = ref(false)
const formError = ref('')

watch(
  () => props.classData,
  (data) => {
    form.name = data.name
    form.course_type = courseTypeToCodingLanguage(data.course_type) ?? data.course_type
    form.schedule = data.schedule
    form.expected_student_count = data.expected_student_count
    form.lesson_count = data.lesson_count
    form.description = data.description || ''
  },
  { immediate: true },
)

const submit = async () => {
  formError.value = ''
  if (!form.name.trim() || !form.schedule.trim()) {
    formError.value = '请填写必填项'
    return
  }
  if (!CLASS_COURSE_TYPES.includes(form.course_type as (typeof CLASS_COURSE_TYPES)[number])) {
    formError.value = '请选择课程类型（Python 或 C++）'
    return
  }

  submitting.value = true
  try {
    await classApi.update(props.classData.id, {
      name: form.name.trim(),
      course_type: form.course_type.trim(),
      schedule: form.schedule.trim(),
      expected_student_count: form.expected_student_count,
      lesson_count: form.lesson_count,
      description: form.description.trim() || undefined,
    })
    emit('success')
    emit('close')
  } catch (err) {
    formError.value = err instanceof Error ? err.message : '保存失败'
  } finally {
    submitting.value = false
  }
}
</script>

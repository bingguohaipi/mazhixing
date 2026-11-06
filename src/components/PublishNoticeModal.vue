<template>
  <div class="modal-mask">
    <div class="modal-box" style="width: 480px;">
      <h3 class="modal-title">发布通知</h3>
      <p class="modal-sub">向指定班级的学生和家长发送通知</p>

      <div v-if="loadingClasses" class="text-sm text-gray-500 py-4 text-center">加载班级...</div>

      <template v-else>
        <div class="modal-field">
          <label class="modal-label">通知标题</label>
          <input
            v-model="form.title"
            type="text"
            class="modal-input"
            placeholder="请输入通知标题"
            maxlength="50"
          >
        </div>
        <div class="modal-field">
          <label class="modal-label">通知内容</label>
          <textarea
            v-model="form.content"
            class="modal-input"
            placeholder="请输入通知内容..."
            rows="5"
            style="resize: vertical; min-height: 100px;"
          ></textarea>
        </div>
        <div class="modal-field">
          <label class="modal-label">发送至</label>
          <div v-if="classes.length === 0" class="text-sm text-gray-500 py-2">
            暂无班级，请先创建班级
          </div>
          <div v-else class="notice-class-list">
            <label class="notice-class-item">
              <input type="checkbox" v-model="selectAll" @change="toggleAll">
              <span>全部班级</span>
            </label>
            <label v-for="cls in classes" :key="cls.id" class="notice-class-item">
              <input v-model="form.selectedClasses" type="checkbox" :value="cls.id">
              <span>{{ cls.name }}（{{ cls.student_count }}人）</span>
            </label>
          </div>
        </div>
        <p v-if="error" class="text-sm text-red-500 mb-2">{{ error }}</p>
      </template>

      <div class="modal-actions">
        <button class="modal-btn-cancel" @click="$emit('close')">取消</button>
        <button
          class="modal-btn-confirm"
          :disabled="submitting || loadingClasses || classes.length === 0"
          @click="submit"
        >
          {{ submitting ? '发布中...' : '发布' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { classApi } from '@/api/classes'
import { noticeApi } from '@/api/notices'
import type { ClassListItem } from '@/types/class'
import { trackEvent } from '@/utils/tracker'

const emit = defineEmits<{ close: []; published: [] }>()

const classes = ref<ClassListItem[]>([])
const loadingClasses = ref(true)
const submitting = ref(false)
const error = ref('')
const selectAll = ref(false)

const form = reactive({
  title: '',
  content: '',
  selectedClasses: [] as number[],
})

watch(
  () => form.selectedClasses.length,
  () => {
    selectAll.value = classes.value.length > 0 && form.selectedClasses.length === classes.value.length
  },
)

const toggleAll = () => {
  if (selectAll.value) {
    form.selectedClasses = classes.value.map((c) => c.id)
  } else {
    form.selectedClasses = []
  }
}

const loadClasses = async () => {
  loadingClasses.value = true
  error.value = ''
  try {
    classes.value = await classApi.list()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载班级失败'
  } finally {
    loadingClasses.value = false
  }
}

const submit = async () => {
  if (!form.title.trim()) {
    error.value = '请输入通知标题'
    return
  }
  if (!form.content.trim()) {
    error.value = '请输入通知内容'
    return
  }
  if (form.selectedClasses.length === 0) {
    error.value = '请至少选择一个发送班级'
    return
  }

  submitting.value = true
  error.value = ''
  try {
    await noticeApi.create({
      title: form.title.trim(),
      content: form.content.trim(),
      class_ids: form.selectedClasses,
    })
    trackEvent({
      event_name: 'notice_publish',
      page: '/teacher/dashboard',
      module: 'teacher',
      detail: `classes=${form.selectedClasses.length}`,
    })
    emit('published')
    emit('close')
  } catch (err) {
    error.value = err instanceof Error ? err.message : '发布失败，请稍后重试'
  } finally {
    submitting.value = false
  }
}

onMounted(loadClasses)
</script>

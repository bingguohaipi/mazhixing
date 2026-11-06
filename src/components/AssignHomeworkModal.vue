<template>
  <div class="modal-mask">
    <div class="modal-box" style="width: 560px; max-height: 90vh; overflow-y: auto;">
      <h3 class="modal-title">布置作业</h3>
      <p class="modal-sub">选择班级、题目并设置截止时间</p>

      <div class="modal-field">
        <label class="modal-label">作业名称 <span style="color:#ef4444">*</span></label>
        <input type="text" class="modal-input" v-model="form.title" placeholder="例如：循环结构练习">
      </div>

      <div class="modal-field">
        <label class="modal-label">选择班级 <span style="color:#ef4444">*</span></label>
        <div v-if="loadingOptions" class="text-sm text-gray-400 py-2">加载中...</div>
        <div v-else-if="classes.length === 0" class="text-sm text-amber-600 py-2">暂无班级，请先创建班级</div>
        <div v-else class="notice-class-list">
          <label v-for="cls in classes" :key="cls.id" class="notice-class-item">
            <input type="checkbox" v-model="form.class_ids" :value="cls.id">
            <span>{{ cls.name }}（{{ cls.student_count }}人）</span>
          </label>
        </div>
      </div>

      <div class="modal-field">
        <div class="flex items-center justify-between gap-2 mb-2">
          <label class="modal-label" style="margin:0">选择题目 <span style="color:#ef4444">*</span></label>
          <button type="button" class="text-sm text-indigo-400 hover:text-indigo-300 shrink-0" @click="openCustomProblemForm">
            + 自行出题
          </button>
        </div>
        <div v-if="loadingOptions" class="text-sm text-gray-400 py-2">加载中...</div>
        <template v-else>
          <p class="text-xs text-gray-500 mb-2">
            公共题、自有题均支持搜索与筛选（难度、知识点）；也可「自行出题」新建
          </p>
          <div class="space-y-3">
            <PublicProblemSearchList
              v-model:keyword="publicKeyword"
              v-model:difficulty="publicFilters.difficulty"
              v-model:knowledge-point="publicFilters.knowledgePoint"
              :active-filter-count="publicActiveFilterCount"
              :has-search-criteria="publicHasSearchCriteria"
              :knowledge-point-options="knowledgePointOptions"
              :loading="publicSearchLoading"
              :displayed="publicDisplayed"
              :selected-ids="form.problem_ids"
              :selected-public-count="selectedPublicCount"
              @apply-filters="applyPublicFilters"
              @reset-filters="resetPublicFilters"
              @update:selected-ids="(ids) => (form.problem_ids = ids)"
            />
            <CustomProblemPickList
              v-model:keyword="customKeyword"
              v-model:difficulty="customFilters.difficulty"
              v-model:knowledge-point="customFilters.knowledgePoint"
              :active-filter-count="customActiveFilterCount"
              :has-search-criteria="customHasSearchCriteria"
              :knowledge-point-options="knowledgePointOptions"
              :loading="customSearchLoading"
              :displayed="customDisplayed"
              :selected-ids="form.problem_ids"
              :selected-custom-count="selectedCustomCount"
              @apply-filters="applyCustomFilters"
              @reset-filters="resetCustomFilters"
              @update:selected-ids="(ids) => (form.problem_ids = ids)"
              @edit="openEditCustomProblem"
            />
          </div>
        </template>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div class="modal-field">
          <label class="modal-label">开始时间 <span style="color:#ef4444">*</span></label>
          <input type="datetime-local" class="modal-input" v-model="form.start_time">
        </div>
        <div class="modal-field">
          <label class="modal-label">截止时间 <span style="color:#ef4444">*</span></label>
          <input type="datetime-local" class="modal-input" v-model="form.end_time">
        </div>
      </div>

      <div class="modal-field">
        <label class="notice-class-item" style="cursor:pointer;">
          <input type="checkbox" v-model="form.allow_late_submission">
          <span>允许截止后补交（补交作业将单独标记，不计入常规统计）</span>
        </label>
      </div>

      <div class="modal-field">
        <label class="notice-class-item" style="cursor:pointer;">
          <input type="checkbox" v-model="targetSpecificStudents">
          <span>仅指定部分学生（不勾选则推送给所选班级全部学生）</span>
        </label>
      </div>

      <div v-if="targetSpecificStudents" class="modal-field">
        <label class="modal-label">选择学生</label>
        <div v-if="form.class_ids.length === 0" class="text-sm text-amber-600 py-2">请先选择班级</div>
        <div v-else-if="loadingStudents" class="text-sm text-gray-400 py-2">加载学生...</div>
        <div v-else-if="availableStudents.length === 0" class="text-sm text-amber-600 py-2">所选班级暂无学生</div>
        <div v-else class="notice-class-list" style="max-height: 160px; overflow-y: auto;">
          <label v-for="student in availableStudents" :key="student.id" class="notice-class-item">
            <input type="checkbox" v-model="form.student_ids" :value="student.id">
            <span>{{ student.display_name }}（{{ student.account }}）</span>
          </label>
        </div>
      </div>

      <div class="modal-field">
        <label class="modal-label">作业说明</label>
        <textarea class="modal-input" v-model="form.description" rows="2" placeholder="可选：补充说明、注意事项等" style="resize: vertical;"></textarea>
      </div>

      <div v-if="formError" class="modal-error show" style="margin-bottom: 12px;">{{ formError }}</div>
      <div class="modal-actions">
        <button class="modal-btn-cancel" @click="$emit('close')">取消</button>
        <button class="modal-btn-confirm" :disabled="submitting" @click="submit">
          {{ submitting ? '提交中...' : '确认布置' }}
        </button>
      </div>
    </div>

    <ProblemFormModal
      v-if="showProblemForm"
      :problem="editingProblem"
      @close="closeProblemForm"
      @success="onCustomProblemSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, toRef, watch } from 'vue'
import CustomProblemPickList from '@/components/CustomProblemPickList.vue'
import ProblemFormModal from '@/components/ProblemFormModal.vue'
import PublicProblemSearchList from '@/components/PublicProblemSearchList.vue'
import { useCustomProblemSearch } from '@/composables/useCustomProblemSearch'
import { usePublicProblemSearch } from '@/composables/usePublicProblemSearch'
import { classApi } from '@/api/classes'
import { homeworkApi } from '@/api/homework'
import { practiceApi } from '@/api/practice'
import { problemApi } from '@/api/problems'
import type { KnowledgePointOptionItem } from '@/types/practice'
import type { ClassListItem, ClassStudentItem } from '@/types/class'
import type { ProblemDetail } from '@/types/problem'
import { problemDetailToListItem } from '@/utils/problem-list'
import { toast } from '@/utils/toast'
import { trackEvent } from '@/utils/tracker'

const emit = defineEmits<{ close: []; success: [] }>()

const form = reactive({
  title: '',
  class_ids: [] as number[],
  problem_ids: [] as number[],
  student_ids: [] as number[],
  start_time: '',
  end_time: '',
  allow_late_submission: false,
  description: '',
})

const classes = ref<ClassListItem[]>([])
const knowledgePointOptions = ref<KnowledgePointOptionItem[]>([])
const {
  keyword: publicKeyword,
  filters: publicFilters,
  activeFilterCount: publicActiveFilterCount,
  hasSearchCriteria: publicHasSearchCriteria,
  loading: publicSearchLoading,
  displayed: publicDisplayed,
  applyFilters: applyPublicFilters,
  onResetFilters: resetPublicFilters,
} = usePublicProblemSearch(toRef(form, 'problem_ids'))
const {
  keyword: customKeyword,
  filters: customFilters,
  activeFilterCount: customActiveFilterCount,
  hasSearchCriteria: customHasSearchCriteria,
  loading: customSearchLoading,
  displayed: customDisplayed,
  customProblemIdSet,
  mergeItem: mergeCustomSearchItem,
  applyFilters: applyCustomFilters,
  onResetFilters: resetCustomFilters,
} = useCustomProblemSearch(toRef(form, 'problem_ids'))
const selectedPublicCount = computed(
  () => form.problem_ids.filter((id) => !customProblemIdSet.value.has(id)).length,
)
const selectedCustomCount = computed(
  () => form.problem_ids.filter((id) => customProblemIdSet.value.has(id)).length,
)
const showProblemForm = ref(false)
const editingProblem = ref<ProblemDetail | null>(null)
const availableStudents = ref<ClassStudentItem[]>([])
const loadingOptions = ref(true)
const loadingStudents = ref(false)
const submitting = ref(false)
const targetSpecificStudents = ref(false)
const formError = ref('')

const toLocalDatetime = (date: Date): string => {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

const toIsoString = (localValue: string): string => {
  return new Date(localValue).toISOString()
}

const loadOptions = async () => {
  loadingOptions.value = true
  try {
    classes.value = await classApi.list()
  } catch (err) {
    formError.value = err instanceof Error ? err.message : '加载选项失败'
  } finally {
    loadingOptions.value = false
  }
}

const loadStudentsForClasses = async () => {
  if (form.class_ids.length === 0) {
    availableStudents.value = []
    form.student_ids = []
    return
  }
  loadingStudents.value = true
  try {
    const results = await Promise.all(form.class_ids.map((classId) => classApi.listStudents(classId)))
    const merged = new Map<number, ClassStudentItem>()
    results.flat().forEach((student) => merged.set(student.id, student))
    availableStudents.value = Array.from(merged.values())
    form.student_ids = form.student_ids.filter((id) => merged.has(id))
  } catch (err) {
    formError.value = err instanceof Error ? err.message : '加载学生失败'
  } finally {
    loadingStudents.value = false
  }
}

watch(
  () => [...form.class_ids],
  () => {
    if (targetSpecificStudents.value) {
      loadStudentsForClasses()
    }
  },
)

watch(targetSpecificStudents, (enabled) => {
  if (enabled) {
    loadStudentsForClasses()
  } else {
    form.student_ids = []
  }
})

const closeProblemForm = () => {
  showProblemForm.value = false
  editingProblem.value = null
}

const openCustomProblemForm = () => {
  editingProblem.value = null
  showProblemForm.value = true
}

const openEditCustomProblem = async (problemId: number) => {
  try {
    editingProblem.value = await problemApi.get(problemId)
    showProblemForm.value = true
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '加载题目失败')
  }
}

const mergeCustomProblem = (detail: ProblemDetail) => {
  const item = problemDetailToListItem(detail)
  if (!item.is_publishable) {
    toast.error('题目需至少一组有效测试用例才能用于布置作业')
    return false
  }
  mergeCustomSearchItem(item)
  return true
}

const onCustomProblemSaved = (action: 'create' | 'update', detail?: ProblemDetail) => {
  closeProblemForm()
  if (!detail) return
  if (!mergeCustomProblem(detail)) return
  if (action === 'create') {
    if (!form.problem_ids.includes(detail.id)) {
      form.problem_ids.push(detail.id)
    }
    toast.success('题目已创建并已勾选')
    trackEvent({ event_name: 'problem_create', page: '/teacher/homework', module: 'teacher', detail: `id=${detail.id}` })
  } else {
    toast.success('题目已更新')
    trackEvent({ event_name: 'problem_update', page: '/teacher/homework', module: 'teacher', detail: `id=${detail.id}` })
  }
}

const submit = async () => {
  formError.value = ''
  if (!form.title.trim()) {
    formError.value = '请输入作业名称'
    return
  }
  if (form.class_ids.length === 0) {
    formError.value = '请至少选择一个班级'
    return
  }
  if (form.problem_ids.length === 0) {
    formError.value = '请至少选择一道题目'
    return
  }
  if (!form.start_time || !form.end_time) {
    formError.value = '请设置开始和截止时间'
    return
  }
  if (new Date(form.end_time) <= new Date(form.start_time)) {
    formError.value = '截止时间必须晚于开始时间'
    return
  }
  if (targetSpecificStudents.value && form.student_ids.length === 0) {
    formError.value = '请至少选择一名学生'
    return
  }

  submitting.value = true
  try {
    const { data: created, message } = await homeworkApi.create({
      title: form.title.trim(),
      description: form.description.trim() || undefined,
      start_time: toIsoString(form.start_time),
      end_time: toIsoString(form.end_time),
      allow_late_submission: form.allow_late_submission,
      class_ids: form.class_ids,
      problem_ids: form.problem_ids,
      student_ids: targetSpecificStudents.value ? form.student_ids : undefined,
    })
    trackEvent({
      event_name: 'homework_publish',
      page: '/teacher/homework',
      module: 'teacher',
      detail: `id=${created.id},late=${form.allow_late_submission}`,
    })
    if (form.allow_late_submission) {
      trackEvent({
        event_name: 'homework_allow_late_on',
        page: '/teacher/homework',
        module: 'teacher',
        detail: `id=${created.id},source=create`,
      })
    }
    toast.success(message)
    emit('success')
    emit('close')
  } catch (err) {
    formError.value = err instanceof Error ? err.message : '布置失败'
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  const now = new Date()
  const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000)
  form.start_time = toLocalDatetime(now)
  form.end_time = toLocalDatetime(tomorrow)
  try {
    knowledgePointOptions.value = await practiceApi.listKnowledgePointOptions()
  } catch {
    knowledgePointOptions.value = []
  }
  loadOptions()
})
</script>

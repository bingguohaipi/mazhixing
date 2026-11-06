<template>
  <div class="modal-mask">
    <div class="modal-box" style="width: 620px; max-height: 90vh; overflow-y: auto;">
      <div v-if="loading" class="py-16 text-center text-gray-500">加载中...</div>

      <!-- 查看模式 -->
      <template v-else-if="detail && mode === 'view'">
        <div class="flex items-start justify-between mb-1">
          <h3 class="modal-title" style="margin:0">{{ detail.title }}</h3>
          <span class="badge shrink-0 ml-2" :class="getStatusClass(detail.status)">{{ detail.status }}</span>
        </div>
        <p class="modal-sub">作业详情与操作管理</p>

        <div class="grid grid-cols-2 gap-3 mb-2 text-center">
          <div class="bg-gray-50 rounded-lg py-2">
            <div class="text-lg font-bold text-gray-900">{{ detail.submitted_count }}/{{ detail.total_students }}</div>
            <div class="text-xs text-gray-500">已完成人数</div>
          </div>
          <div class="bg-gray-50 rounded-lg py-2">
            <div class="text-lg font-bold text-green-600">{{ detail.correct_count }}</div>
            <div class="text-xs text-gray-500">全对人数</div>
          </div>
        </div>
        <p class="text-xs text-gray-400 mb-4">
          修改作业题目数量并保存后，此处会立即重算；只改题目内容/用例不会自动重判学生历史提交。
        </p>

        <div class="space-y-3 text-sm mb-4">
          <div class="flex gap-2">
            <span class="text-gray-500 w-20 shrink-0">发布班级</span>
            <span class="text-gray-900">{{ detail.classes.map(c => c.name).join('、') || '-' }}</span>
          </div>
          <div class="flex gap-2">
            <span class="text-gray-500 w-20 shrink-0">开始时间</span>
            <span class="text-gray-900">{{ formatTime(detail.start_time) }}</span>
          </div>
          <div class="flex gap-2">
            <span class="text-gray-500 w-20 shrink-0">截止时间</span>
            <span class="text-gray-900">{{ formatTime(detail.end_time) }}</span>
          </div>
          <div class="flex gap-2">
            <span class="text-gray-500 w-20 shrink-0">补交权限</span>
            <span :class="detail.allow_late_submission ? 'text-indigo-600' : 'text-gray-500'">
              {{ detail.allow_late_submission ? '已开启' : '未开启' }}
            </span>
          </div>
          <div v-if="(detail.late_submission_count ?? 0) > 0" class="flex gap-2">
            <span class="text-gray-500 w-20 shrink-0">补交人数</span>
            <span class="text-amber-600">{{ detail.late_submission_count }} 人（单独统计）</span>
          </div>
          <div v-if="detail.description" class="flex gap-2">
            <span class="text-gray-500 w-20 shrink-0">作业说明</span>
            <span class="text-gray-900 whitespace-pre-wrap">{{ detail.description }}</span>
          </div>
        </div>

        <div class="mb-4">
          <div class="text-sm font-medium text-gray-700 mb-2">题目列表（{{ detail.problems.length }} 道）</div>
          <div class="border border-gray-100 rounded-lg divide-y divide-gray-50 max-h-40 overflow-y-auto">
            <div v-for="(p, idx) in detail.problems" :key="p.id" class="px-3 py-2 text-sm flex items-center justify-between">
              <span class="text-gray-900">{{ idx + 1 }}. #{{ p.id }} {{ p.title }}</span>
              <span class="text-gray-400 text-xs">{{ p.language }} · {{ p.difficulty }}</span>
            </div>
          </div>
        </div>

        <div class="flex flex-wrap gap-2 mb-4 pt-2 border-t border-gray-100">
          <button
            type="button"
            class="px-3 py-1.5 text-sm border border-gray-300 text-gray-800 rounded-lg hover:bg-gray-50"
            @click="showStudentReport = true"
          >
            学生作答情况
          </button>
          <button
            v-if="detail.status === '未开始' || detail.status === '进行中'"
            class="px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            @click="mode = 'edit'"
          >
            {{ detail.status === '进行中' ? '修改题目' : '编辑作业' }}
          </button>
          <button
            v-if="detail.status !== '已撤回' && detail.status !== '已截止'"
            class="px-3 py-1.5 text-sm border border-red-200 text-red-600 rounded-lg hover:bg-red-50"
            @click="handleWithdraw"
          >
            撤回作业
          </button>
          <button
            class="px-3 py-1.5 text-sm border border-red-300 text-red-700 rounded-lg hover:bg-red-50"
            @click="handleDelete"
          >
            删除作业
          </button>
          <button
            v-if="detail.status === '已截止'"
            class="px-3 py-1.5 text-sm border border-indigo-300 text-indigo-600 rounded-lg hover:bg-indigo-50"
            @click="handleToggleLate"
          >
            {{ detail.allow_late_submission ? '关闭补交' : '开启补交' }}
          </button>
        </div>

        <div class="modal-actions">
          <button class="modal-btn-cancel" @click="$emit('close')">关闭</button>
        </div>

        <HomeworkStudentReportModal
          v-if="showStudentReport"
          :homework-id="detail.id"
          @close="showStudentReport = false"
        />
      </template>

      <!-- 编辑模式 -->
      <template v-else-if="detail && mode === 'edit'">
        <h3 class="modal-title">编辑作业</h3>
        <p class="modal-sub">
          保存后将向作业所属班级的学生发送更新通知（通知中心 + 作业「有更新」标记）
        </p>

        <div class="modal-field">
          <label class="modal-label">作业名称 <span style="color:#ef4444">*</span></label>
          <input type="text" class="modal-input" v-model="form.title">
        </div>

        <div v-if="detail.status !== '进行中'" class="modal-field">
          <label class="modal-label">选择班级 <span style="color:#ef4444">*</span></label>
          <div class="notice-class-list">
            <label v-for="cls in classes" :key="cls.id" class="notice-class-item">
              <input type="checkbox" v-model="form.class_ids" :value="cls.id">
              <span>{{ cls.name }}（{{ cls.student_count }}人）</span>
            </label>
          </div>
        </div>

        <div class="modal-field">
          <div class="flex items-center justify-between gap-2 mb-2">
            <label class="modal-label" style="margin:0">选择题目 <span style="color:#ef4444">*</span></label>
            <button type="button" class="text-sm text-indigo-400 hover:text-indigo-300 shrink-0" @click="openCreateCustomProblem">
              + 自行出题
            </button>
          </div>
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
            class="mt-3"
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

        <div class="grid grid-cols-2 gap-3">
          <div v-if="detail.status !== '进行中'" class="modal-field">
            <label class="modal-label">开始时间 <span style="color:#ef4444">*</span></label>
            <input type="datetime-local" class="modal-input" v-model="form.start_time">
          </div>
          <div class="modal-field" :class="detail.status === '进行中' ? 'col-span-2' : ''">
            <label class="modal-label">截止时间 <span style="color:#ef4444">*</span></label>
            <input type="datetime-local" class="modal-input" v-model="form.end_time">
          </div>
        </div>

        <div class="modal-field">
          <label class="notice-class-item" style="cursor:pointer;">
            <input type="checkbox" v-model="form.allow_late_submission">
            <span>允许截止后补交</span>
          </label>
        </div>

        <div class="modal-field">
          <label class="modal-label">作业说明</label>
          <textarea class="modal-input" v-model="form.description" rows="2" style="resize: vertical;"></textarea>
        </div>

        <div v-if="formError" class="modal-error show" style="margin-bottom: 12px;">{{ formError }}</div>
        <div class="modal-actions">
          <button class="modal-btn-cancel" @click="mode = 'view'">返回查看</button>
          <button class="modal-btn-confirm" :disabled="submitting" @click="submitEdit">
            {{ submitting ? '保存中...' : '保存修改' }}
          </button>
        </div>
      </template>
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
import { computed, onMounted, reactive, ref, toRef } from 'vue'
import CustomProblemPickList from '@/components/CustomProblemPickList.vue'
import HomeworkStudentReportModal from '@/components/HomeworkStudentReportModal.vue'
import ProblemFormModal from '@/components/ProblemFormModal.vue'
import PublicProblemSearchList from '@/components/PublicProblemSearchList.vue'
import { useCustomProblemSearch } from '@/composables/useCustomProblemSearch'
import { usePublicProblemSearch } from '@/composables/usePublicProblemSearch'
import { classApi } from '@/api/classes'
import { homeworkApi } from '@/api/homework'
import { toast } from '@/utils/toast'
import { practiceApi } from '@/api/practice'
import { problemApi } from '@/api/problems'
import type { KnowledgePointOptionItem } from '@/types/practice'
import type { ClassListItem } from '@/types/class'
import type { HomeworkDetail, HomeworkStatus } from '@/types/homework'
import type { ProblemDetail, ProblemListItem } from '@/types/problem'
import { problemDetailToListItem } from '@/utils/problem-list'
import { trackEvent } from '@/utils/tracker'

const props = defineProps<{ homeworkId: number }>()
const emit = defineEmits<{ close: []; changed: [] }>()

const detail = ref<HomeworkDetail | null>(null)
const loading = ref(true)
const mode = ref<'view' | 'edit'>('view')
const submitting = ref(false)
const formError = ref('')

const classes = ref<ClassListItem[]>([])
const showStudentReport = ref(false)
const showProblemForm = ref(false)
const editingProblem = ref<ProblemDetail | null>(null)

const form = reactive({
  title: '',
  class_ids: [] as number[],
  problem_ids: [] as number[],
  start_time: '',
  end_time: '',
  allow_late_submission: false,
  description: '',
})

const knowledgePointOptions = ref<KnowledgePointOptionItem[]>([])
const {
  keyword: publicKeyword,
  filters: publicFilters,
  activeFilterCount: publicActiveFilterCount,
  hasSearchCriteria: publicHasSearchCriteria,
  loading: publicSearchLoading,
  displayed: publicDisplayed,
  seedCache: seedPublicProblemCache,
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
  seedCache: seedCustomProblemCache,
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

const closeProblemForm = () => {
  showProblemForm.value = false
  editingProblem.value = null
}

const openCreateCustomProblem = () => {
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

const refreshDetail = async () => {
  const hw = await homeworkApi.get(props.homeworkId)
  detail.value = hw
  if (mode.value === 'edit') {
    fillForm(hw)
  }
}

const onCustomProblemSaved = async (action: 'create' | 'update', saved?: ProblemDetail) => {
  closeProblemForm()
  if (!saved) return
  const item = problemDetailToListItem(saved)
  if (!item.is_publishable) {
    toast.error('题目需至少一组有效测试用例')
    return
  }
  mergeCustomSearchItem(item)
  if (action === 'create') {
    if (!form.problem_ids.includes(item.id)) {
      form.problem_ids.push(item.id)
    }
    toast.success('题目已创建并已勾选')
  } else {
    toast.success('题目已更新')
  }
  try {
    await refreshDetail()
    emit('changed')
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '刷新作业数据失败')
  }
}

const getStatusClass = (status: HomeworkStatus) => {
  if (status === '进行中') return 'bg-amber-100 text-amber-700'
  if (status === '已截止') return 'bg-gray-100 text-gray-600'
  if (status === '已撤回') return 'bg-red-100 text-red-700'
  return 'bg-indigo-100 text-indigo-700'
}

const formatTime = (iso: string) =>
  new Date(iso).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })

const toLocalDatetime = (date: Date): string => {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

const toIsoString = (localValue: string) => new Date(localValue).toISOString()

const fillForm = (hw: HomeworkDetail) => {
  form.title = hw.title
  form.class_ids = hw.classes.map((c) => c.id)
  form.problem_ids = hw.problems.map((p) => p.id)
  form.start_time = toLocalDatetime(new Date(hw.start_time))
  form.end_time = toLocalDatetime(new Date(hw.end_time))
  form.allow_late_submission = hw.allow_late_submission
  form.description = hw.description || ''
  seedPublicProblemCache(
    hw.problems.map((p) => ({
      id: p.id,
      title: p.title,
      language: p.language as ProblemListItem['language'],
    languages: [p.language as ProblemListItem['language']],
      difficulty: p.difficulty as ProblemListItem['difficulty'],
      gesp_level: 'GESP1' as ProblemListItem['gesp_level'],
      knowledge_point: null,
    knowledge_points: [],
      test_case_count: 1,
      is_publishable: true,
      pass_rate: 0,
      submission_count: 0,
      created_at: '',
    })),
  )
}

const loadDetail = async () => {
  loading.value = true
  try {
    detail.value = await homeworkApi.get(props.homeworkId)
    if (detail.value) fillForm(detail.value)
  } catch (err) {
    alert(err instanceof Error ? err.message : '加载作业详情失败')
    emit('close')
  } finally {
    loading.value = false
  }
}

const seedCustomProblemsFromHomework = async () => {
  if (form.problem_ids.length === 0) return
  try {
    const details = await Promise.all(
      form.problem_ids.map((id) => problemApi.get(id).catch(() => null)),
    )
    const customItems = details
      .filter((d): d is ProblemDetail => d != null && d.private_no != null)
      .map((d) => problemDetailToListItem(d))
      .filter((item) => item.is_publishable)
    seedCustomProblemCache(customItems)
  } catch {
    /* 忽略预载失败，仍可搜索 */
  }
}

const loadOptions = async () => {
  classes.value = await classApi.list()
  await seedCustomProblemsFromHomework()
}

const submitEdit = async () => {
  if (!detail.value) return
  formError.value = ''
  if (!form.title.trim() || form.class_ids.length === 0 || form.problem_ids.length === 0) {
    formError.value = '请填写完整信息'
    return
  }
  if (!form.start_time || !form.end_time || new Date(form.end_time) <= new Date(form.start_time)) {
    formError.value = '请检查时间设置'
    return
  }

  submitting.value = true
  try {
    const payload: Parameters<typeof homeworkApi.update>[1] = {
      title: form.title.trim(),
      description: form.description.trim() || undefined,
      end_time: toIsoString(form.end_time),
      allow_late_submission: form.allow_late_submission,
      problem_ids: form.problem_ids,
    }
    if (detail.value.status !== '进行中') {
      payload.start_time = toIsoString(form.start_time)
      payload.class_ids = form.class_ids
    }
    const { data, message } = await homeworkApi.update(detail.value.id, payload)
    detail.value = data
    mode.value = 'view'
    toast.success(message)
    trackEvent({
      event_name: 'homework_update',
      page: '/teacher/homework',
      module: 'teacher',
      detail: `id=${data.id}`,
    })
    emit('changed')
  } catch (err) {
    formError.value = err instanceof Error ? err.message : '保存失败'
  } finally {
    submitting.value = false
  }
}

const handleWithdraw = async () => {
  if (!detail.value || !confirm(`确定撤回作业「${detail.value.title}」吗？`)) return
  try {
    detail.value = await homeworkApi.withdraw(detail.value.id)
    toast.success('作业已撤回，已通知相关班级学生')
    trackEvent({ event_name: 'homework_withdraw', page: '/teacher/homework', module: 'teacher', detail: `id=${detail.value.id}` })
    emit('changed')
  } catch (err) {
    alert(err instanceof Error ? err.message : '撤回失败')
  }
}

const handleDelete = async () => {
  if (!detail.value) return
  if (
    !confirm(
      `确定删除作业「${detail.value.title}」吗？\n删除后学生端将不再显示，已提交记录保留在系统中。`,
    )
  ) {
    return
  }
  try {
    const message = await homeworkApi.delete(detail.value.id)
    toast.success(message)
    trackEvent({
      event_name: 'homework_delete',
      page: '/teacher/homework',
      module: 'teacher',
      detail: `id=${detail.value.id}`,
    })
    emit('changed')
    emit('close')
  } catch (err) {
    alert(err instanceof Error ? err.message : '删除失败')
  }
}

const handleToggleLate = async () => {
  if (!detail.value) return
  try {
    const enabled = !detail.value.allow_late_submission
    const { data, message } = await homeworkApi.setAllowLate(detail.value.id, enabled)
    detail.value = data
    toast.success(message)
    trackEvent({
      event_name: enabled ? 'homework_allow_late_on' : 'homework_allow_late_off',
      page: '/teacher/homework',
      module: 'teacher',
      detail: `id=${detail.value.id}`,
    })
    emit('changed')
  } catch (err) {
    alert(err instanceof Error ? err.message : '操作失败')
  }
}

onMounted(async () => {
  try {
    knowledgePointOptions.value = await practiceApi.listKnowledgePointOptions()
  } catch {
    knowledgePointOptions.value = []
  }
  await loadDetail()
  await loadOptions()
})
</script>

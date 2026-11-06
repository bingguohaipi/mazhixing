<template>
  <div>
    <div class="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between gap-3">
      <h1 class="text-lg font-semibold text-gray-900 shrink-0">班级管理</h1>
      <div class="flex items-center gap-3 flex-wrap justify-end">
        <div ref="filterAnchorRef" class="relative shrink-0">
          <button
            type="button"
            class="practice-filter-trigger"
            :class="{ 'is-active': activeFilterCount > 0 }"
            aria-label="筛选班级"
            @click.stop="toggleFilter"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-4 w-4">
              <path
                fill-rule="evenodd"
                d="M2 3.5A.5.5 0 0 1 2.5 3h15a.5.5 0 0 1 .394.808l-5.29 6.593A1 1 0 0 0 12.5 11v4.5a.5.5 0 0 1-.276.447l-2 1A.5.5 0 0 1 9.724 16.5V11a1 1 0 0 0-.104-.402L2.606 3.808A.5.5 0 0 1 2.5 3.5Z"
                clip-rule="evenodd"
              />
            </svg>
            <span v-if="activeFilterCount > 0" class="text-xs font-semibold">{{ activeFilterCount }}</span>
          </button>
          <ClassFilterPopover
            :open="filterOpen"
            :weekday="filterWeekday"
            :course-type="filterCourseType"
            @apply="onFilterApply"
            @reset="onFilterReset"
          />
        </div>
        <input
          v-model="keyword"
          type="search"
          placeholder="搜索班级名称"
          class="search-field input-light-bg w-48 rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <button class="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700" @click="router.push('/teacher/classes/create')">
          + 创建班级
        </button>
      </div>
    </div>

    <div class="p-6">
      <div v-if="loading" class="text-center py-16 text-gray-500">加载中...</div>

      <div v-else-if="classes.length === 0" class="text-center py-16">
        <div class="text-4xl mb-3">{{ hasListQuery ? '🔍' : '👥' }}</div>
        <p class="text-gray-500 mb-4">
          {{ hasListQuery ? '暂无符合条件的班级，请调整筛选或搜索条件' : '暂无班级，请先创建班级' }}
        </p>
        <button
          v-if="hasListQuery"
          type="button"
          class="mr-2 rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
          @click="clearListQuery"
        >
          清空条件
        </button>
        <button
          v-if="!hasListQuery"
          class="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700"
          @click="router.push('/teacher/classes/create')"
        >
          创建第一个班级
        </button>
      </div>

      <div v-else class="grid grid-cols-3 gap-4">
        <div v-for="cls in classes" :key="cls.id" class="bg-white rounded-xl border border-gray-100 card-hover">
          <div class="h-20 rounded-t-xl" :class="getGradient(cls.id)"></div>
          <div class="p-4">
            <div class="flex items-center justify-between mb-2">
              <h3 class="font-semibold text-gray-900">{{ cls.name }}</h3>
              <span class="badge bg-green-100 text-green-700">进行中</span>
            </div>
            <p class="text-sm text-gray-500 mb-3">{{ cls.schedule }} · {{ cls.course_type }}</p>
            <div class="flex items-center gap-4 text-sm text-gray-500 mb-4">
              <span>👥 {{ cls.student_count }}人</span>
              <span>📚 {{ cls.lesson_count }}次课</span>
            </div>
            <div class="flex gap-2">
              <div
                class="roster-popover-wrap flex-1"
                @mouseenter="openPopover(cls)"
                @mouseleave="closePopover"
              >
                <button class="w-full py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">学生名单</button>
                <div class="roster-popover" :class="{ show: activePopover === cls.id }">
                  <div class="roster-popover-title">{{ cls.name }} · 学生名单（{{ cls.student_count }}人）</div>
                  <div v-if="popoverLoading === cls.id" class="roster-empty">加载中...</div>
                  <div
                    v-else-if="getPopoverStudents(cls).length > 0"
                    class="roster-list"
                    :class="getPopoverStudents(cls).length > 4 ? 'roster-list--scroll' : 'roster-list--compact'"
                  >
                    <div v-for="student in getPopoverStudents(cls)" :key="student.id" class="roster-popover-item">
                      <span>
                        <span class="avatar" :style="{ background: getAvatarColor(student.id) }">{{ teacherStudentNameInitial(student) }}</span>
                        {{ formatTeacherStudentRealName(student) }}
                      </span>
                      <span class="text-gray-500">{{ student.account }}</span>
                    </div>
                  </div>
                  <div class="roster-empty" v-else>暂无学生</div>
                  <div
                    v-if="getPopoverStudents(cls).length > 4"
                    class="roster-popover-more"
                  >
                    共 {{ cls.student_count }} 人，可滚动查看
                  </div>
                </div>
              </div>
              <button class="flex-1 py-1.5 text-sm bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-100" @click="router.push(`/teacher/classes/${cls.id}`)">
                管理
              </button>
              <button
                class="py-1.5 px-3 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-60"
                :disabled="editLoadingId === cls.id"
                @click="openEdit(cls)"
              >
                {{ editLoadingId === cls.id ? '…' : '编辑' }}
              </button>
              <button class="px-2 py-1.5 text-sm text-red-500 border border-red-200 rounded-lg hover:bg-red-50" @click="handleDelete(cls)" title="删除班级">
                🗑
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <EditClassModal
      v-if="showEditModal && editingClass"
      :class-data="editingClass"
      @close="closeEditModal"
      @success="onEditSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useDebouncedWatch } from '@/composables/useDebouncedWatch'
import { useRouter } from 'vue-router'
import { classApi } from '@/api/classes'
import ClassFilterPopover from '@/components/class/ClassFilterPopover.vue'
import EditClassModal from '@/components/EditClassModal.vue'
import type { ClassDetail, ClassListItem, StudentBrief } from '@/types/class'
import { toast } from '@/utils/toast'
import { formatTeacherStudentRealName, teacherStudentNameInitial } from '@/utils/teacher-student-name'

const router = useRouter()
const classes = ref<ClassListItem[]>([])
const loading = ref(true)
const keyword = ref('')
const filterWeekday = ref('')
const filterCourseType = ref('')

const filterOpen = ref(false)
const filterAnchorRef = ref<HTMLElement | null>(null)

const activeFilterCount = computed(() => {
  let count = 0
  if (filterWeekday.value) count += 1
  if (filterCourseType.value) count += 1
  return count
})

const hasListQuery = computed(
  () =>
    Boolean(keyword.value.trim()) ||
    Boolean(filterWeekday.value) ||
    Boolean(filterCourseType.value),
)
const activePopover = ref<number | null>(null)
const popoverLoading = ref<number | null>(null)
const popoverStudents = ref<Record<number, StudentBrief[]>>({})
const showEditModal = ref(false)
const editingClass = ref<ClassDetail | null>(null)
const editLoadingId = ref<number | null>(null)

const getPopoverStudents = (cls: ClassListItem): StudentBrief[] =>
  popoverStudents.value[cls.id] ?? cls.students_preview

const openPopover = async (cls: ClassListItem) => {
  activePopover.value = cls.id
  if (popoverStudents.value[cls.id] || cls.student_count === 0) return
  if (cls.student_count <= 4) {
    popoverStudents.value[cls.id] = cls.students_preview
    return
  }
  popoverLoading.value = cls.id
  try {
    const students = await classApi.listStudents(cls.id)
    popoverStudents.value[cls.id] = students.map((s) => ({
      id: s.id,
      account: s.account,
      real_name: s.real_name,
      nickname: s.nickname,
      display_name: s.display_name,
    }))
  } catch {
    popoverStudents.value[cls.id] = cls.students_preview
  } finally {
    popoverLoading.value = null
  }
}

const closePopover = () => {
  activePopover.value = null
  popoverLoading.value = null
}

const GRADIENTS = [
  'bg-gradient-to-r from-indigo-500 to-purple-500',
  'bg-gradient-to-r from-green-500 to-teal-500',
  'bg-gradient-to-r from-amber-500 to-orange-500',
  'bg-gradient-to-r from-pink-500 to-rose-500',
  'bg-gradient-to-r from-cyan-500 to-blue-500',
]

const AVATAR_COLORS = ['#3b82f6', '#ec4899', '#14b8a6', '#eab308', '#6366f1', '#f97316', '#8b5cf6', '#ef4444']

const getGradient = (id: number) => GRADIENTS[(id - 1) % GRADIENTS.length]
const getAvatarColor = (id: number) => AVATAR_COLORS[(id - 1) % AVATAR_COLORS.length]

const loadClasses = async () => {
  loading.value = true
  try {
    classes.value = await classApi.list({
      keyword: keyword.value.trim() || undefined,
      weekday: filterWeekday.value || undefined,
      course_type: filterCourseType.value || undefined,
    })
  } catch (err) {
    alert(err instanceof Error ? err.message : '加载班级失败')
  } finally {
    loading.value = false
  }
}

const openEdit = async (cls: ClassListItem) => {
  editLoadingId.value = cls.id
  try {
    editingClass.value = await classApi.get(cls.id)
    showEditModal.value = true
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '加载班级信息失败')
  } finally {
    editLoadingId.value = null
  }
}

const closeEditModal = () => {
  showEditModal.value = false
  editingClass.value = null
}

const onEditSuccess = async () => {
  toast.success('班级信息已更新')
  await loadClasses()
}

const handleDelete = async (cls: ClassListItem) => {
  if (!confirm(`确定删除班级「${cls.name}」吗？此操作不可恢复。`)) return
  try {
    await classApi.remove(cls.id)
    await loadClasses()
  } catch (err) {
    alert(err instanceof Error ? err.message : '删除失败')
  }
}

const toggleFilter = () => {
  filterOpen.value = !filterOpen.value
}

const onFilterApply = (payload: { weekday: string; courseType: string }) => {
  filterWeekday.value = payload.weekday
  filterCourseType.value = payload.courseType
  filterOpen.value = false
  void loadClasses()
}

const onFilterReset = () => {
  filterWeekday.value = ''
  filterCourseType.value = ''
  filterOpen.value = false
  void loadClasses()
}

const clearListQuery = () => {
  keyword.value = ''
  filterWeekday.value = ''
  filterCourseType.value = ''
  void loadClasses()
}

function onDocumentClick(event: MouseEvent) {
  if (!filterOpen.value || !filterAnchorRef.value) return
  if (!filterAnchorRef.value.contains(event.target as Node)) {
    filterOpen.value = false
  }
}

watch(filterOpen, (open) => {
  document.removeEventListener('click', onDocumentClick)
  if (open) {
    void nextTick(() => {
      document.addEventListener('click', onDocumentClick)
    })
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
})

useDebouncedWatch(keyword, () => {
  void loadClasses()
})

onMounted(loadClasses)
</script>

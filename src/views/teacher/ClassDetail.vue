<template>
  <div>
    <div class="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-3">
      <button class="text-sm text-gray-500 hover:text-gray-900" @click="router.push('/teacher/classes')">← 返回班级管理</button>
      <h1 class="text-lg font-semibold text-gray-900">
        {{ classInfo?.name || '班级详情' }} · 班级学生
      </h1>
      <div class="ml-auto flex items-center gap-2">
        <input
          v-model="keyword"
          type="text"
          placeholder="搜索学生"
          class="input-light-bg px-3 py-1.5 text-sm border border-gray-300 rounded-lg w-40 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <button v-if="classInfo" class="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50" @click="showEditModal = true">
          编辑班级
        </button>
        <button class="px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700" @click="showAddModal = true">
          + 添加学生
        </button>
      </div>
    </div>

    <div class="p-6 space-y-4">
      <div v-if="loading" class="text-center py-16 text-gray-500">加载中...</div>

      <div v-else-if="students.length === 0" class="bg-white rounded-xl border border-gray-100 p-12 text-center">
        <div class="text-4xl mb-3">📚</div>
        <p class="text-gray-500 mb-4">暂无学生，请先添加学生</p>
        <button class="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700" @click="showAddModal = true">
          + 添加学生
        </button>
      </div>

      <div v-else class="bg-white rounded-xl border border-gray-100 p-5">
        <table class="w-full text-sm">
          <thead class="text-gray-500 border-b border-gray-100">
            <tr class="text-left">
              <th class="pb-2 font-medium">真实姓名</th>
              <th class="pb-2 font-medium">登录账号</th>
              <th class="pb-2 font-medium">昵称</th>
              <th class="pb-2 font-medium">完成题数</th>
              <th class="pb-2 font-medium">正确率</th>
              <th class="pb-2 font-medium">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-for="student in students" :key="student.id">
              <td class="py-2.5">
                <div class="flex items-center gap-2">
                  <div class="w-7 h-7 rounded-full flex items-center justify-center text-xs" :class="getAvatarClass(student.id)">
                    {{ teacherStudentNameInitial(student) }}
                  </div>
                  <span>{{ formatTeacherStudentRealName(student) }}</span>
                </div>
              </td>
              <td class="py-2.5 text-gray-500 font-mono text-xs">{{ student.account }}</td>
              <td class="py-2.5 text-gray-600">{{ student.nickname || '—' }}</td>
              <td class="py-2.5">{{ student.completed_problems || '-' }}</td>
              <td class="py-2.5" :class="student.accuracy ? getAccuracyClass(student.accuracy) : 'text-gray-400'">
                {{ student.accuracy ? `${student.accuracy}%` : '-' }}
              </td>
              <td class="py-2.5">
                <div class="flex items-center gap-3 flex-wrap">
                  <button class="text-indigo-600 hover:underline" @click="openViewStudent(student)">查看</button>
                  <button class="text-indigo-600 hover:underline" @click="openBindParent(student)">绑定家长</button>
                  <button class="text-indigo-600 hover:underline" @click="handleResetPassword(student)">重置密码</button>
                  <button class="text-red-500 hover:underline" @click="handleRemove(student)">移除</button>
                </div>
                <div v-if="parentBindings[student.id]?.length" class="text-xs text-gray-500 mt-1">
                  已绑定：{{ parentBindings[student.id].map((item) => item.parent_name).join('、') }}
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <AddStudentModal
      v-if="showAddModal && classId"
      :class-id="classId"
      :enrolled-student-ids="students.map((s) => s.id)"
      @close="showAddModal = false"
      @success="onStudentAdded"
    />
    <EditClassModal
      v-if="showEditModal && classInfo"
      :class-data="classInfo"
      @close="showEditModal = false"
      @success="loadClass"
    />
    <BindParentModal
      v-if="bindTarget"
      :class-id="classId"
      :student-id="bindTarget.id"
      :student-name="formatTeacherStudentRealName(bindTarget)"
      @close="bindTarget = null"
      @success="onParentBound"
    />
    <ViewStudentInfoModal
      v-if="viewTarget"
      :account="viewTarget.account"
      :real-name="viewTarget.real_name"
      :nickname="viewTarget.nickname"
      @close="viewTarget = null"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useDebouncedWatch } from '@/composables/useDebouncedWatch'
import { useRoute, useRouter } from 'vue-router'
import { classApi } from '@/api/classes'
import AddStudentModal from '@/components/AddStudentModal.vue'
import BindParentModal from '@/components/BindParentModal.vue'
import EditClassModal from '@/components/EditClassModal.vue'
import ViewStudentInfoModal from '@/components/ViewStudentInfoModal.vue'
import { toast } from '@/utils/toast'
import { formatTeacherStudentRealName, teacherStudentNameInitial } from '@/utils/teacher-student-name'
import { trackEvent } from '@/utils/tracker'
import type { ClassDetail, ClassStudentItem, ParentBindingItem } from '@/types/class'

const route = useRoute()
const router = useRouter()

const classId = computed(() => Number(route.params.id))
const classInfo = ref<ClassDetail | null>(null)
const students = ref<ClassStudentItem[]>([])
const loading = ref(true)
const keyword = ref('')
const showAddModal = ref(false)
const showEditModal = ref(false)
const bindTarget = ref<ClassStudentItem | null>(null)
const viewTarget = ref<ClassStudentItem | null>(null)
const parentBindings = ref<Record<number, ParentBindingItem[]>>({})
const AVATAR_CLASSES = [
  'bg-blue-100 text-blue-700',
  'bg-pink-100 text-pink-700',
  'bg-green-100 text-green-700',
  'bg-amber-100 text-amber-700',
  'bg-purple-100 text-purple-700',
]

const getAvatarClass = (id: number) => AVATAR_CLASSES[(id - 1) % AVATAR_CLASSES.length]

const getAccuracyClass = (accuracy: number) => {
  if (accuracy >= 80) return 'text-green-600 font-medium'
  if (accuracy >= 60) return 'text-amber-600 font-medium'
  return 'text-red-500 font-medium'
}

const loadClass = async () => {
  if (!classId.value || Number.isNaN(classId.value)) {
    router.push('/teacher/classes')
    return
  }
  try {
    classInfo.value = await classApi.get(classId.value)
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '加载班级失败')
    router.push('/teacher/classes')
  }
}

const loadStudents = async () => {
  if (!classId.value || Number.isNaN(classId.value)) return
  loading.value = true
  try {
    await loadClass()
    students.value = await classApi.listStudents(classId.value, keyword.value.trim() || undefined)
    await loadParentBindings()
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '加载学生失败')
  } finally {
    loading.value = false
  }
}

const loadParentBindings = async () => {
  const bindings: Record<number, ParentBindingItem[]> = {}
  await Promise.all(
    students.value.map(async (student) => {
      bindings[student.id] = await classApi.listParentBindings(classId.value, student.id)
    }),
  )
  parentBindings.value = bindings
}

const openBindParent = (student: ClassStudentItem) => {
  bindTarget.value = student
}

const openViewStudent = (student: ClassStudentItem) => {
  viewTarget.value = student
}

const onParentBound = async () => {
  trackEvent({ event_name: 'parent_bind', page: '/teacher/classes', module: 'teacher', detail: `class=${classId.value}` })
  bindTarget.value = null
  await loadParentBindings()
}

const onStudentAdded = (message: string) => {
  trackEvent({ event_name: 'student_add', page: '/teacher/classes', module: 'teacher', detail: `class=${classId.value}` })
  toast.success(message)
  loadStudents()
}

const handleResetPassword = async (student: ClassStudentItem) => {
  if (!confirm(`确定将 ${formatTeacherStudentRealName(student)} 的密码重置为 123456 吗？`)) return
  try {
    await classApi.resetPassword(classId.value, student.id)
    trackEvent({ event_name: 'student_reset_password', page: '/teacher/classes', module: 'teacher', detail: `student=${student.id}` })
    toast.success(`已重置 ${formatTeacherStudentRealName(student)} 的密码为 123456`)
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '重置失败')
  }
}

const handleRemove = async (student: ClassStudentItem) => {
  if (!confirm(`确定将 ${formatTeacherStudentRealName(student)} 从班级中移除吗？`)) return
  try {
    await classApi.removeStudent(classId.value, student.id)
    trackEvent({ event_name: 'student_remove', page: '/teacher/classes', module: 'teacher', detail: `student=${student.id}` })
    await loadStudents()
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '移除失败')
  }
}

useDebouncedWatch(keyword, () => {
  void loadStudents()
})

onMounted(loadStudents)
</script>

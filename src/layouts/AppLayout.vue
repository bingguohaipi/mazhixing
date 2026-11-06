<template>
  <div
    class="flex h-screen overflow-hidden dark-mode"
    :class="{ 'app-role-teacher': auth.role === 'teacher' }"
  >
    <aside class="w-64 bg-white border-r border-gray-200 flex flex-col shrink-0">
      <div class="p-4 border-b border-gray-200">
        <div v-if="auth.role === 'student'" class="flex items-start gap-2 -m-1 p-1">
          <RouterLink to="/student/profile" class="shrink-0 rounded-xl hover:opacity-90 transition">
            <div
              v-if="studentAvatarUrl"
              class="w-12 h-12 rounded-xl overflow-hidden border border-gray-200"
            >
              <img :src="studentAvatarUrl" alt="" class="w-full h-full object-cover" />
            </div>
            <div
              v-else
              class="w-12 h-12 rounded-xl bg-indigo-600 flex items-center justify-center text-white font-bold text-xl"
            >
              {{ sidebarInitial }}
            </div>
          </RouterLink>
          <div class="min-w-0 flex-1 pt-0.5">
            <RouterLink
              to="/student/profile"
              class="block rounded-md hover:bg-gray-50 -mx-1 px-1 transition"
            >
              <div class="text-base font-bold text-gray-900 truncate leading-tight">{{ auth.displayName }}</div>
            </RouterLink>
            <div v-if="petStore.points" class="mt-2 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs">
              <RouterLink
                to="/student/points"
                class="student-sidebar-stat text-indigo-600 hover:text-indigo-500 font-medium whitespace-nowrap"
              >
                🪙 {{ petStore.points.balance }} 积分
              </RouterLink>
              <span v-if="petStore.activePet" class="text-gray-300 select-none">·</span>
              <RouterLink
                v-if="petStore.activePet"
                to="/student/pet-shop"
                class="student-sidebar-stat text-gray-500 hover:text-indigo-500 whitespace-nowrap truncate max-w-[8rem]"
              >
                🐾 {{ petStore.activePet.name }} Lv.{{ petStore.activePet.level }}
              </RouterLink>
              <RouterLink
                v-else
                to="/student/pet-shop"
                class="student-sidebar-stat text-gray-400 hover:text-indigo-500 whitespace-nowrap"
              >
                去领养宠物
              </RouterLink>
            </div>
          </div>
        </div>
        <div v-else class="flex items-center gap-2">
          <div class="w-12 h-12 rounded-xl bg-indigo-600 flex items-center justify-center text-white font-bold text-xl">码</div>
          <div>
            <div class="font-bold text-gray-900">码智星</div>
            <div class="text-xs text-gray-500">{{ auth.displayName }}</div>
          </div>
        </div>
      </div>

      <nav class="flex-1 overflow-y-auto scrollbar-thin py-2">
        <template v-if="auth.role === 'teacher'">
          <div class="px-3 py-1 text-xs font-semibold text-gray-400 uppercase">教师端</div>
          <RouterLink
            v-for="item in teacherNav"
            :key="item.to"
            :to="item.to"
            class="nav-item block px-4 py-2 text-sm text-gray-700"
            active-class="active"
          >
            {{ item.label }}
          </RouterLink>
        </template>

        <template v-else-if="auth.role === 'student'">
          <div class="px-3 py-1 text-xs font-semibold text-gray-400 uppercase">学生端</div>
          <RouterLink
            v-for="item in studentNav"
            :key="item.to"
            :to="item.to"
            class="nav-item block px-4 py-2 text-sm text-gray-700"
            active-class="active"
          >
            {{ item.label }}
          </RouterLink>
        </template>

        <template v-else-if="auth.role === 'parent'">
          <div class="px-3 py-1 text-xs font-semibold text-gray-400 uppercase">家长端</div>
          <RouterLink
            v-for="item in parentNav"
            :key="item.to"
            :to="item.to"
            class="nav-item block px-4 py-2 text-sm text-gray-700"
            active-class="active"
          >
            {{ item.label }}
          </RouterLink>
        </template>

        <template v-else-if="auth.role === 'admin'">
          <div class="px-3 py-1 text-xs font-semibold text-gray-400 uppercase">管理端</div>
          <RouterLink
            v-for="item in adminNav"
            :key="item.to"
            :to="item.to"
            class="nav-item block px-4 py-2 text-sm text-gray-700"
            active-class="active"
          >
            {{ item.label }}
          </RouterLink>
        </template>

        <RouterLink
          v-if="auth.role === 'parent'"
          to="/suggestions"
          class="nav-item block px-4 py-2 text-sm text-gray-700"
          active-class="active"
        >
          建议反馈
        </RouterLink>
      </nav>

      <div class="p-3 border-t border-gray-200 space-y-1">
        <button class="sidebar-user-btn" @click="showChangePwdModal = true">🔑 修改密码</button>
        <button class="sidebar-user-btn" @click="handleLogout">🚪 退出登录</button>
      </div>
    </aside>

    <main class="app-main-panel flex-1 overflow-y-auto scrollbar-thin relative">
      <RouterView @open-publish-notice="showPublishNoticeModal = true" />
    </main>

    <DesktopPetOverlay v-if="auth.role === 'student'" />

    <ChangePwdModal v-if="showChangePwdModal" @close="showChangePwdModal = false" @success="handlePwdChanged" />
    <PublishNoticeModal
      v-if="showPublishNoticeModal"
      @close="showPublishNoticeModal = false"
      @published="handleNoticePublished"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePetStore } from '@/stores/pet'
import { toast } from '@/utils/toast'
import ChangePwdModal from '@/components/ChangePwdModal.vue'
import PublishNoticeModal from '@/components/PublishNoticeModal.vue'
import DesktopPetOverlay from '@/components/DesktopPetOverlay.vue'
import { flushSuggestionResolvedNotifications } from '@/composables/useSuggestionResolvedToasts'

const router = useRouter()
const auth = useAuthStore()
const petStore = usePetStore()

function syncAppRoleDataset(role: string | null | undefined) {
  if (role) {
    document.documentElement.dataset.appRole = role
  } else {
    delete document.documentElement.dataset.appRole
  }
}

watch(
  () => auth.role,
  (role) => {
    syncAppRoleDataset(role)
    if (role === 'student') void petStore.bootstrap()
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  delete document.documentElement.dataset.appRole
})

onMounted(() => {
  if (auth.role === 'student') void petStore.bootstrap()
})

watch(
  () => auth.isAuthenticated,
  (loggedIn) => {
    if (loggedIn) void flushSuggestionResolvedNotifications()
  },
  { immediate: true },
)

const showChangePwdModal = ref(false)
const showPublishNoticeModal = ref(false)

const sidebarInitial = computed(() => {
  const name = auth.displayName || '?'
  return name.trim().charAt(0).toUpperCase()
})

const studentAvatarUrl = computed(() => {
  const url = auth.user?.avatar_url
  if (!url) return null
  if (url.startsWith('http')) return url
  return url
})

const handleNoticePublished = () => {
  toast.success('通知发布成功')
}

const teacherNav = [
  { to: '/teacher/dashboard', label: '工作台' },
  { to: '/teacher/roster', label: '学生名单' },
  { to: '/teacher/classes', label: '班级管理' },
  { to: '/teacher/homework', label: '作业管理' },
  { to: '/teacher/analytics', label: '学情统计' },
  { to: '/teacher/my-questions', label: '自有题库' },
  { to: '/teacher/questions', label: '公共题库' },
  { to: '/suggestions', label: '建议反馈' },
  { to: '/teacher/profile', label: '个人中心' },
]

const studentNav = [
  { to: '/student/dashboard', label: '我的工作台' },
  { to: '/student/analytics', label: '个人学情' },
  { to: '/student/questions', label: '题库' },
  { to: '/student/wrong', label: '错题本' },
  { to: '/student/leaderboard', label: '排行榜' },
  { to: '/student/arena', label: '擂台' },
  { to: '/student/pet-shop', label: '宠物商城' },
  { to: '/suggestions', label: '建议反馈' },
  { to: '/student/profile', label: '个人中心' },
]

const adminNav = [
  { to: '/admin/dashboard', label: '工作台' },
  { to: '/admin/public-problems', label: '题库管理' },
  { to: '/admin/knowledge-points', label: '知识点管理' },
  { to: '/admin/users', label: '用户管理' },
  { to: '/admin/suggestions', label: '建议中心' },
  { to: '/admin/pet-shop', label: '宠物商城' },
]

const parentNav = [
  { to: '/parent/overview', label: '学情总览' },
  { to: '/parent/trends', label: '学习趋势' },
  { to: '/parent/weak-points', label: '薄弱知识点' },
  { to: '/parent/wrong-top', label: '高频错题' },
  { to: '/parent/profile', label: '个人中心' },
]

const handleLogout = () => {
  auth.logout()
  router.push('/login')
}

const handlePwdChanged = () => {
  showChangePwdModal.value = false
  auth.logout()
  router.push('/login')
}
</script>

<style>
#app { width: 100%; height: 100vh; }
</style>

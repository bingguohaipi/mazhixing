import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { authApi } from '@/api/auth'
import { clearTokens, setTokens } from '@/api/client'
import { resetParentContext } from '@/composables/useParentContext'
import type { LoginPayload, RegisterPayload, UserInfo, UserRole } from '@/types/auth'

const ROLE_HOME: Record<UserRole, string> = {
  admin: '/admin/dashboard',
  teacher: '/teacher/dashboard',
  student: '/student/dashboard',
  parent: '/parent/overview',
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserInfo | null>(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => user.value !== null)
  const role = computed(() => user.value?.role ?? null)
  const displayName = computed(() => user.value?.display_name || user.value?.account || '')

  const homeRoute = computed(() => (role.value ? ROLE_HOME[role.value] : '/login'))

  async function login(payload: LoginPayload): Promise<void> {
    loading.value = true
    resetParentContext()
    try {
      const result = await authApi.login(payload)
      setTokens(result.tokens.access_token, result.tokens.refresh_token)
      user.value = result.user
    } finally {
      loading.value = false
    }
  }

  async function register(payload: RegisterPayload): Promise<void> {
    loading.value = true
    try {
      await authApi.register(payload)
    } finally {
      loading.value = false
    }
  }

  async function fetchMe(): Promise<boolean> {
    const token = localStorage.getItem('mzx_access_token')
    if (!token) {
      user.value = null
      return false
    }
    loading.value = true
    try {
      user.value = await authApi.me()
      return true
    } catch {
      clearTokens()
      user.value = null
      return false
    } finally {
      loading.value = false
    }
  }

  function logout(): void {
    clearTokens()
    user.value = null
    resetParentContext()
  }

  function hasRole(roles: UserRole[]): boolean {
    return !!role.value && roles.includes(role.value)
  }

  function patchUser(partial: Partial<UserInfo>): void {
    if (user.value) {
      user.value = { ...user.value, ...partial }
    }
  }

  return {
    user,
    loading,
    isAuthenticated,
    role,
    displayName,
    homeRoute,
    login,
    register,
    fetchMe,
    logout,
    hasRole,
    patchUser,
  }
})

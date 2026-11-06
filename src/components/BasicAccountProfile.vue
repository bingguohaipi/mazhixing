<template>
  <div
    class="min-h-full"
    :class="
      centered
        ? centeredLower
          ? 'flex flex-col items-center justify-start px-6 pb-6 pt-8 md:pt-10'
          : 'flex flex-col items-center justify-center p-6'
        : 'flex justify-center p-6'
    "
  >
    <div
      class="w-full max-w-xl space-y-6"
      :class="
        centered && !centeredLower
          ? 'mx-auto -translate-y-12 md:-translate-y-[4.5rem]'
          : 'mx-auto'
      "
    >
      <div :class="centered ? 'text-center' : ''">
        <h1 class="text-lg font-semibold text-gray-900">个人中心</h1>
        <p class="text-sm text-gray-500 mt-1">码智星 · {{ roleLabel }} · 账号 {{ profile?.account }}</p>
      </div>

      <div v-if="loading" class="text-center py-16 text-gray-500">加载中...</div>
      <template v-else-if="profile">
        <section class="bg-white rounded-xl border border-gray-100 p-6 space-y-4">
          <div class="grid gap-3 text-sm">
            <div class="flex justify-between gap-4 border-b border-gray-50 pb-2">
              <span class="text-gray-500">真实姓名</span>
              <span class="font-medium text-gray-900 text-right">{{ profile.real_name || '—' }}</span>
            </div>
            <div class="flex justify-between gap-4 border-b border-gray-50 pb-2">
              <span class="text-gray-500">登录账号</span>
              <span class="font-mono text-gray-900 text-right">{{ profile.account }}</span>
            </div>
          </div>

          <div>
            <label class="text-sm font-medium text-gray-700">昵称</label>
            <div class="flex flex-col sm:flex-row gap-2 mt-1">
              <input
                v-model="nicknameInput"
                type="text"
                maxlength="16"
                placeholder="2–16 字，不含不文明用语"
                class="flex-1 min-w-0 px-3 py-2 border border-gray-300 rounded-lg text-sm"
              />
              <button
                type="button"
                class="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 shrink-0"
                :disabled="nicknameSaving"
                @click="saveNickname"
              >
                {{ nicknameSaving ? '保存中...' : '保存昵称' }}
              </button>
            </div>
            <p class="text-xs text-gray-400 mt-1">昵称全平台不可重复（不区分大小写）；真实姓名由管理员或老师维护。</p>
          </div>
        </section>

        <slot name="extra" :profile="profile" />

        <section
          class="bg-white rounded-xl border border-gray-100 p-6"
          :class="centered ? 'text-center' : ''"
        >
          <h2 class="text-sm font-semibold text-gray-900 mb-2">账号安全</h2>
          <p class="text-sm text-gray-500 mb-3">修改密码后需重新登录</p>
          <button
            type="button"
            class="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
            @click="showChangePwd = true"
          >
            修改密码
          </button>
        </section>
      </template>

      <ChangePwdModal
        v-if="showChangePwd"
        center-in-main
        @close="showChangePwd = false"
        @success="onPwdChanged"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import ChangePwdModal from '@/components/ChangePwdModal.vue'
import { useAuthStore } from '@/stores/auth'
import { toast } from '@/utils/toast'

export interface BasicProfileShape {
  account: string
  real_name: string | null
  nickname: string | null
}

const props = withDefaults(
  defineProps<{
    roleLabel: string
    load: () => Promise<BasicProfileShape>
    saveNickname: (nickname: string) => Promise<BasicProfileShape>
    /** 标题居中，且整块内容在页面中水平/垂直居中（教师个人中心） */
    centered?: boolean
    /** 与 centered 合用：内容从上方留白下移，避免贴顶（家长个人中心） */
    centeredLower?: boolean
  }>(),
  { centered: false, centeredLower: false },
)

const router = useRouter()
const auth = useAuthStore()
const profile = ref<BasicProfileShape | null>(null)
const loading = ref(true)
const nicknameInput = ref('')
const nicknameSaving = ref(false)
const showChangePwd = ref(false)

const syncAuth = (data: BasicProfileShape) => {
  auth.patchUser({
    display_name: data.nickname || data.real_name || data.account,
    nickname: data.nickname,
    real_name: data.real_name,
  })
}

const loadProfile = async () => {
  loading.value = true
  try {
    profile.value = await props.load()
    nicknameInput.value = profile.value.nickname || ''
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '加载失败')
  } finally {
    loading.value = false
  }
}

const saveNickname = async () => {
  const value = nicknameInput.value.trim()
  if (!value) {
    toast.error('请输入昵称')
    return
  }
  nicknameSaving.value = true
  try {
    const data = await props.saveNickname(value)
    profile.value = data
    syncAuth(data)
    toast.success('昵称已更新')
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '保存失败')
  } finally {
    nicknameSaving.value = false
  }
}

const onPwdChanged = () => {
  showChangePwd.value = false
  auth.logout()
  void router.push('/login')
}

onMounted(() => {
  void loadProfile()
})
</script>

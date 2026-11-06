<template>
  <div class="min-h-full flex justify-center p-6">
    <div class="w-full max-w-xl space-y-6 text-center">
    <div>
      <h1 class="text-lg font-semibold text-gray-900">个人中心</h1>
      <p class="text-sm text-gray-500 mt-1">码智星 · 账号 {{ profile?.account }}</p>
      <p class="text-xs text-gray-400 mt-0.5">真实姓名由老师维护；昵称与密码可自行修改</p>
    </div>

    <div v-if="loading" class="text-center py-16 text-gray-500">加载中...</div>
    <template v-else-if="profile">
      <section class="bg-white rounded-xl border border-gray-100 p-6 flex flex-col items-center gap-5">
        <div class="relative shrink-0">
          <div
            v-if="avatarPreview"
            class="w-20 h-20 rounded-full overflow-hidden border-2 border-indigo-100 bg-gray-50"
          >
            <img :src="avatarPreview" alt="头像" class="w-full h-full object-cover" />
          </div>
          <div
            v-else
            class="w-20 h-20 rounded-full bg-indigo-600 text-white flex items-center justify-center text-2xl font-semibold"
          >
            {{ avatarInitial }}
          </div>
          <label class="mt-2 block text-center text-xs text-indigo-600 cursor-pointer hover:text-indigo-800">
            <input type="file" accept="image/jpeg,image/png,image/webp" class="hidden" @change="onAvatarPick" />
            {{ avatarUploading ? '上传中...' : '更换头像' }}
          </label>
        </div>
        <div class="w-full max-w-sm space-y-4 text-left">
          <div class="grid gap-2 text-sm border-b border-gray-100 pb-4">
            <div class="flex justify-between gap-2">
              <span class="text-gray-500">真实姓名</span>
              <span class="font-medium text-gray-900">{{ profile.real_name || profile.display_name || '—' }}</span>
            </div>
            <div class="flex justify-between gap-2">
              <span class="text-gray-500">登录账号</span>
              <span class="font-mono text-gray-900">{{ profile.account }}</span>
            </div>
            <div class="flex justify-between gap-2">
              <span class="text-gray-500">所在班级</span>
              <span class="text-gray-900 text-right">
                {{ profile.class_names.length ? profile.class_names.join('、') : '暂未加入班级' }}
              </span>
            </div>
          </div>
          <div>
            <label class="text-sm font-medium text-gray-700">昵称</label>
            <div class="flex flex-col sm:flex-row gap-2 mt-1 justify-center">
              <input
                v-model="nicknameInput"
                type="text"
                maxlength="16"
                placeholder="2–16 字，不含不文明用语"
                class="flex-1 min-w-0 px-3 py-2 border border-gray-300 rounded-lg text-sm text-center sm:text-left"
              />
              <button
                type="button"
                class="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 shrink-0"
                :disabled="nicknameSaving"
                @click="saveNickname"
              >
                {{ nicknameSaving ? '保存中...' : '保存' }}
              </button>
            </div>
            <p class="text-xs text-gray-400 mt-1">擂台与排行榜展示昵称，不影响真实姓名。</p>
          </div>
          <div v-if="profile.student_no" class="text-sm text-gray-600">
            学号：<span class="font-mono">{{ profile.student_no }}</span>
          </div>
        </div>
      </section>

      <section class="bg-white rounded-xl border border-gray-100 p-6">
        <h2 class="text-sm font-semibold text-gray-900 mb-3">我的老师</h2>
        <ul v-if="profile.teachers.length" class="space-y-3">
          <li
            v-for="t in profile.teachers"
            :key="t.id"
            class="flex flex-wrap items-baseline justify-center gap-x-2 text-sm border-b border-gray-50 pb-2 last:border-0"
          >
            <span class="font-medium text-gray-900">{{ t.display_name }}</span>
            <span v-if="t.class_names.length" class="text-gray-500">
              · {{ t.class_names.join('、') }}
            </span>
          </li>
        </ul>
        <p v-else class="text-sm text-gray-500">暂未关联老师，请等待老师将你加入班级</p>
      </section>

      <section class="bg-white rounded-xl border border-gray-100 p-6">
        <h2 class="text-sm font-semibold text-gray-900 mb-3">我的家长</h2>
        <ul v-if="profile.parents.length" class="space-y-2">
          <li v-for="p in profile.parents" :key="p.id" class="text-sm font-medium text-gray-900">
            {{ p.display_name }}
          </li>
        </ul>
        <p v-else class="text-sm text-gray-500">暂未绑定家长账号</p>
      </section>

      <section class="bg-white rounded-xl border border-gray-100 p-6 text-left">
        <h2 class="text-sm font-semibold text-gray-900 mb-3">桌面小伙伴</h2>
        <label class="flex items-center justify-between gap-4 py-2 text-sm">
          <span class="text-gray-700">显示桌面宠物</span>
          <input v-model="petSettings.desktop_pet_enabled" type="checkbox" class="w-4 h-4" @change="savePetSettings" />
        </label>
        <label class="flex items-center justify-between gap-4 py-2 text-sm">
          <span class="text-gray-700">做题时宠物休息</span>
          <input v-model="petSettings.silent_while_coding" type="checkbox" class="w-4 h-4" @change="savePetSettings" />
        </label>
        <p class="text-xs text-gray-400 mt-2">关闭显示后不会在页面上看到小伙伴，仍可在宠物商城喂养。</p>
      </section>

      <section class="bg-white rounded-xl border border-gray-100 p-6">
        <h2 class="text-sm font-semibold text-gray-900 mb-2">账号安全</h2>
        <p class="text-sm text-gray-500 mb-3">修改密码后需重新登录</p>
        <div class="flex justify-center">
          <button
            type="button"
            class="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
            @click="showChangePwd = true"
          >
            修改密码
          </button>
        </div>
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
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { petApi } from '@/api/pet'
import { studentProfileApi } from '@/api/student-profile'
import { usePetStore } from '@/stores/pet'
import ChangePwdModal from '@/components/ChangePwdModal.vue'
import { useAuthStore } from '@/stores/auth'
import type { StudentProfile } from '@/types/student-profile'
import { toast } from '@/utils/toast'

const router = useRouter()
const auth = useAuthStore()
const petStore = usePetStore()
const petSettings = ref({ desktop_pet_enabled: true, silent_while_coding: true })
const profile = ref<StudentProfile | null>(null)
const loading = ref(true)
const nicknameInput = ref('')
const nicknameSaving = ref(false)
const avatarUploading = ref(false)
const showChangePwd = ref(false)

const avatarPreview = computed(() => profile.value?.avatar_url ?? null)

const avatarInitial = computed(() => {
  const name = nicknameInput.value || profile.value?.account || '?'
  return name.trim().charAt(0).toUpperCase()
})

const load = async () => {
  loading.value = true
  try {
    profile.value = await studentProfileApi.getProfile()
    nicknameInput.value = profile.value.nickname || ''
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '加载失败')
  } finally {
    loading.value = false
  }
}

const syncAuthUser = (data: StudentProfile) => {
  auth.patchUser({
    display_name: data.nickname || data.real_name || data.display_name || data.account,
    real_name: data.real_name ?? data.display_name,
    nickname: data.nickname,
    avatar_url: data.avatar_url,
  })
}

const saveNickname = async () => {
  const value = nicknameInput.value.trim()
  if (!value) {
    toast.error('请输入昵称')
    return
  }
  nicknameSaving.value = true
  try {
    const data = await studentProfileApi.updateNickname(value)
    profile.value = data
    syncAuthUser(data)
    toast.success('昵称已更新')
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '保存失败')
  } finally {
    nicknameSaving.value = false
  }
}

const onAvatarPick = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  if (file.size > 2 * 1024 * 1024) {
    toast.error('头像不能超过 2MB')
    return
  }
  avatarUploading.value = true
  try {
    const data = await studentProfileApi.uploadAvatar(file)
    profile.value = data
    syncAuthUser(data)
    toast.success('头像已更新')
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '上传失败')
  } finally {
    avatarUploading.value = false
  }
}

const onPwdChanged = () => {
  showChangePwd.value = false
  auth.logout()
  void router.push('/login')
}

const loadPetSettings = async () => {
  try {
    const s = await petApi.getSettings()
    petSettings.value = { ...s }
    petStore.settings = s
  } catch {
    /* optional */
  }
}

const savePetSettings = async () => {
  try {
    const s = await petApi.patchSettings({ ...petSettings.value })
    petSettings.value = { ...s }
    petStore.settings = s
    toast.success('已保存')
  } catch {
    toast.error('保存失败')
  }
}

onMounted(() => {
  void load()
  void loadPetSettings()
})
</script>

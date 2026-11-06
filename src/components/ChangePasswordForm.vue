<template>
  <div :class="theme === 'inline' ? 'w-full max-w-sm mx-auto space-y-4' : ''">
    <template v-if="theme === 'modal'">
      <h3 class="modal-title">修改密码</h3>
      <p class="modal-sub">修改成功后需重新登录</p>
    </template>

    <div :class="fieldClass">
      <label :class="labelClass">原密码</label>
      <PasswordInput
        v-model="form.oldPwd"
        :input-class="inputClass"
        placeholder="请输入当前密码"
        autocomplete="current-password"
      />
    </div>
    <div :class="fieldClass">
      <label :class="labelClass">新密码</label>
      <PasswordInput
        v-model="form.newPwd"
        :input-class="inputClass"
        placeholder="6-20位，包含字母和数字"
        autocomplete="new-password"
      />
    </div>
    <div :class="fieldClass">
      <label :class="labelClass">确认新密码</label>
      <PasswordInput
        v-model="form.newPwd2"
        :input-class="inputClass"
        placeholder="请再次输入新密码"
        autocomplete="new-password"
      />
    </div>
    <div
      v-if="formError"
      :class="theme === 'modal' ? 'modal-error show' : 'text-sm text-red-600 text-center'"
      :style="theme === 'modal' ? 'margin-bottom: 12px;' : undefined"
    >
      {{ formError }}
    </div>
    <div :class="theme === 'modal' ? 'modal-actions' : 'flex flex-wrap justify-center gap-3 pt-1'">
      <button
        v-if="showCancel"
        :class="theme === 'modal' ? 'modal-btn-cancel' : 'px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50'"
        type="button"
        @click="emit('cancel')"
      >
        取消
      </button>
      <button
        :class="
          theme === 'modal'
            ? 'modal-btn-confirm'
            : 'px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50'
        "
        type="button"
        :disabled="submitting"
        @click="submit"
      >
        {{ submitting ? '提交中...' : '确认修改' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { authApi } from '@/api/auth'
import PasswordInput from '@/components/PasswordInput.vue'

const props = withDefaults(
  defineProps<{
    theme?: 'modal' | 'inline'
    showCancel?: boolean
  }>(),
  { theme: 'inline', showCancel: false },
)

const emit = defineEmits<{ cancel: []; success: [] }>()

const form = reactive({
  oldPwd: '',
  newPwd: '',
  newPwd2: '',
})

const submitting = ref(false)
const formError = ref('')

const fieldClass = computed(() => (props.theme === 'modal' ? 'modal-field' : 'space-y-1 text-left'))
const labelClass = computed(() =>
  props.theme === 'modal' ? 'modal-label' : 'text-sm font-medium text-gray-700',
)
const inputClass = computed(() =>
  props.theme === 'modal'
    ? 'modal-input'
    : 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm',
)

const submit = async () => {
  formError.value = ''
  if (!form.oldPwd || !form.newPwd || !form.newPwd2) {
    formError.value = '请填写完整信息'
    return
  }
  if (form.newPwd.length < 6 || form.newPwd.length > 20) {
    formError.value = '密码长度为6-20位'
    return
  }
  if (!/[a-zA-Z]/.test(form.newPwd) || !/\d/.test(form.newPwd)) {
    formError.value = '密码需同时包含字母和数字'
    return
  }
  if (form.newPwd !== form.newPwd2) {
    formError.value = '两次新密码输入不一致'
    return
  }
  if (form.newPwd === form.oldPwd) {
    formError.value = '新密码不能与原密码相同'
    return
  }

  submitting.value = true
  try {
    await authApi.changePassword({
      old_password: form.oldPwd,
      new_password: form.newPwd,
    })
    emit('success')
  } catch (err) {
    formError.value = err instanceof Error ? err.message : '密码修改失败'
  } finally {
    submitting.value = false
  }
}
</script>

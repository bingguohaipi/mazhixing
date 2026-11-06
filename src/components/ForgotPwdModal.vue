<template>
  <div class="modal-mask">
    <div class="modal-box">
      <h3 class="modal-title">找回密码</h3>
      <p class="modal-sub">通过手机号验证码重置密码</p>
      <div class="modal-field">
        <label class="modal-label">手机号</label>
        <input type="tel" class="modal-input" :class="{ error: errors.phone }" v-model="form.phone" placeholder="请输入注册手机号" @blur="validateField('phone')" @input="clearError('phone')">
        <div class="modal-error" :class="{ show: errors.phone }">{{ errors.phoneMsg }}</div>
      </div>
      <div class="modal-field">
        <label class="modal-label">验证码</label>
        <div class="code-row">
          <input type="text" class="modal-input" :class="{ error: errors.code }" v-model="form.code" placeholder="请输入6位验证码" @blur="validateField('code')" @input="clearError('code')">
          <button class="code-btn" @click="sendCode" :disabled="countdown > 0 || sending">{{ countdown > 0 ? `${countdown}s后重发` : '获取验证码' }}</button>
        </div>
        <div class="modal-error" :class="{ show: errors.code }">{{ errors.codeMsg }}</div>
      </div>
      <div class="modal-field">
        <label class="modal-label">新密码</label>
        <PasswordInput
          v-model="form.pwd"
          input-class="modal-input"
          :has-error="errors.pwd"
          placeholder="6-20位，包含字母和数字"
          autocomplete="new-password"
          @blur="validateField('pwd')"
          @update:model-value="clearError('pwd')"
        />
        <div class="modal-error" :class="{ show: errors.pwd }">{{ errors.pwdMsg }}</div>
      </div>
      <div class="modal-field">
        <label class="modal-label">确认新密码</label>
        <PasswordInput
          v-model="form.pwd2"
          input-class="modal-input"
          :has-error="errors.pwd2"
          placeholder="请再次输入新密码"
          autocomplete="new-password"
          @blur="validateField('pwd2')"
          @update:model-value="clearError('pwd2')"
        />
        <div class="modal-error" :class="{ show: errors.pwd2 }">{{ errors.pwd2Msg }}</div>
      </div>
      <div v-if="formError" class="modal-error show" style="margin-bottom: 12px;">{{ formError }}</div>
      <div class="modal-actions">
        <button class="modal-btn-cancel" @click="$emit('close')">取消</button>
        <button class="modal-btn-confirm" :disabled="submitting" @click="submit">{{ submitting ? '提交中...' : '重置密码' }}</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { authApi } from '@/api/auth'
import PasswordInput from '@/components/PasswordInput.vue'
import type { UserRole } from '@/types/auth'

const props = defineProps<{
  role: Exclude<UserRole, 'student' | 'admin'>
}>()

const emit = defineEmits(['close'])

const form = reactive({
  phone: '',
  code: '',
  pwd: '',
  pwd2: ''
})

const errors = reactive({
  phone: false, phoneMsg: '',
  code: false, codeMsg: '',
  pwd: false, pwdMsg: '',
  pwd2: false, pwd2Msg: ''
})

const countdown = ref(0)
const sending = ref(false)
const submitting = ref(false)
const formError = ref('')

const showError = (field: string, msg: string) => {
  (errors as Record<string, boolean | string>)[field] = true
  ;(errors as Record<string, boolean | string>)[field + 'Msg'] = msg
}

const clearError = (field: string) => {
  (errors as Record<string, boolean | string>)[field] = false
  ;(errors as Record<string, boolean | string>)[field + 'Msg'] = ''
}

const validateField = (field: string) => {
  if (field === 'phone') {
    if (!form.phone) { clearError('phone'); return false }
    if (!/^1[3-9]\d{9}$/.test(form.phone)) { showError('phone', '请输入正确的11位手机号码'); return false }
    clearError('phone')
  } else if (field === 'code') {
    if (!form.code) { clearError('code'); return false }
    if (!/^\d{6}$/.test(form.code)) { showError('code', '验证码为6位数字'); return false }
    clearError('code')
  } else if (field === 'pwd') {
    if (!form.pwd) { clearError('pwd'); return false }
    if (form.pwd.length < 6 || form.pwd.length > 20) { showError('pwd', '密码长度为6-20位'); return false }
    if (!/[a-zA-Z]/.test(form.pwd) || !/\d/.test(form.pwd)) { showError('pwd', '密码需同时包含字母和数字'); return false }
    clearError('pwd')
    if (form.pwd2) validateField('pwd2')
  } else if (field === 'pwd2') {
    if (!form.pwd2) { clearError('pwd2'); return false }
    if (form.pwd2 !== form.pwd) { showError('pwd2', '两次密码输入不一致'); return false }
    clearError('pwd2')
  }
  return true
}

const sendCode = async () => {
  if (!form.phone || !/^1[3-9]\d{9}$/.test(form.phone)) {
    showError('phone', '请输入正确的手机号')
    return
  }
  sending.value = true
  try {
    const result = await authApi.sendCode({
      phone: form.phone,
      purpose: 'reset_password',
      role: props.role,
    })
    countdown.value = 60
    const timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) clearInterval(timer)
    }, 1000)
    if (result.dev_code) {
      alert(`验证码已发送（开发环境验证码：${result.dev_code}）`)
    }
  } catch (err) {
    formError.value = err instanceof Error ? err.message : '验证码发送失败'
  } finally {
    sending.value = false
  }
}

const submit = async () => {
  formError.value = ''
  if (!form.phone.trim()) { showError('phone', '请输入手机号') }
  if (!form.code.trim()) { showError('code', '请输入验证码') }
  if (!form.pwd) { showError('pwd', '请输入新密码') }
  if (!form.pwd2) { showError('pwd2', '请确认新密码') }
  if (!form.phone || !form.code || !form.pwd || !form.pwd2) return

  const valid1 = validateField('phone')
  const valid2 = validateField('code')
  const valid3 = validateField('pwd')
  const valid4 = validateField('pwd2')
  if (!valid1 || !valid2 || !valid3 || !valid4) return

  submitting.value = true
  try {
    await authApi.resetPassword({
      phone: form.phone,
      code: form.code,
      new_password: form.pwd,
      role: props.role,
    })
    alert('密码重置成功！请使用新密码登录。')
    emit('close')
  } catch (err) {
    formError.value = err instanceof Error ? err.message : '密码重置失败'
  } finally {
    submitting.value = false
  }
}
</script>

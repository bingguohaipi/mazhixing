<template>
  <div class="modal-mask">
    <div class="modal-box" style="width: 420px;">
      <h3 class="modal-title">绑定家长</h3>
      <p class="modal-sub">为 {{ studentName }} 绑定家长账号，家长可使用手机号登录查看学情</p>

      <div class="modal-field">
        <label class="modal-label">家长手机号 <span style="color:#ef4444">*</span></label>
        <input
          v-model="form.parent_phone"
          type="tel"
          class="modal-input"
          placeholder="请输入家长手机号"
        />
      </div>
      <div class="modal-field">
        <label class="modal-label">家长姓名</label>
        <input
          v-model="form.parent_name"
          type="text"
          class="modal-input"
          placeholder="可选，默认「家长用户」"
        />
      </div>

      <div v-if="formError" class="modal-error show" style="margin-bottom: 12px;">{{ formError }}</div>
      <div class="modal-actions">
        <button class="modal-btn-cancel" @click="$emit('close')">取消</button>
        <button class="modal-btn-confirm" :disabled="submitting" @click="submit">
          {{ submitting ? '绑定中...' : '确认绑定' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { classApi } from '@/api/classes'
import { toast } from '@/utils/toast'

const props = defineProps<{
  classId: number
  studentId: number
  studentName: string
}>()

const emit = defineEmits<{ close: []; success: [message: string] }>()

const submitting = ref(false)
const formError = ref('')
const form = reactive({
  parent_phone: '',
  parent_name: '',
})

const submit = async () => {
  formError.value = ''
  if (!/^1\d{10}$/.test(form.parent_phone.trim())) {
    formError.value = '请输入有效的11位手机号'
    return
  }

  submitting.value = true
  try {
    const result = await classApi.bindParent(props.classId, props.studentId, {
      parent_phone: form.parent_phone.trim(),
      parent_name: form.parent_name.trim() || undefined,
    })
    const message = result.default_password
      ? `绑定成功，新家长默认密码：${result.default_password}`
      : '绑定成功'
    toast.success(message)
    emit('success', message)
    emit('close')
  } catch (err) {
    formError.value = err instanceof Error ? err.message : '绑定失败'
  } finally {
    submitting.value = false
  }
}
</script>

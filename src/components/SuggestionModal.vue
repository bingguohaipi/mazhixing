<template>
  <div class="modal-mask">
    <div class="modal-box" style="width: 520px; max-height: 90vh; overflow-y: auto;">
      <h3 class="modal-title">我要建议</h3>
      <p class="modal-sub">向相关人员反馈题目或平台问题（可附图）</p>

      <div class="modal-field">
        <label class="modal-label">发送给</label>
        <input
          v-model="recipientKeyword"
          type="search"
          class="modal-input mb-2"
          placeholder="搜索姓名或账号"
        />
        <select v-model.number="form.to_user_id" class="modal-input" :disabled="!filteredRecipients.length">
          <option v-if="!filteredRecipients.length" :value="0">暂无可选对象</option>
          <option v-for="r in filteredRecipients" :key="r.id" :value="r.id">
            {{ roleLabel(r.role) }} · {{ r.display_name }}（{{ r.account }}）
          </option>
        </select>
        <p class="text-xs text-gray-500 mt-1">{{ recipientScopeHint }}</p>
      </div>

      <div class="modal-field">
        <label class="modal-label">标题 <span style="color:#ef4444">*</span></label>
        <input v-model="form.title" type="text" class="modal-input" maxlength="200" placeholder="简要概括建议主题" />
      </div>

      <div class="modal-field">
        <label class="modal-label">内容 <span style="color:#ef4444">*</span></label>
        <textarea v-model="form.content" class="modal-input" rows="4" placeholder="请描述问题或建议" />
      </div>

      <div class="modal-field">
        <label class="modal-label">图片（选填，最多 3 张）</label>
        <input type="file" accept="image/*" multiple @change="onPickImages">
        <div v-if="form.image_urls.length" class="flex gap-2 mt-2 flex-wrap">
          <button
            v-for="(url, idx) in form.image_urls"
            :key="idx"
            type="button"
            class="rounded border overflow-hidden hover:ring-2 hover:ring-indigo-400"
            @click="previewSrc = mediaUrl(url)"
          >
            <img :src="mediaUrl(url)" alt="" class="w-16 h-16 object-cover">
          </button>
        </div>
      </div>

      <div v-if="formError" class="modal-error show">{{ formError }}</div>
      <div class="modal-actions">
        <button class="modal-btn-cancel" @click="$emit('close')">取消</button>
        <button class="modal-btn-confirm" :disabled="submitting" @click="submit">
          {{ submitting ? '发送中...' : '发送' }}
        </button>
      </div>
    </div>
    <ImageLightbox :src="previewSrc" @close="previewSrc = null" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import ImageLightbox from '@/components/ImageLightbox.vue'
import { suggestionApi } from '@/api/suggestions'
import type { SuggestionRecipient } from '@/types/suggestion'
import { useAuthStore } from '@/stores/auth'
import { toast } from '@/utils/toast'

const props = defineProps<{
  contextType?: 'general' | 'problem'
  contextId?: number
  defaultToUserId?: number
}>()

const emit = defineEmits<{ close: []; success: [] }>()

const auth = useAuthStore()
const recipients = ref<SuggestionRecipient[]>([])
const recipientKeyword = ref('')
const previewSrc = ref<string | null>(null)
const submitting = ref(false)
const formError = ref('')
const form = reactive({
  to_user_id: 0,
  title: '',
  content: '',
  image_urls: [] as string[],
})

const roleLabel = (role: string) => {
  const map: Record<string, string> = { admin: '管理员', teacher: '教师', student: '学生', parent: '家长' }
  return map[role] ?? role
}

const recipientScopeHint = computed(() => {
  const map: Record<string, string> = {
    teacher: '可选：本班学生、其家长、管理员',
    student: '可选：任课教师、管理员',
    parent: '可选：孩子任课教师、管理员',
    admin: '可选：教师、学生、家长',
  }
  return map[auth.role ?? ''] ?? '请选择接收人'
})

const filteredRecipients = computed(() => {
  const needle = recipientKeyword.value.trim().toLowerCase()
  if (!needle) return recipients.value
  return recipients.value.filter(
    (item) =>
      item.display_name.toLowerCase().includes(needle)
      || item.account.toLowerCase().includes(needle),
  )
})

watch(filteredRecipients, (list) => {
  if (!list.length) {
    form.to_user_id = 0
    return
  }
  if (!list.some((item) => item.id === form.to_user_id)) {
    form.to_user_id = list[0].id
  }
})

const mediaUrl = (url: string) => {
  if (url.startsWith('http')) return url
  const base = import.meta.env.VITE_API_BASE_URL?.replace(/\/api\/v1$/, '') || ''
  return `${base}${url}`
}

const loadRecipients = async () => {
  recipients.value = await suggestionApi.listRecipients({
    context_type: props.contextType,
    context_id: props.contextId,
  })
  if (props.defaultToUserId && recipients.value.some((r) => r.id === props.defaultToUserId)) {
    form.to_user_id = props.defaultToUserId
  } else if (recipients.value.length) {
    form.to_user_id = recipients.value[0].id
  }
}

const onPickImages = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const files = input.files ? Array.from(input.files).slice(0, 3 - form.image_urls.length) : []
  for (const file of files) {
    try {
      const url = await suggestionApi.uploadImage(file)
      form.image_urls.push(url)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : '图片上传失败')
    }
  }
  input.value = ''
}

const submit = async () => {
  if (!form.title.trim()) {
    formError.value = '请填写标题'
    return
  }
  if (!form.content.trim()) {
    formError.value = '请填写建议内容'
    return
  }
  if (!form.to_user_id) {
    formError.value = '请选择接收人'
    return
  }
  submitting.value = true
  formError.value = ''
  try {
    await suggestionApi.create({
      to_user_id: form.to_user_id,
      title: form.title.trim(),
      content: form.content,
      context_type: props.contextType ?? 'general',
      context_id: props.contextId,
      image_urls: form.image_urls,
    })
    toast.success('建议已发送')
    emit('success')
    emit('close')
  } catch (err) {
    formError.value = err instanceof Error ? err.message : '发送失败'
  } finally {
    submitting.value = false
  }
}

onMounted(loadRecipients)
</script>

<template>
  <div class="problem-feedback-mask" @click.self="$emit('close')">
    <div class="problem-feedback-dialog" role="dialog" aria-labelledby="problem-feedback-title">
      <div class="problem-feedback-header">
        <h2 id="problem-feedback-title" class="problem-feedback-title">请填写反馈内容</h2>
        <button type="button" class="problem-feedback-close" aria-label="关闭" @click="$emit('close')">
          ×
        </button>
      </div>

      <div class="problem-feedback-body">
        <div class="problem-feedback-row">
          <span class="problem-feedback-label">题目：</span>
          <span class="problem-feedback-value">{{ problemTitle }}</span>
        </div>

        <div class="problem-feedback-row problem-feedback-row--top">
          <span class="problem-feedback-label">
            <span class="text-red-500">*</span> 反馈类型：
          </span>
          <div class="problem-feedback-tags">
            <button
              v-for="tag in feedbackTypes"
              :key="tag"
              type="button"
              class="problem-feedback-tag"
              :class="{ 'is-active': selectedType === tag }"
              @click="selectedType = tag"
            >
              {{ tag }}
            </button>
          </div>
        </div>

        <div class="problem-feedback-row problem-feedback-row--top">
          <span class="problem-feedback-label">
            <span class="text-red-500">*</span> 反馈内容：
          </span>
          <div class="problem-feedback-field-stack">
            <textarea
              v-model="content"
              class="problem-feedback-textarea"
              rows="6"
              placeholder="请详细描述您遇到的问题"
            />
            <div class="problem-feedback-images">
              <button
                v-for="(url, idx) in imageUrls"
                :key="url"
                type="button"
                class="problem-feedback-thumb"
                @click="previewSrc = mediaUrl(url)"
              >
                <img :src="mediaUrl(url)" alt="">
                <span
                  class="problem-feedback-thumb-remove"
                  title="移除"
                  @click.stop="removeImage(idx)"
                >
                  ×
                </span>
              </button>
              <label v-if="imageUrls.length < 3" class="problem-feedback-upload">
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp,image/gif"
                  class="sr-only"
                  @change="onPickImages"
                >
                <span class="problem-feedback-upload-icon">+</span>
                <span>添加图片</span>
              </label>
            </div>
            <p class="problem-feedback-images-hint">选填，最多 3 张</p>
          </div>
        </div>
      </div>

      <div v-if="formError" class="problem-feedback-error">{{ formError }}</div>

      <div class="problem-feedback-footer">
        <p class="problem-feedback-hint">反馈将发送给题目相关教师或管理员，可在「建议中心」查看回复</p>
        <div class="problem-feedback-actions">
          <button type="button" class="problem-feedback-btn-cancel" @click="$emit('close')">取消</button>
          <button
            type="button"
            class="problem-feedback-btn-confirm"
            :disabled="submitting || !canSubmit"
            @click="submit"
          >
            {{ submitting ? '提交中…' : '确认' }}
          </button>
        </div>
      </div>
    </div>
    <ImageLightbox :src="previewSrc" @close="previewSrc = null" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import ImageLightbox from '@/components/ImageLightbox.vue'
import { suggestionApi } from '@/api/suggestions'
import { toast } from '@/utils/toast'

const props = defineProps<{
  problemId: number
  problemTitle: string
}>()

const emit = defineEmits<{ close: []; success: [] }>()

const feedbackTypes = [
  '题目描述不清',
  '翻译错误',
  '题目过于简单',
  '题目考察点无意义',
  '其他',
] as const

const selectedType = ref<(typeof feedbackTypes)[number] | ''>('')
const content = ref('')
const imageUrls = ref<string[]>([])
const previewSrc = ref<string | null>(null)
const formError = ref('')
const submitting = ref(false)
const toUserId = ref(0)

const hasBody = computed(() => Boolean(content.value.trim() || imageUrls.value.length))

const canSubmit = computed(() => Boolean(selectedType.value && hasBody.value && toUserId.value))

const mediaUrl = (url: string) => {
  if (url.startsWith('http')) return url
  const base = import.meta.env.VITE_API_BASE_URL?.replace(/\/api\/v1$/, '') || ''
  return `${base}${url}`
}

const onPickImages = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  if (imageUrls.value.length >= 3) {
    toast.error('最多上传 3 张图片')
    return
  }
  try {
    const url = await suggestionApi.uploadImage(file)
    imageUrls.value = [...imageUrls.value, url]
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '图片上传失败')
  }
}

const removeImage = (index: number) => {
  imageUrls.value = imageUrls.value.filter((_, i) => i !== index)
}

const loadRecipient = async () => {
  const recipients = await suggestionApi.listRecipients({
    context_type: 'problem',
    context_id: props.problemId,
  })
  toUserId.value = recipients[0]?.id ?? 0
}

const submit = async () => {
  if (!selectedType.value) {
    formError.value = '请选择反馈类型'
    return
  }
  if (!hasBody.value) {
    formError.value = '请填写反馈内容或添加图片'
    return
  }
  if (!toUserId.value) {
    formError.value = '暂无可接收反馈的对象，请稍后再试'
    return
  }
  submitting.value = true
  formError.value = ''
  const text = content.value.trim()
  const body = text
    ? `【反馈类型】${selectedType.value}\n\n${text}`
    : `【反馈类型】${selectedType.value}\n\n（见附图）`
  try {
    await suggestionApi.create({
      to_user_id: toUserId.value,
      title: selectedType.value,
      content: body,
      context_type: 'problem',
      context_id: props.problemId,
      image_urls: imageUrls.value,
    })
    toast.success('反馈已提交')
    emit('success')
    emit('close')
  } catch (err) {
    formError.value = err instanceof Error ? err.message : '提交失败'
  } finally {
    submitting.value = false
  }
}

onMounted(loadRecipient)
</script>

<style scoped>
/* 深色反馈弹窗（与做题页暗色背景一致） */
.problem-feedback-mask {
  --pfb-surface: #0a0a0f;
  --pfb-input: #16161f;
  --pfb-text: #ffffff;
  --pfb-text-muted: #8888a0;
  --pfb-border: #353548;
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.62);
}

.problem-feedback-dialog {
  width: 100%;
  max-width: 640px;
  max-height: 90vh;
  overflow-y: auto;
  color-scheme: dark;
  background: var(--pfb-surface);
  color: var(--pfb-text);
  border: 1px solid var(--pfb-border);
  border-radius: 8px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.45);
}

.problem-feedback-header,
.problem-feedback-body,
.problem-feedback-footer {
  background: var(--pfb-surface);
}

.problem-feedback-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--pfb-border);
}

.problem-feedback-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--pfb-text);
}

.problem-feedback-close {
  border: none;
  background: var(--pfb-surface);
  font-size: 1.25rem;
  line-height: 1;
  color: #9ca3af;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
}

.problem-feedback-close:hover {
  color: var(--pfb-text);
}

.problem-feedback-body {
  padding: 1.25rem 1.5rem 0.5rem;
}

.problem-feedback-field-stack {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  min-width: 0;
}

.problem-feedback-row {
  display: grid;
  grid-template-columns: 7.5rem 1fr;
  gap: 0.75rem 1rem;
  align-items: center;
  margin-bottom: 1.25rem;
}

.problem-feedback-row--top {
  align-items: start;
}

.problem-feedback-label {
  text-align: right;
  font-size: 0.875rem;
  color: var(--pfb-text-muted);
  line-height: 1.5;
}

.problem-feedback-value {
  font-size: 0.875rem;
  color: var(--pfb-text);
}

.problem-feedback-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.problem-feedback-tag {
  padding: 0.35rem 0.75rem;
  font-size: 0.8125rem;
  color: #e4e4e7;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.35);
  border-radius: 9999px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s, color 0.15s;
}

.problem-feedback-tag:hover {
  border-color: rgba(255, 255, 255, 0.55);
  background: rgba(255, 255, 255, 0.04);
}

.problem-feedback-tag.is-active {
  background: rgba(255, 255, 255, 0.1);
  border-color: #ffffff;
  color: #ffffff;
}

.problem-feedback-textarea {
  width: 100%;
  min-height: 140px;
  padding: 0.75rem 1rem;
  font-size: 0.875rem;
  line-height: 1.5;
  color: var(--pfb-text);
  background: var(--pfb-input);
  border: 1px solid var(--pfb-border);
  border-radius: 8px;
  resize: vertical;
  outline: none;
  -webkit-text-fill-color: var(--pfb-text);
}

.problem-feedback-textarea::placeholder {
  color: var(--pfb-text-muted);
}

.problem-feedback-textarea:focus {
  border-color: #52525b;
  box-shadow: none;
}

.problem-feedback-images {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
}

.problem-feedback-thumb {
  position: relative;
  width: 4rem;
  height: 4rem;
  padding: 0;
  border: 1px solid var(--pfb-border);
  border-radius: 8px;
  overflow: hidden;
  background: var(--pfb-input);
  cursor: pointer;
}

.problem-feedback-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.problem-feedback-thumb-remove {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 1.125rem;
  height: 1.125rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.875rem;
  line-height: 1;
  color: #fff;
  background: rgba(0, 0, 0, 0.55);
  border-radius: 9999px;
  cursor: pointer;
}

.problem-feedback-upload {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.15rem;
  width: 4rem;
  height: 4rem;
  font-size: 0.625rem;
  color: var(--pfb-text-muted);
  background: transparent;
  border: 1px dashed #52525b;
  border-radius: 8px;
  cursor: pointer;
}

.problem-feedback-upload:hover {
  border-color: #71717a;
  color: #d4d4d8;
}

.problem-feedback-upload-icon {
  font-size: 1.25rem;
  line-height: 1;
  color: var(--pfb-text-muted);
}

.problem-feedback-images-hint {
  margin: 0;
  font-size: 0.75rem;
  color: var(--pfb-text-muted);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.problem-feedback-error {
  margin: 0 1.5rem;
  font-size: 0.8125rem;
  color: #dc2626;
  background: var(--pfb-surface);
}

.problem-feedback-footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.5rem 1.25rem;
  margin-top: 0.5rem;
}

.problem-feedback-hint {
  margin: 0;
  flex: 1;
  min-width: 12rem;
  font-size: 0.75rem;
  color: var(--pfb-text-muted);
}

.problem-feedback-actions {
  display: flex;
  gap: 0.75rem;
  margin-left: auto;
}

.problem-feedback-btn-cancel {
  padding: 0.5rem 1.25rem;
  font-size: 0.875rem;
  color: #111827;
  background: #ffffff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.problem-feedback-btn-cancel:hover {
  background: #f4f4f5;
}

.problem-feedback-btn-confirm {
  padding: 0.5rem 1.25rem;
  font-size: 0.875rem;
  color: var(--pfb-text-muted);
  background: #353548;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.problem-feedback-btn-confirm:not(:disabled) {
  color: #0a0a0f;
  background: #7dd3a8;
}

.problem-feedback-btn-confirm:not(:disabled):hover {
  background: #5bc492;
}

.problem-feedback-btn-confirm:disabled {
  cursor: not-allowed;
}

:global(.dark-mode) .problem-feedback-mask textarea.problem-feedback-textarea,
:global(html[data-app-role='teacher'].dark-mode) .problem-feedback-mask textarea.problem-feedback-textarea {
  background: var(--pfb-input) !important;
  color: var(--pfb-text) !important;
  -webkit-text-fill-color: var(--pfb-text) !important;
  border-color: var(--pfb-border) !important;
}

:global(.dark-mode) .problem-feedback-mask textarea.problem-feedback-textarea::placeholder,
:global(html[data-app-role='teacher'].dark-mode) .problem-feedback-mask textarea.problem-feedback-textarea::placeholder {
  color: var(--pfb-text-muted) !important;
}
</style>

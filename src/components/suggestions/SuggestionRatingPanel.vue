<template>
  <div class="suggestion-rating-panel">
    <p class="suggestion-rating-panel__label">请对本次处理结果打分（1–5 分）</p>
    <div class="suggestion-rating-panel__stars" role="group" aria-label="满意度评分">
      <button
        v-for="n in 5"
        :key="n"
        type="button"
        class="suggestion-rating-panel__star"
        :class="{ 'is-active': n <= (hoverScore || selectedScore) }"
        :disabled="submitting"
        :aria-label="`${n} 分`"
        @click="selectedScore = n"
        @mouseenter="hoverScore = n"
        @mouseleave="hoverScore = 0"
      >
        ★
      </button>
    </div>
    <button
      type="button"
      class="suggestion-rating-panel__submit"
      :disabled="!selectedScore || submitting"
      @click="submit"
    >
      {{ submitting ? '提交中…' : '提交评分' }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { suggestionApi } from '@/api/suggestions'
import { toast } from '@/utils/toast'

const props = defineProps<{
  suggestionId: number
}>()

const emit = defineEmits<{ rated: [] }>()

const selectedScore = ref(0)
const hoverScore = ref(0)
const submitting = ref(false)

const submit = async () => {
  if (!selectedScore.value) return
  submitting.value = true
  try {
    await suggestionApi.rate(props.suggestionId, { score: selectedScore.value })
    toast.success('感谢您的评分')
    emit('rated')
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '评分失败')
  } finally {
    submitting.value = false
  }
}
</script>

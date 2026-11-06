<template>
  <button type="button" class="suggestion-list-row" @click="$emit('open', item.id)">
    <div class="suggestion-list-row__icon" aria-hidden="true">
      <span class="suggestion-list-row__icon-inner">⏳</span>
    </div>
    <div class="suggestion-list-row__body">
      <p class="suggestion-list-row__title">{{ item.title }}</p>
      <p class="suggestion-list-row__ref">{{ refNo }}</p>
      <p class="suggestion-list-row__content">{{ item.content }}</p>
      <div class="suggestion-list-row__meta">
        <span :class="['suggestion-status', statusClass]">{{ statusText }}</span>
        <span class="suggestion-list-row__time">{{ listTime }}</span>
      </div>
    </div>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { SuggestionItem } from '@/types/suggestion'
import {
  formatSuggestionListTime,
  formatSuggestionRef,
  suggestionStatusClass,
  suggestionStatusLabel,
} from '@/utils/suggestionDisplay'

const props = defineProps<{
  item: SuggestionItem
}>()

defineEmits<{ open: [id: number] }>()

const refNo = computed(() => formatSuggestionRef(props.item.id, props.item.created_at))
const listTime = computed(() => formatSuggestionListTime(props.item.created_at))
const statusText = computed(() => suggestionStatusLabel(props.item.status))
const statusClass = computed(() => suggestionStatusClass(props.item.status))
</script>

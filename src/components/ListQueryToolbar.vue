<template>
  <div class="list-query-toolbar" :class="{ 'list-query-toolbar--compact': compact }">
    <label class="list-query-toolbar-search">
      <span class="list-query-toolbar-search-icon" aria-hidden="true">🔍</span>
      <input
        :value="keyword"
        type="search"
        class="list-query-toolbar-input"
        :placeholder="placeholder"
        @input="emit('update:keyword', ($event.target as HTMLInputElement).value)"
      >
    </label>
    <select
      v-if="sortOptions.length"
      :value="sortValue"
      class="list-query-toolbar-sort"
      @change="emit('update:sortValue', ($event.target as HTMLSelectElement).value)"
    >
      <option v-for="opt in sortOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
    </select>
    <div v-if="$slots.filter" ref="filterWrapRef" class="list-query-toolbar-filter-wrap">
      <button
        type="button"
        class="list-query-toolbar-filter-btn"
        :class="{ 'is-active': filterActive }"
        :aria-label="filterAriaLabel"
        @click.stop="emit('toggleFilter')"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4">
          <path
            fill-rule="evenodd"
            d="M2 3.5A.5.5 0 0 1 2.5 3h15a.5.5 0 0 1 .394.808l-5.29 6.593A1 1 0 0 0 12.5 11v4.5a.5.5 0 0 1-.276.447l-2 1A.5.5 0 0 1 9.724 16.5V11a1 1 0 0 0-.104-.402L2.606 3.808A.5.5 0 0 1 2.5 3.5Z"
            clip-rule="evenodd"
          />
        </svg>
        <span v-if="filterActive" class="list-query-toolbar-filter-dot" />
      </button>
      <slot name="filter" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

export type ListQuerySortOption = { value: string; label: string }

const filterWrapRef = ref<HTMLElement | null>(null)
defineExpose({ filterWrapRef })

withDefaults(
  defineProps<{
    keyword: string
    placeholder?: string
    sortValue?: string
    sortOptions?: ListQuerySortOption[]
    filterActive?: boolean
    filterAriaLabel?: string
    compact?: boolean
  }>(),
  {
    placeholder: '搜索',
    sortValue: '',
    sortOptions: () => [],
    filterActive: false,
    filterAriaLabel: '筛选',
    compact: false,
  },
)

const emit = defineEmits<{
  'update:keyword': [value: string]
  'update:sortValue': [value: string]
  toggleFilter: []
}>()
</script>

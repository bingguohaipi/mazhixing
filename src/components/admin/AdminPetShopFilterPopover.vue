<template>
  <div
    v-if="open"
    class="practice-filter-popover absolute right-0 top-[calc(100%+6px)] z-30 w-[260px] border border-gray-200 bg-white p-3.5"
    role="dialog"
    aria-label="筛选商品"
    @click.stop
    @mousedown.stop
  >
    <div class="practice-filter-title">筛选</div>
    <label class="block mt-3">
      <span class="practice-filter-label">类型</span>
      <select
        :value="category"
        class="practice-filter-select"
        @change="emit('update:category', ($event.target as HTMLSelectElement).value)"
      >
        <option value="">全部</option>
        <option value="pet">宠物</option>
        <option value="food">食物</option>
        <option value="drink">饮料</option>
      </select>
    </label>
    <div class="practice-filter-footer">
      <button type="button" class="practice-filter-btn-reset" @click="emit('reset')">重置</button>
      <button type="button" class="practice-filter-btn-apply" @click="emit('apply')">应用</button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  open: boolean
  category: string
}>()

const emit = defineEmits<{
  'update:category': [value: string]
  apply: []
  reset: []
}>()
</script>

<template>
  <div
    v-if="open"
    class="practice-filter-popover absolute right-0 top-[calc(100%+6px)] z-30 w-[260px] border border-gray-200 bg-white p-3.5"
    role="dialog"
    aria-label="筛选用户"
    @click.stop
    @mousedown.stop
  >
    <div class="practice-filter-title">筛选</div>
    <label class="block mt-3">
      <span class="practice-filter-label">角色</span>
      <select
        :value="role"
        class="practice-filter-select"
        @change="emit('update:role', ($event.target as HTMLSelectElement).value)"
      >
        <option value="">全部角色</option>
        <option value="teacher">教师</option>
        <option value="student">学生</option>
        <option value="parent">家长</option>
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
  role: string
}>()

const emit = defineEmits<{
  'update:role': [value: string]
  apply: []
  reset: []
}>()
</script>

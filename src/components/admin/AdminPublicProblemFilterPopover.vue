<template>
  <div
    v-if="open"
    class="practice-filter-popover absolute right-0 top-[calc(100%+6px)] z-30 w-[260px] border border-gray-200 bg-white p-3.5"
    role="dialog"
    aria-label="筛选题目"
    @click.stop
    @mousedown.stop
  >
    <div class="practice-filter-title">筛选</div>
    <div class="space-y-3 mt-3">
      <label class="block">
        <span class="practice-filter-label">难度</span>
        <select
          :value="difficulty"
          class="practice-filter-select"
          @change="emit('update:difficulty', ($event.target as HTMLSelectElement).value)"
        >
          <option value="">全部</option>
          <option value="入门">入门</option>
          <option value="简单">简单</option>
          <option value="中等">中等</option>
          <option value="困难">困难</option>
        </select>
      </label>
      <label class="block">
        <span class="practice-filter-label">上架状态</span>
        <select
          :value="status"
          class="practice-filter-select"
          @change="emit('update:status', ($event.target as HTMLSelectElement).value)"
        >
          <option value="">全部状态</option>
          <option value="published">已上架</option>
          <option value="archived">已下架</option>
          <option value="draft">草稿</option>
        </select>
      </label>
    </div>
    <div class="practice-filter-footer">
      <button type="button" class="practice-filter-btn-reset" @click="emit('reset')">重置</button>
      <button type="button" class="practice-filter-btn-apply" @click="emit('apply')">应用</button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  open: boolean
  difficulty: string
  status: string
}>()

const emit = defineEmits<{
  'update:difficulty': [value: string]
  'update:status': [value: string]
  apply: []
  reset: []
}>()
</script>

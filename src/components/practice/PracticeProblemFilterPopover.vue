<template>
  <Teleport to="body" :disabled="!teleportToBody">
    <div
      v-if="open"
      ref="rootEl"
      class="practice-filter-popover z-[10001] w-[260px] border border-gray-200 bg-white p-3.5"
      :class="teleportToBody ? 'problem-pick-filter-popover-fixed' : 'absolute right-0 top-[calc(100%+6px)]'"
      :style="teleportToBody ? fixedStyle : undefined"
      role="dialog"
      aria-label="筛选题目"
      @click.stop
      @mousedown.stop
    >
    <div class="practice-filter-title">筛选</div>
    <div class="space-y-3">
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
      <label v-if="showKnowledgePoint" class="block">
        <span class="practice-filter-label">知识点</span>
        <select
          :value="knowledgePoint"
          class="practice-filter-select"
          @change="emit('update:knowledgePoint', ($event.target as HTMLSelectElement).value)"
        >
          <option value="">全部</option>
          <option v-for="opt in knowledgePointOptions" :key="opt.name" :value="opt.name">
            {{ opt.name }}
          </option>
        </select>
      </label>
      <label v-if="showLanguage" class="block">
        <span class="practice-filter-label">语言</span>
        <select
          :value="language"
          class="practice-filter-select"
          @change="emit('update:language', ($event.target as HTMLSelectElement).value)"
        >
          <option value="">全部</option>
          <option value="Python">Python</option>
          <option value="C++">C++</option>
        </select>
      </label>
      <label v-if="showMyPassed" class="block">
        <span class="practice-filter-label">我的进度</span>
        <select
          :value="myPassed"
          class="practice-filter-select"
          @change="emit('update:myPassed', ($event.target as HTMLSelectElement).value)"
        >
          <option value="">全部题目</option>
          <option value="passed">我已通过 (AC)</option>
        </select>
      </label>
    </div>
    <div class="practice-filter-footer">
      <button type="button" class="practice-filter-btn-reset" @click="emit('reset')">重置</button>
      <button type="button" class="practice-filter-btn-apply" @click="emit('apply')">应用</button>
    </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { CSSProperties } from 'vue'
import type { KnowledgePointOptionItem } from '@/types/practice'

const rootEl = ref<HTMLElement | null>(null)

withDefaults(
  defineProps<{
    open: boolean
    difficulty: string
    knowledgePoint: string
    language: string
    showKnowledgePoint?: boolean
    showLanguage?: boolean
    showMyPassed?: boolean
    myPassed?: string
    knowledgePointOptions: KnowledgePointOptionItem[]
    teleportToBody?: boolean
    fixedStyle?: CSSProperties
  }>(),
  {
    showKnowledgePoint: true,
    showLanguage: true,
    showMyPassed: false,
    myPassed: '',
    teleportToBody: false,
    fixedStyle: () => ({}),
  },
)

defineExpose({ rootEl })

const emit = defineEmits<{
  'update:difficulty': [value: string]
  'update:knowledgePoint': [value: string]
  'update:language': [value: string]
  'update:myPassed': [value: string]
  apply: []
  reset: []
}>()
</script>

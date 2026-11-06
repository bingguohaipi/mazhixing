<template>
  <ListQueryToolbar
    ref="toolbarRef"
    :keyword="keyword"
    :placeholder="placeholder"
    :filter-active="activeFilterCount > 0"
    filter-aria-label="筛选题目"
    @update:keyword="emit('update:keyword', $event)"
    @toggle-filter="toggleFilter"
  >
    <template #filter>
      <PracticeProblemFilterPopover
        :open="filterOpen"
        teleport-to-body
        :show-language="false"
        :fixed-style="popoverFixedStyle"
        :difficulty="draftDifficulty"
        :knowledge-point="draftKnowledgePoint"
        language=""
        :knowledge-point-options="knowledgePointOptions"
        @update:difficulty="draftDifficulty = $event"
        @update:knowledge-point="draftKnowledgePoint = $event"
        @apply="onApply"
        @reset="onReset"
      />
    </template>
  </ListQueryToolbar>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch, type CSSProperties } from 'vue'
import ListQueryToolbar from '@/components/ListQueryToolbar.vue'
import type { ComponentPublicInstance } from 'vue'
import PracticeProblemFilterPopover from '@/components/practice/PracticeProblemFilterPopover.vue'
import type { KnowledgePointOptionItem } from '@/types/practice'

const props = defineProps<{
  keyword: string
  placeholder: string
  difficulty: string
  knowledgePoint: string
  activeFilterCount: number
  knowledgePointOptions: KnowledgePointOptionItem[]
}>()

const emit = defineEmits<{
  'update:keyword': [value: string]
  'update:difficulty': [value: string]
  'update:knowledgePoint': [value: string]
  apply: []
  reset: []
}>()

const filterOpen = ref(false)
const toolbarRef = ref<ComponentPublicInstance<{ filterWrapRef: HTMLElement | null }> | null>(null)
const popoverFixedStyle = ref<CSSProperties>({})
const POPOVER_WIDTH = 260

const updatePopoverPosition = () => {
  const el = toolbarRef.value?.filterWrapRef ?? null
  if (!el) return
  const rect = el.getBoundingClientRect()
  const left = Math.min(Math.max(8, rect.right - POPOVER_WIDTH), window.innerWidth - POPOVER_WIDTH - 8)
  popoverFixedStyle.value = {
    position: 'fixed',
    top: `${rect.bottom + 6}px`,
    left: `${left}px`,
  }
}

const draftDifficulty = ref('')
const draftKnowledgePoint = ref('')

const syncDraftFromApplied = () => {
  draftDifficulty.value = props.difficulty
  draftKnowledgePoint.value = props.knowledgePoint
}

const bindPositionListeners = () => {
  window.addEventListener('scroll', updatePopoverPosition, true)
  window.addEventListener('resize', updatePopoverPosition)
}

const unbindPositionListeners = () => {
  window.removeEventListener('scroll', updatePopoverPosition, true)
  window.removeEventListener('resize', updatePopoverPosition)
}

const toggleFilter = () => {
  if (!filterOpen.value) {
    syncDraftFromApplied()
  }
  filterOpen.value = !filterOpen.value
  if (filterOpen.value) {
    void nextTick(() => {
      updatePopoverPosition()
      bindPositionListeners()
    })
  } else {
    unbindPositionListeners()
  }
}

const onApply = () => {
  emit('update:difficulty', draftDifficulty.value)
  emit('update:knowledgePoint', draftKnowledgePoint.value)
  filterOpen.value = false
  emit('apply')
}

const onReset = () => {
  draftDifficulty.value = ''
  draftKnowledgePoint.value = ''
  emit('update:difficulty', '')
  emit('update:knowledgePoint', '')
  filterOpen.value = false
  emit('reset')
}

function onDocumentClick(event: MouseEvent) {
  if (!filterOpen.value) return
  const target = event.target as HTMLElement
  if (target.closest('.practice-filter-popover')) return
  if (target.closest('.list-query-toolbar-filter-btn')) return
  filterOpen.value = false
  unbindPositionListeners()
}

watch(filterOpen, (open) => {
  document.removeEventListener('mousedown', onDocumentClick)
  if (open) {
    void nextTick(() => {
      document.addEventListener('mousedown', onDocumentClick)
    })
  } else {
    unbindPositionListeners()
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('mousedown', onDocumentClick)
  unbindPositionListeners()
})
</script>

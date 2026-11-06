<template>
  <div ref="rootRef" class="toolbar-select inline-block min-w-0" :class="wrapperClass">
    <button
      type="button"
      class="select-field-flat toolbar-select-trigger w-full rounded-lg border border-gray-200 px-3 py-1.5 text-sm text-left"
      :aria-expanded="open"
      aria-haspopup="listbox"
      @click="toggle"
    >
      <span class="toolbar-select-label block truncate">{{ currentLabel }}</span>
    </button>
    <Teleport to="body">
      <div v-if="open" class="toolbar-select-backdrop fixed inset-0 z-[200]" @click="close" />
      <ul
        v-if="open"
        class="toolbar-select-menu fixed z-[201] max-h-60 overflow-y-auto"
        :style="menuStyle"
        role="listbox"
      >
        <li
          v-for="opt in options"
          :key="String(opt.value)"
          role="option"
          class="toolbar-select-option"
          :class="{ 'is-selected': opt.value === modelValue }"
          @click="choose(opt.value)"
        >
          {{ opt.label }}
        </li>
      </ul>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'

export interface ToolbarSelectOption {
  value: string | number | null
  label: string
}

const props = withDefaults(
  defineProps<{
    modelValue: string | number | null
    options: ToolbarSelectOption[]
    placeholder?: string
    wrapperClass?: string
  }>(),
  { placeholder: '请选择' },
)

const emit = defineEmits<{
  'update:modelValue': [value: string | number | null]
  change: [value: string | number | null]
}>()

const open = ref(false)
const rootRef = ref<HTMLElement | null>(null)
const menuStyle = ref<{ top: string; left: string; minWidth: string }>({
  top: '0px',
  left: '0px',
  minWidth: '0px',
})

const currentLabel = computed(() => {
  const hit = props.options.find((opt) => opt.value === props.modelValue)
  return hit?.label ?? props.placeholder
})

const updateMenuPosition = () => {
  const btn = rootRef.value?.querySelector('button')
  if (!btn) return
  const rect = btn.getBoundingClientRect()
  const gap = 4
  menuStyle.value = {
    top: `${rect.bottom + gap}px`,
    left: `${rect.left}px`,
    minWidth: `${rect.width}px`,
  }
}

const close = () => {
  open.value = false
}

const toggle = () => {
  open.value = !open.value
  if (open.value) {
    void nextTick(updateMenuPosition)
  }
}

const choose = (value: string | number | null) => {
  if (value !== props.modelValue) {
    emit('update:modelValue', value)
    emit('change', value)
  }
  close()
}

const onWindowChange = () => {
  if (open.value) updateMenuPosition()
}

watch(open, (isOpen) => {
  if (isOpen) {
    window.addEventListener('resize', onWindowChange)
    window.addEventListener('scroll', onWindowChange, true)
  } else {
    window.removeEventListener('resize', onWindowChange)
    window.removeEventListener('scroll', onWindowChange, true)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onWindowChange)
  window.removeEventListener('scroll', onWindowChange, true)
})
</script>

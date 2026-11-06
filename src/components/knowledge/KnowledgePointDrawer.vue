<template>
  <Teleport to="body">
    <Transition name="kp-drawer-fade">
      <div v-if="open" class="kp-drawer-root fixed inset-0 z-[960]" @click.self="emit('close')">
        <aside
          class="kp-drawer-panel fixed top-0 right-0 h-full w-[min(480px,100vw)] bg-white border-l border-gray-200 shadow-2xl flex flex-col"
          role="dialog"
          aria-labelledby="kp-drawer-title"
        >
          <header class="flex items-center justify-between px-5 py-4 border-b border-gray-100 shrink-0">
            <h2 id="kp-drawer-title" class="text-lg font-semibold text-gray-900">描述</h2>
            <button
              type="button"
              class="w-8 h-8 rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-700"
              aria-label="关闭"
              @click="emit('close')"
            >
              ✕
            </button>
          </header>
          <div class="flex-1 overflow-y-auto px-5 py-4 kp-markdown text-sm text-gray-700" v-html="html" />
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { renderMarkdown } from '@/utils/render-markdown'

const props = defineProps<{
  open: boolean
  contentMarkdown: string
}>()

const emit = defineEmits<{ close: [] }>()

const html = computed(() => renderMarkdown(props.contentMarkdown || ''))
</script>

<style scoped>
.kp-drawer-fade-enter-active,
.kp-drawer-fade-leave-active {
  transition: opacity 0.2s ease;
}
.kp-drawer-fade-enter-active .kp-drawer-panel,
.kp-drawer-fade-leave-active .kp-drawer-panel {
  transition: transform 0.25s ease;
}
.kp-drawer-fade-enter-from,
.kp-drawer-fade-leave-to {
  opacity: 0;
}
.kp-drawer-fade-enter-from .kp-drawer-panel,
.kp-drawer-fade-leave-to .kp-drawer-panel {
  transform: translateX(100%);
}

.kp-drawer-root {
  background: rgba(0, 0, 0, 0.35);
}
</style>

<style>
.dark-mode .kp-drawer-panel {
  background-color: #0a0a0f !important;
  border-color: #1f1f2e !important;
}
.dark-mode .kp-drawer-panel h2,
.dark-mode .kp-drawer-panel .text-gray-900 {
  color: #e8e8f0 !important;
}
.dark-mode .kp-markdown {
  color: #c8c8d8 !important;
}
.kp-markdown h2 {
  font-size: 1rem;
  font-weight: 600;
  margin: 1.25rem 0 0.5rem;
  color: inherit;
}
.kp-markdown h2:first-child {
  margin-top: 0;
}
.kp-markdown p {
  margin: 0.5rem 0;
  line-height: 1.65;
}
.kp-markdown pre {
  background: #1e1e2e;
  color: #e8e8f0;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  overflow-x: auto;
  margin: 0.75rem 0;
  font-size: 12px;
}
.kp-markdown code {
  font-family: ui-monospace, monospace;
  font-size: 0.92em;
}
</style>

<template>
  <Teleport to="body">
    <div
      v-if="src"
      class="fixed inset-0 z-[2000] flex items-center justify-center bg-black/80 p-4"
      role="dialog"
      aria-modal="true"
      @click.self="close"
    >
      <button
        type="button"
        class="absolute top-4 right-4 text-white/90 hover:text-white text-2xl leading-none"
        aria-label="关闭"
        @click="close"
      >
        ×
      </button>
      <img :src="src" alt="预览" class="max-w-full max-h-[90vh] rounded-lg shadow-2xl object-contain" />
    </div>
  </Teleport>
</template>

<script setup lang="ts">
defineProps<{ src: string | null }>()
const emit = defineEmits<{ close: [] }>()

const close = () => emit('close')
</script>

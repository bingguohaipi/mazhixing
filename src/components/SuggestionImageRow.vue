<template>
  <div v-if="urls.length" class="flex flex-wrap gap-2">
    <button
      v-for="(url, idx) in urls"
      :key="idx"
      type="button"
      class="rounded border border-gray-200 overflow-hidden hover:ring-2 hover:ring-indigo-400 focus:outline-none"
      @click="emit('preview', resolve(url))"
    >
      <img :src="resolve(url)" class="w-16 h-16 object-cover" alt="建议附图" />
    </button>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ urls: string[] }>()
const emit = defineEmits<{ preview: [url: string] }>()

const resolve = (url: string) => {
  if (url.startsWith('http')) return url
  const base = import.meta.env.VITE_API_BASE_URL?.replace(/\/api\/v1$/, '') || ''
  return `${base}${url}`
}
</script>

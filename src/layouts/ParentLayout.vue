<template>
  <div>
    <div class="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between flex-wrap gap-3">
      <div class="flex items-center gap-3">
        <h1 class="text-lg font-semibold text-gray-900">家长学情</h1>
        <span class="badge bg-purple-100 text-purple-700">家长端</span>
      </div>
      <div v-if="!isProfilePage && children.length > 0" class="flex items-center gap-3">
        <select
          v-model="selectedStudentId"
          class="px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
          @change="onContextChange"
        >
          <option v-for="child in children" :key="child.student_id" :value="child.student_id">
            {{ child.display_name }}
          </option>
        </select>
        <select
          v-model="period"
          class="px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
          @change="onContextChange"
        >
          <option value="7">近 7 天</option>
          <option value="30">近 30 天</option>
        </select>
      </div>
    </div>

    <RouterView />
  </div>
</template>

<script setup lang="ts">
import { computed, onActivated, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useParentContext } from '@/composables/useParentContext'
import { usePageDwell } from '@/composables/usePageDwell'
import { trackEvent } from '@/utils/tracker'

const route = useRoute()
const { children, selectedStudentId, period, loadOverview, initParentContext } = useParentContext()

usePageDwell('parent_page_dwell', '/parent', 'parent')

const isProfilePage = computed(() => route.name === 'parent-profile')

const onContextChange = () => {
  void loadOverview()
}

onMounted(() => {
  trackEvent({ event_name: 'parent_page_view', page: '/parent', module: 'parent' })
  void initParentContext()
})

onActivated(() => {
  void initParentContext()
})
</script>

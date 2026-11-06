<template>
  <div>
    <div v-if="loading" class="p-6 text-center text-gray-500">加载中...</div>
    <div v-else-if="!overview" class="p-12 text-center text-gray-500">暂无数据</div>
    <div v-else class="p-6">
      <div class="surface-dark-card rounded-xl p-5">
        <h3 class="font-semibold text-gray-900 mb-4">高频错题 TOP3</h3>
        <div v-if="overview.top_wrong_problems.length === 0" class="text-sm text-gray-500 py-6 text-center">
          太棒了，暂无错题
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="(item, idx) in overview.top_wrong_problems"
            :key="item.problem_id"
            class="wrong-top-item flex items-center justify-between gap-3"
          >
            <div>
              <span class="text-sm font-medium text-gray-900">{{ idx + 1 }}. #{{ item.problem_id }} {{ item.title }}</span>
              <span class="text-xs text-gray-500 ml-2">{{ item.knowledge_point || '未分类' }}</span>
            </div>
            <span class="text-sm text-red-600 font-medium">错 {{ item.wrong_count }} 次</span>
          </div>
        </div>
        <div class="mt-4 text-center">
          <RouterLink
            to="/parent/wrong-book"
            class="wrong-top-link"
            @click="trackViewAll"
          >
            查看全部错题 →
          </RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useParentContext } from '@/composables/useParentContext'
import { trackEvent } from '@/utils/tracker'

const { overview, loading } = useParentContext()

const trackViewAll = () => {
  trackEvent({ event_name: 'parent_wrong_book_link', page: '/parent/wrong-top', module: 'parent' })
}

onMounted(() => {
  trackEvent({ event_name: 'parent_wrong_top_view', page: '/parent/wrong-top', module: 'parent' })
})
</script>

<style scoped>
.wrong-top-item {
  padding: 12px;
  border-radius: 8px;
  background: #0f0f16;
  border: 1px solid rgba(239, 68, 68, 0.22);
}

.wrong-top-item :deep(.text-gray-900),
.wrong-top-item .title-text {
  color: #f0f0f5;
}

.wrong-top-item :deep(.text-gray-500) {
  color: #787890;
}

.wrong-top-item :deep(.text-red-600) {
  color: #f87171;
}

.wrong-top-link {
  display: inline-flex;
  padding: 8px 16px;
  font-size: 14px;
  color: #a5b4fc;
  background: #0f0f16;
  border: 1px solid rgba(99, 102, 241, 0.28);
  border-radius: 8px;
  text-decoration: none;
  transition: border-color 0.2s;
}

.wrong-top-link:hover {
  border-color: rgba(99, 102, 241, 0.45);
}
</style>

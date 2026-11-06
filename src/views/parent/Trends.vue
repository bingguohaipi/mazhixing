<template>
  <div>
    <div v-if="loading" class="p-6 text-center text-gray-500">加载中...</div>
    <div v-else-if="!overview" class="p-12 text-center text-gray-500">暂无数据</div>
    <div v-else class="p-6">
      <div class="surface-dark-card rounded-xl p-5">
        <h3 class="font-semibold text-gray-900 mb-4">近{{ overview.learning_trend.length }}天学习趋势</h3>
        <TrendBarChart :items="overview.learning_trend" />
        <p class="text-xs text-gray-400 mt-4 text-center">统计近 {{ overview.period_days }} 天内有效提交次数</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineAsyncComponent, onMounted } from 'vue'

const TrendBarChart = defineAsyncComponent(
  () => import('@/components/charts/TrendBarChart.vue'),
)
import { useParentContext } from '@/composables/useParentContext'
import { trackEvent } from '@/utils/tracker'

const { overview, loading } = useParentContext()

onMounted(() => {
  trackEvent({ event_name: 'parent_trends_view', page: '/parent/trends', module: 'parent' })
})
</script>

<template>
  <div>
    <div v-if="loading" class="p-6 text-center text-gray-500">加载中...</div>
    <div v-else-if="!overview" class="p-12 text-center text-gray-500">暂无数据</div>
    <div v-else class="p-6">
      <div class="surface-dark-card rounded-xl p-5">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-semibold text-gray-900">知识点掌握情况</h3>
          <span v-if="weakKnowledgeCount > 0" class="text-sm text-amber-600">
            {{ weakKnowledgeCount }} 个薄弱点（&lt;60%）
          </span>
        </div>
        <div v-if="overview.knowledge_points.length === 0" class="text-sm text-gray-500 py-8 text-center">
          暂无做题记录
        </div>
        <KnowledgeBarChart v-if="overview.knowledge_points.length > 0" :items="overview.knowledge_points" />
        <div v-if="weakPoints.length > 0" class="mt-4 pt-4 border-t border-gray-100">
          <p class="text-xs text-gray-500 mb-2">点击薄弱知识点查看关联错题</p>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="item in weakPoints"
              :key="item.name"
              class="surface-dark-inset px-3 py-1.5 text-sm rounded-lg text-amber-400 border border-amber-500/20 hover:border-amber-500/35"
              @click="drillToWrongBook(item.name)"
            >
              {{ item.name }}（{{ item.mastery_rate }}%）
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const KnowledgeBarChart = defineAsyncComponent(
  () => import('@/components/charts/KnowledgeBarChart.vue'),
)
import { useParentContext } from '@/composables/useParentContext'
import { trackEvent } from '@/utils/tracker'

const router = useRouter()
const { overview, loading, weakKnowledgeCount } = useParentContext()

const weakPoints = computed(
  () => overview.value?.knowledge_points.filter((item) => item.mastery_rate < 60) ?? [],
)

const drillToWrongBook = (name: string) => {
  trackEvent({
    event_name: 'parent_weak_point_click',
    page: '/parent/weak-points',
    module: 'parent',
    detail: name,
  })
  void router.push({ path: '/parent/wrong-book', query: { knowledge: name } })
}

onMounted(() => {
  trackEvent({ event_name: 'parent_weak_points_view', page: '/parent/weak-points', module: 'parent' })
})
</script>

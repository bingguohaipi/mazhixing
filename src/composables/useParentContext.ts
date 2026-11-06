import { computed, ref } from 'vue'
import { parentApi } from '@/api/parent'
import { toast } from '@/utils/toast'
import type { ParentChildBrief, ParentPeriod, ParentStudentOverview } from '@/types/parent'

const children = ref<ParentChildBrief[]>([])
const selectedStudentId = ref<number | null>(null)
const period = ref<ParentPeriod>('7')
const overview = ref<ParentStudentOverview | null>(null)
const loading = ref(true)
const initialized = ref(false)

/** 退出登录或切换账号时清空，避免仍显示上一用户的绑定状态 */
export function resetParentContext(): void {
  children.value = []
  selectedStudentId.value = null
  overview.value = null
  period.value = '7'
  loading.value = true
  initialized.value = false
}

export function useParentContext() {
  const weakKnowledgeCount = computed(
    () => overview.value?.knowledge_points.filter((item) => item.mastery_rate < 60).length ?? 0,
  )

  const maxTrendCount = computed(() =>
    Math.max(...(overview.value?.learning_trend.map((item) => item.count) ?? [0]), 1),
  )

  const loadOverview = async () => {
    if (!selectedStudentId.value) return
    loading.value = true
    try {
      overview.value = await parentApi.getOverview(selectedStudentId.value, period.value)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : '加载学情失败')
    } finally {
      loading.value = false
    }
  }

  const initParentContext = async () => {
    loading.value = true
    try {
      const list = await parentApi.listChildren()
      children.value = list
      if (list.length > 0) {
        const stillSelected =
          selectedStudentId.value != null
          && list.some((item) => item.student_id === selectedStudentId.value)
        if (!stillSelected) {
          selectedStudentId.value = list[0].student_id
        }
        await loadOverview()
      } else {
        selectedStudentId.value = null
        overview.value = null
      }
      initialized.value = true
    } catch (err) {
      toast.error(err instanceof Error ? err.message : '加载失败')
    } finally {
      loading.value = false
    }
  }

  return {
    children,
    selectedStudentId,
    period,
    overview,
    loading,
    weakKnowledgeCount,
    maxTrendCount,
    loadOverview,
    initParentContext,
  }
}

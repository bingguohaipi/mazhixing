<template>
  <div class="p-6 max-w-7xl mx-auto space-y-4">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-lg font-semibold text-gray-900">公共题库管理</h1>
        <p class="text-xs text-gray-500 mt-1">
          增删改查公共题目；保存后学生/教师端按题目组展示最高版本。历史版本可删除，最新版请用「下架」。
        </p>
      </div>
      <div class="flex flex-wrap gap-2">
        <button
          type="button"
          class="px-3 py-1.5 text-sm rounded-lg border border-gray-300 hover:bg-gray-50"
          @click="showImport = true"
        >
          批量导入
        </button>
        <button
          type="button"
          class="px-3 py-1.5 text-sm rounded-lg bg-indigo-600 text-white hover:bg-indigo-700"
          @click="openCreate"
        >
          新建题目
        </button>
      </div>
    </div>

    <ListQueryToolbar
      v-model:keyword="keyword"
      placeholder="搜索题号或标题"
      :filter-active="activeFilterCount > 0"
      filter-aria-label="筛选题目"
      @toggle-filter="toggleFilter"
    >
      <template #filter>
        <AdminPublicProblemFilterPopover
          :open="filterOpen"
          :difficulty="draftDifficulty"
          :status="draftStatus"
          @update:difficulty="draftDifficulty = $event"
          @update:status="draftStatus = $event"
          @apply="onFilterApply"
          @reset="onFilterReset"
        />
      </template>
    </ListQueryToolbar>

    <div v-if="loading" class="text-center py-12 text-gray-500">加载中...</div>
    <div v-else-if="items.length === 0" class="text-center py-12 text-gray-500">
      {{ hasListQuery ? PROBLEM_FILTER_EMPTY_MESSAGE : '暂无题目' }}
    </div>
    <div v-else class="bg-white border border-gray-100 rounded-xl overflow-x-auto">
      <table class="w-full text-sm min-w-[960px]">
        <thead class="bg-gray-50 text-left text-gray-600">
          <tr>
            <th class="px-4 py-3">ID</th>
            <th class="px-4 py-3">题目组 / 版本</th>
            <th class="px-4 py-3">标题</th>
            <th class="px-4 py-3">难度</th>
            <th class="px-4 py-3">状态</th>
            <th class="px-4 py-3">用例</th>
            <th class="px-4 py-3 w-56">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in items" :key="p.id" class="border-t border-gray-50 align-middle">
            <td class="px-4 py-3 text-gray-500">#{{ p.id }}</td>
            <td class="px-4 py-3 text-gray-600">
              组 {{ p.public_group_id }} · v{{ p.version }}
              <span v-if="isLatestVersion(p)" class="text-xs text-indigo-600 ml-1">当前</span>
            </td>
            <td class="px-4 py-3 font-medium text-gray-900">{{ p.title }}</td>
            <td class="px-4 py-3">{{ p.difficulty }}</td>
            <td class="px-4 py-3">
              <span class="text-xs px-2 py-0.5 rounded" :class="statusClass(p.publish_status)">
                {{ statusLabel(p.publish_status) }}
              </span>
            </td>
            <td class="px-4 py-3 text-gray-500">{{ p.test_case_count }}</td>
            <td class="px-4 py-3">
              <div class="flex flex-wrap gap-x-2 gap-y-1 text-xs">
                <button type="button" class="text-indigo-600 hover:underline" @click="viewDetail(p.id)">查看</button>
                <button type="button" class="text-indigo-600 hover:underline" @click="edit(p.id)">编辑</button>
                <button type="button" class="text-indigo-600 hover:underline" @click="createVersion(p.id)">新版本</button>
                <button
                  v-if="p.publish_status !== 'published'"
                  type="button"
                  class="text-green-600 hover:underline"
                  @click="publish(p.id)"
                >
                  上架
                </button>
                <button
                  v-if="p.publish_status === 'published'"
                  type="button"
                  class="text-amber-600 hover:underline"
                  @click="archive(p.id)"
                >
                  下架
                </button>
                <button type="button" class="text-red-600 hover:underline" @click="removeVersion(p)">
                  删除
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="total > pageSize" class="flex items-center justify-between text-sm text-gray-500">
      <span>共 {{ total }} 条</span>
      <div class="flex items-center gap-2">
        <button
          type="button"
          class="px-2 py-1 border rounded disabled:opacity-40"
          :disabled="page <= 1"
          @click="load(page - 1)"
        >
          上一页
        </button>
        <span>第 {{ page }} / {{ totalPages }} 页</span>
        <button
          type="button"
          class="px-2 py-1 border rounded disabled:opacity-40"
          :disabled="page >= totalPages"
          @click="load(page + 1)"
        >
          下一页
        </button>
      </div>
    </div>

    <ProblemFormModal
      v-if="showForm"
      :problem="editing"
      :on-save="handleSave"
      @close="showForm = false"
      @success="onFormSuccess"
    />

    <ProblemImportModal
      v-if="showImport"
      :import-fn="adminApi.importPublicProblems"
      @close="showImport = false"
      @success="onImportSuccess"
    />

    <div v-if="viewing" class="modal-mask" @click.self="viewing = null">
      <div class="modal-box flex flex-col" style="width: 640px; max-height: 85vh;">
        <h3 class="modal-title">#{{ viewing.id }} {{ viewing.title }}</h3>
        <p class="modal-sub">难度 {{ viewing.difficulty }} · {{ viewing.languages?.join(' / ') || viewing.language }}</p>
        <div class="overflow-y-auto flex-1 min-h-0 space-y-3 text-sm text-gray-300">
          <section>
            <h4 class="text-xs text-gray-500 mb-1">题目描述</h4>
            <p class="whitespace-pre-wrap">{{ viewing.description }}</p>
          </section>
          <section v-if="viewing.sample_input || viewing.sample_output">
            <h4 class="text-xs text-gray-500 mb-1">样例</h4>
            <pre class="text-xs bg-black/30 p-2 rounded whitespace-pre-wrap">{{ viewing.sample_input || '(空)' }}</pre>
            <pre class="text-xs bg-black/30 p-2 rounded whitespace-pre-wrap mt-1">{{ viewing.sample_output || '(空)' }}</pre>
          </section>
          <section>
            <h4 class="text-xs text-gray-500 mb-1">测试用例（{{ viewing.test_cases?.length ?? 0 }}）</h4>
            <p class="text-xs text-gray-500">完整编辑请点「编辑」</p>
          </section>
        </div>
        <div class="modal-actions mt-4 shrink-0">
          <button type="button" class="modal-btn-confirm w-full" @click="viewing = null">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { adminApi } from '@/api/admin'
import AdminPublicProblemFilterPopover from '@/components/admin/AdminPublicProblemFilterPopover.vue'
import ListQueryToolbar from '@/components/ListQueryToolbar.vue'
import ProblemFormModal from '@/components/ProblemFormModal.vue'
import ProblemImportModal from '@/components/ProblemImportModal.vue'
import { useDebouncedWatch } from '@/composables/useDebouncedWatch'
import { useListFilterPanel } from '@/composables/useListFilterPanel'
import type { PublicProblemListItem } from '@/types/admin'
import type { ProblemCreatePayload, ProblemDetail } from '@/types/problem'
import {
  hasProblemCatalogQuery,
  PROBLEM_FILTER_EMPTY_MESSAGE,
} from '@/constants/problem-catalog'
import { toast } from '@/utils/toast'

const items = ref<PublicProblemListItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const keyword = ref('')
const statusFilter = ref('')
const difficultyFilter = ref('')
const draftStatus = ref('')
const draftDifficulty = ref('')
const { filterOpen, toggleFilter, closeFilter } = useListFilterPanel()
const loading = ref(false)

const activeFilterCount = computed(() => {
  let n = 0
  if (statusFilter.value) n += 1
  if (difficultyFilter.value) n += 1
  return n
})

const showForm = ref(false)
const showImport = ref(false)
const editing = ref<ProblemDetail | null>(null)
const editingId = ref<number | null>(null)
const viewing = ref<ProblemDetail | null>(null)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

const hasListQuery = computed(() =>
  hasProblemCatalogQuery({
    keyword: keyword.value,
    statusFilter: statusFilter.value,
    difficulty: difficultyFilter.value,
  })
)

const onFilterApply = () => {
  statusFilter.value = draftStatus.value
  difficultyFilter.value = draftDifficulty.value
  closeFilter()
  void load(1)
}

const onFilterReset = () => {
  draftStatus.value = ''
  draftDifficulty.value = ''
  statusFilter.value = ''
  difficultyFilter.value = ''
  closeFilter()
  void load(1)
}

const maxVersionByGroup = computed(() => {
  const map = new Map<number, number>()
  for (const p of items.value) {
    map.set(p.public_group_id, Math.max(map.get(p.public_group_id) ?? 0, p.version))
  }
  return map
})

const isLatestVersion = (p: PublicProblemListItem) => {
  const max = maxVersionByGroup.value.get(p.public_group_id) ?? p.version
  return p.version >= max
}

const statusLabel = (status: string) => {
  if (status === 'published') return '已上架'
  if (status === 'archived') return '已下架'
  if (status === 'draft') return '草稿'
  return status
}

const statusClass = (status: string) => {
  if (status === 'published') return 'bg-green-100 text-green-700'
  if (status === 'archived') return 'bg-gray-100 text-gray-600'
  return 'bg-amber-100 text-amber-800'
}

const load = async (targetPage = page.value) => {
  loading.value = true
  try {
    const data = await adminApi.listPublicProblems({
      page: targetPage,
      page_size: pageSize,
      keyword: keyword.value.trim() || undefined,
      status: statusFilter.value || undefined,
      difficulty: difficultyFilter.value || undefined,
    })
    items.value = data.items
    total.value = data.total
    page.value = data.page
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '加载失败')
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editing.value = null
  editingId.value = null
  showForm.value = true
}

const edit = async (id: number) => {
  try {
    editing.value = await adminApi.getPublicProblem(id)
    editingId.value = id
    showForm.value = true
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '加载失败')
  }
}

const viewDetail = async (id: number) => {
  try {
    viewing.value = await adminApi.getPublicProblem(id)
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '加载失败')
  }
}

const handleSave = async (payload: ProblemCreatePayload, isEdit: boolean, problemId?: number) => {
  if (isEdit && problemId) {
    return adminApi.updatePublicProblem(problemId, payload)
  }
  return adminApi.createPublicProblem(payload)
}

const onFormSuccess = async () => {
  showForm.value = false
  await load(page.value)
  toast.success('题目已保存')
}

const onImportSuccess = async () => {
  showImport.value = false
  await load(1)
  toast.success('导入完成')
}

const publish = async (id: number) => {
  try {
    await adminApi.publishPublicProblem(id)
    toast.success('已上架')
    await load(page.value)
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '操作失败')
  }
}

const archive = async (id: number) => {
  if (!confirm('确定下架该版本？学生端将不再展示（若仍有更高版本则不受影响）。')) return
  try {
    await adminApi.archivePublicProblem(id)
    toast.success('已下架')
    await load(page.value)
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '操作失败')
  }
}

const createVersion = async (id: number) => {
  try {
    const detail = await adminApi.newVersionPublicProblem(id)
    toast.success(`已创建 v${detail.version ?? ''}，请编辑后保存`)
    await load(1)
    editing.value = detail
    editingId.value = detail.id
    showForm.value = true
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '创建失败')
  }
}

const removeVersion = async (p: PublicProblemListItem) => {
  if (!confirm(`确定删除「${p.title}」v${p.version}（#${p.id}）？不可恢复。`)) return
  try {
    await adminApi.deletePublicProblemVersion(p.id)
    toast.success('已删除')
    await load(page.value)
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '删除失败')
  }
}

useDebouncedWatch(keyword, () => {
  void load(1)
})

onMounted(() => load(1))
</script>

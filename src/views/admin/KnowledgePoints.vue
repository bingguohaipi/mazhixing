<template>
  <div class="p-6 max-w-6xl mx-auto space-y-6">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <div class="flex flex-wrap items-center gap-3">
          <h1 class="text-lg font-semibold text-gray-900">知识点管理</h1>
          <button
            type="button"
            class="px-3 py-1.5 text-sm rounded-lg bg-indigo-600 text-white hover:bg-indigo-700"
            @click="openCreate"
          >
            新增知识点
          </button>
        </div>
        <p class="text-xs text-gray-500 mt-1">
          维护题库标签与专题说明；建题时只能从本列表选择。删除前需确保无题目引用。
        </p>
      </div>
    </div>

    <ListQueryToolbar
      v-model:keyword="keyword"
      v-model:sort-value="sortValue"
      :sort-options="sortOptions"
      placeholder="搜索名称 / 简介…"
    />

    <div v-if="loading" class="text-center py-12 text-gray-500">加载中...</div>
    <div v-else-if="items.length === 0" class="text-center py-12 text-gray-500">暂无知识点</div>
    <div v-else class="bg-white border border-gray-100 rounded-xl overflow-x-auto">
      <table class="w-full text-sm min-w-[720px]">
        <thead class="bg-gray-50 text-left text-gray-600">
          <tr>
            <th class="px-4 py-3 w-16">排序</th>
            <th class="px-4 py-3">名称</th>
            <th class="px-4 py-3">简介</th>
            <th class="px-4 py-3 w-24">题目数</th>
            <th class="px-4 py-3 w-36">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in items" :key="row.id" class="border-t border-gray-50 align-top">
            <td class="px-4 py-3 text-gray-500">{{ row.sort_order }}</td>
            <td class="px-4 py-3 font-medium text-gray-900">{{ row.name }}</td>
            <td class="px-4 py-3 text-gray-600 max-w-md truncate" :title="row.summary">{{ row.summary || '—' }}</td>
            <td class="px-4 py-3 text-gray-500">{{ row.problem_count }}</td>
            <td class="px-4 py-3">
              <div class="flex gap-2">
                <button type="button" class="text-indigo-600 hover:underline text-xs" @click="openEdit(row)">
                  编辑
                </button>
                <button
                  type="button"
                  class="text-red-600 hover:underline text-xs disabled:opacity-40"
                  :disabled="row.name === '未分类' || deleting === row.id"
                  @click="confirmDelete(row)"
                >
                  {{ deleting === row.id ? '删除中…' : '删除' }}
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div
      v-if="showModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      @click.self="closeModal"
    >
      <div class="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto p-6 space-y-4">
        <h2 class="text-base font-semibold text-gray-900">{{ editingId ? '编辑知识点' : '新增知识点' }}</h2>
        <div class="space-y-3">
          <div>
            <label class="block text-xs text-gray-500 mb-1">名称</label>
            <input
              v-model="form.name"
              type="text"
              maxlength="64"
              class="w-full input-light-bg border border-gray-200 rounded-lg px-3 py-2 text-sm"
              :disabled="!!editingId && form.name === '未分类'"
            />
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">简介（列表 / 下拉展示）</label>
            <input
              v-model="form.summary"
              type="text"
              maxlength="512"
              class="w-full input-light-bg border border-gray-200 rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">排序（越小越靠前）</label>
            <input
              v-model.number="form.sort_order"
              type="number"
              min="0"
              max="9999"
              class="w-full input-light-bg border border-gray-200 rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">详细说明（Markdown，学生端专题抽屉）</label>
            <textarea
              v-model="form.content_markdown"
              rows="10"
              class="w-full input-light-bg border border-gray-200 rounded-lg px-3 py-2 text-sm font-mono text-xs"
              placeholder="## 描述&#10;…"
            />
          </div>
        </div>
        <div class="flex justify-end gap-2 pt-2">
          <button type="button" class="px-4 py-2 text-sm rounded-lg border border-gray-200" @click="closeModal">
            取消
          </button>
          <button
            type="button"
            class="px-4 py-2 text-sm rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
            :disabled="submitting"
            @click="submitForm"
          >
            {{ submitting ? '保存中…' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useDebouncedWatch } from '@/composables/useDebouncedWatch'
import { adminApi } from '@/api/admin'
import ListQueryToolbar from '@/components/ListQueryToolbar.vue'
import type { AdminKnowledgePointItem } from '@/types/knowledge-admin'
import { toast } from '@/utils/toast'

const loading = ref(true)
const submitting = ref(false)
const deleting = ref<number | null>(null)
const keyword = ref('')
const sortValue = ref('sort_order:asc')
const sortOptions = [
  { value: 'sort_order:asc', label: '默认排序' },
  { value: 'problem_count:asc', label: '题目数 ↑' },
  { value: 'problem_count:desc', label: '题目数 ↓' },
]
const items = ref<AdminKnowledgePointItem[]>([])
const showModal = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({
  name: '',
  summary: '',
  content_markdown: '',
  sort_order: 100,
})

const listParams = computed(() => {
  const [sortBy, sortOrder] = sortValue.value.split(':') as ['sort_order' | 'problem_count', 'asc' | 'desc']
  return {
    keyword: keyword.value.trim() || undefined,
    sort_by: sortBy,
    sort_order: sortOrder,
  }
})

async function load() {
  loading.value = true
  try {
    const data = await adminApi.listKnowledgePoints(listParams.value)
    items.value = data.items
  } catch {
    toast.error('加载知识点失败')
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.name = ''
  form.summary = ''
  form.content_markdown = ''
  form.sort_order = 100
}

function openCreate() {
  editingId.value = null
  resetForm()
  showModal.value = true
}

function openEdit(row: AdminKnowledgePointItem) {
  editingId.value = row.id
  form.name = row.name
  form.summary = row.summary
  form.content_markdown = row.content_markdown
  form.sort_order = row.sort_order
  showModal.value = true
}

function closeModal() {
  showModal.value = false
}

async function submitForm() {
  const name = form.name.trim()
  if (!name) {
    toast.error('请填写知识点名称')
    return
  }
  submitting.value = true
  try {
    if (editingId.value) {
      await adminApi.updateKnowledgePoint(editingId.value, {
        name,
        summary: form.summary.trim(),
        content_markdown: form.content_markdown,
        sort_order: form.sort_order,
      })
      toast.success('已更新')
    } else {
      await adminApi.createKnowledgePoint({
        name,
        summary: form.summary.trim(),
        content_markdown: form.content_markdown,
        sort_order: form.sort_order,
      })
      toast.success('已创建')
    }
    closeModal()
    await load()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '保存失败'
    toast.error(msg)
  } finally {
    submitting.value = false
  }
}

async function confirmDelete(row: AdminKnowledgePointItem) {
  if (!window.confirm(`确定删除知识点「${row.name}」？`)) return
  deleting.value = row.id
  try {
    await adminApi.deleteKnowledgePoint(row.id)
    toast.success('已删除')
    await load()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '删除失败'
    toast.error(msg)
  } finally {
    deleting.value = null
  }
}

useDebouncedWatch(keyword, () => {
  void load()
})

watch(sortValue, () => {
  void load()
})

onMounted(() => {
  load()
})
</script>

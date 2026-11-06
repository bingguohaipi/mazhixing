<template>
  <div class="p-6 max-w-2xl mx-auto space-y-6">
    <div>
      <h1 class="text-lg font-semibold text-gray-900">积分明细</h1>
      <p class="text-2xl font-bold text-indigo-600 mt-2">🪙 {{ summary?.balance ?? '—' }}</p>
      <p class="text-xs text-gray-500">每题首次 AC +10 积分（上线后生效）</p>
    </div>

    <div v-if="loading" class="text-center py-12 text-gray-500">加载中...</div>
    <ul v-else class="bg-white border border-gray-100 rounded-xl divide-y divide-gray-50">
      <li v-if="items.length === 0" class="p-8 text-center text-gray-500 text-sm">还没有积分记录，快去题库首次通过题目吧</li>
      <li v-for="row in items" :key="row.id" class="px-4 py-3 flex justify-between gap-3 text-sm">
        <div>
          <span :class="row.delta > 0 ? 'text-green-600' : 'text-red-500'" class="font-semibold">
            {{ row.delta > 0 ? '+' : '' }}{{ row.delta }}
          </span>
          <span class="text-gray-700 ml-2">{{ row.ref_title || row.type }}</span>
        </div>
        <time class="text-gray-400 text-xs shrink-0">{{ formatTime(row.created_at) }}</time>
      </li>
    </ul>
    <button
      v-if="items.length < total"
      type="button"
      class="w-full py-2 text-sm text-indigo-600 border border-indigo-100 rounded-lg"
      @click="loadMore"
    >
      加载更多
    </button>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { petApi } from '@/api/pet'
import type { PointLedgerItem, StudentPointsSummary } from '@/types/pet'

const summary = ref<StudentPointsSummary | null>(null)
const items = ref<PointLedgerItem[]>([])
const total = ref(0)
const page = ref(1)
const loading = ref(true)

function formatTime(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

async function fetchPage(p: number, append: boolean) {
  const [s, ledger] = await Promise.all([petApi.getPoints(), petApi.getPointLedger(p, 20)])
  summary.value = s
  total.value = ledger.total
  items.value = append ? [...items.value, ...ledger.items] : ledger.items
}

async function loadMore() {
  page.value += 1
  await fetchPage(page.value, true)
}

onMounted(async () => {
  try {
    await fetchPage(1, false)
  } finally {
    loading.value = false
  }
})
</script>

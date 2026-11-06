<template>
  <div class="suggestion-page-shell flex min-h-full flex-col gap-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h1 class="text-xl font-semibold text-gray-100">建议中心</h1>
      <button
        type="button"
        class="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
        @click="showCompose = true"
      >
        发送建议
      </button>
    </div>

    <div v-if="auth.role !== 'admin'" class="flex gap-2 border-b border-gray-700 pb-2">
      <button
        type="button"
        class="px-3 py-1.5 text-sm rounded-lg"
        :class="tab === 'inbox' ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:bg-white/5'"
        @click="switchTab('inbox')"
      >
        收到的建议
      </button>
      <button
        type="button"
        class="px-3 py-1.5 text-sm rounded-lg"
        :class="tab === 'sent' ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:bg-white/5'"
        @click="switchTab('sent')"
      >
        我发出的
      </button>
    </div>

    <ListQueryToolbar
      v-model:keyword="searchKeyword"
      placeholder="搜索发送者"
      :filter-active="activeFilterCount > 0"
      filter-aria-label="筛选建议"
      @toggle-filter="toggleFilter"
    >
      <template #filter>
        <SuggestionFilterPopover
          :open="filterOpen"
          :processed="draftProcessed"
          @update:processed="draftProcessed = $event"
          @apply="onFilterApply"
          @reset="onFilterReset"
        />
      </template>
    </ListQueryToolbar>

    <div class="flex flex-col gap-3 min-h-0">
      <SuggestionListRow
        v-for="item in items"
        :key="item.id"
        :item="item"
        @open="openDetail"
      />
      <div v-if="!items.length" class="suggestion-card p-8 text-center text-gray-500">
        暂无建议
      </div>
    </div>

    <SuggestionModal v-if="showCompose" @close="showCompose = false" @success="onComposeSuccess" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import ListQueryToolbar from '@/components/ListQueryToolbar.vue'
import SuggestionFilterPopover from '@/components/suggestions/SuggestionFilterPopover.vue'
import SuggestionListRow from '@/components/suggestions/SuggestionListRow.vue'
import SuggestionModal from '@/components/SuggestionModal.vue'
import { useDebouncedWatch } from '@/composables/useDebouncedWatch'
import { useListFilterPanel } from '@/composables/useListFilterPanel'
import { adminApi } from '@/api/admin'
import { suggestionApi } from '@/api/suggestions'
import type { SuggestionItem, SuggestionListResponse } from '@/types/suggestion'
import { useAuthStore } from '@/stores/auth'
import { suggestionDetailPath } from '@/utils/suggestionDisplay'

const auth = useAuthStore()
const router = useRouter()
const items = ref<SuggestionItem[]>([])
const showCompose = ref(false)
const tab = ref<'inbox' | 'sent'>('inbox')

const searchKeyword = ref('')
const appliedProcessed = ref('')
const draftProcessed = ref('')
const { filterOpen, toggleFilter, closeFilter } = useListFilterPanel()

const activeFilterCount = computed(() => (appliedProcessed.value ? 1 : 0))

const listQueryParams = () => {
  const sender = searchKeyword.value.trim() || undefined
  let processed: boolean | undefined
  if (appliedProcessed.value === 'true') processed = true
  if (appliedProcessed.value === 'false') processed = false
  return { sender, processed }
}

const load = async () => {
  const params = listQueryParams()
  if (auth.role === 'admin') {
    const data = (await adminApi.listAllSuggestions({ page: 1, page_size: 50, ...params })) as SuggestionListResponse
    items.value = data.items
  } else if (tab.value === 'sent') {
    const data = await suggestionApi.sent(1, 50, params)
    items.value = data.items
  } else {
    const data = await suggestionApi.inbox(1, 50, params)
    items.value = data.items
  }
}

const openDetail = (id: number) => {
  router.push(suggestionDetailPath(auth.role, id))
}

const switchTab = (next: 'inbox' | 'sent') => {
  tab.value = next
  void load()
}

const onFilterApply = () => {
  appliedProcessed.value = draftProcessed.value
  closeFilter()
  void load()
}

const onFilterReset = () => {
  draftProcessed.value = ''
  appliedProcessed.value = ''
  closeFilter()
  void load()
}

const onComposeSuccess = async () => {
  if (auth.role !== 'admin') {
    tab.value = 'sent'
  }
  await load()
}

useDebouncedWatch(searchKeyword, () => {
  void load()
})

onMounted(load)
</script>

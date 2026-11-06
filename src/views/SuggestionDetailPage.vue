<template>
  <div class="suggestion-page-shell suggestion-detail flex min-h-full w-full flex-col">
    <header class="suggestion-detail__header">
      <button type="button" class="suggestion-detail__back" aria-label="返回" @click="goBack">‹</button>
      <h1 class="suggestion-detail__heading">留言详情</h1>
    </header>

    <div v-if="loading" class="p-8 text-center text-gray-500">加载中…</div>
    <div v-else-if="!item" class="p-8 text-center text-gray-500">建议不存在或无权查看</div>
    <template v-else>
      <div class="suggestion-detail__meta-bar">
        <span class="suggestion-detail__meta-icon" aria-hidden="true">⏳</span>
        <span class="suggestion-detail__ref">{{ refNo }}</span>
        <span :class="['suggestion-status', statusClass]">{{ statusText }}</span>
        <span class="suggestion-detail__meta-time">{{ headerTime }}</span>
      </div>

      <div class="suggestion-detail__thread">
        <section
          v-for="msg in threadMessages"
          :key="msg.key"
          class="suggestion-detail__message"
        >
          <p v-if="msg.kind === 'root'" class="suggestion-detail__message-title">{{ msg.title }}</p>
          <p v-else class="suggestion-detail__message-from">
            {{ msg.fromLabel }} · {{ msg.timeLabel }}
          </p>
          <p v-if="msg.content" class="suggestion-detail__message-body whitespace-pre-wrap">{{ msg.content }}</p>
          <SuggestionImageRow v-if="msg.image_urls.length" :urls="msg.image_urls" @preview="openPreview" />
        </section>
      </div>

      <div
        v-if="item.context_type === 'problem' && item.context_problem"
        class="suggestion-detail__context text-sm py-2 text-gray-400"
      >
        <span class="text-gray-500">关联题目：</span>
        <RouterLink
          v-if="problemLink"
          :to="problemLink"
          class="text-indigo-400 hover:underline"
        >
          {{ problemLabel }}
        </RouterLink>
        <span v-else>{{ problemLabel }}</span>
      </div>

      <div v-if="canManage && item.status !== 'resolved' && item.status !== 'closed'" class="suggestion-detail__actions py-2 flex gap-3">
        <button
          v-if="item.status === 'pending'"
          type="button"
          class="text-sm text-indigo-400"
          @click="mark('read')"
        >
          标为已读
        </button>
        <button type="button" class="text-sm text-green-500" @click="mark('resolved')">已处理</button>
      </div>

      <div v-if="showRatedResult" class="suggestion-detail__rated py-3">
        <p class="text-sm text-gray-400 mb-1">您的评分</p>
        <span class="suggestion-detail__rated-stars" aria-label="已提交评分">
          <span v-for="n in 5" :key="n" :class="{ 'is-on': n <= (item.satisfaction_rating ?? 0) }">★</span>
        </span>
        <p class="text-sm text-gray-300 mt-1">{{ item.satisfaction_rating }} 分</p>
      </div>

      <SuggestionRatingPanel
        v-if="canRate"
        :suggestion-id="item.id"
        @rated="load"
      />

      <div v-if="canReply" class="suggestion-detail__composer">
        <button
          v-if="!composerOpen"
          type="button"
          class="suggestion-detail__composer-trigger"
          @click="composerOpen = true"
        >
          回复
        </button>
        <div v-else class="suggestion-detail__composer-panel">
          <textarea
            v-model="replyDraft"
            rows="4"
            class="suggestion-detail__composer-input"
            placeholder="请输入"
          />
          <div class="suggestion-detail__composer-toolbar">
            <label class="suggestion-detail__attach" aria-label="上传图片">
              📎
              <input type="file" accept="image/*" class="hidden" @change="onPickImage" />
            </label>
            <div class="suggestion-detail__composer-actions">
              <button type="button" class="suggestion-detail__btn-cancel" @click="closeComposer">取消</button>
              <button
                type="button"
                class="suggestion-detail__btn-send"
                :disabled="replySubmitting"
                @click="submitReply"
              >
                {{ replySubmitting ? '发送中…' : '发送' }}
              </button>
            </div>
          </div>
          <div v-if="replyImages.length" class="flex gap-2 px-3 pb-2 flex-wrap">
            <img
              v-for="(url, idx) in replyImages"
              :key="idx"
              :src="mediaUrl(url)"
              class="w-12 h-12 object-cover rounded border border-gray-600 cursor-pointer"
              alt=""
              @click="openPreview(mediaUrl(url))"
            />
          </div>
        </div>
      </div>
    </template>

    <ImageLightbox :src="previewSrc" @close="previewSrc = null" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import ImageLightbox from '@/components/ImageLightbox.vue'
import SuggestionImageRow from '@/components/SuggestionImageRow.vue'
import SuggestionRatingPanel from '@/components/suggestions/SuggestionRatingPanel.vue'
import { suggestionApi } from '@/api/suggestions'
import type { SuggestionItem } from '@/types/suggestion'
import { useAuthStore } from '@/stores/auth'
import {
  formatSuggestionDetailTime,
  formatSuggestionRef,
  suggestionListPath,
  suggestionStatusClass,
  suggestionStatusLabel,
} from '@/utils/suggestionDisplay'
import { suggestionProblemLabel, suggestionProblemPath } from '@/utils/suggestionProblemLink'
import { toast } from '@/utils/toast'

interface ThreadMessage {
  key: string
  kind: 'root' | 'reply'
  title: string
  fromLabel?: string
  timeLabel?: string
  content: string
  image_urls: string[]
}

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const item = ref<SuggestionItem | null>(null)
const loading = ref(true)
const previewSrc = ref<string | null>(null)
const composerOpen = ref(false)
const replyDraft = ref('')
const replyImages = ref<string[]>([])
const replySubmitting = ref(false)

const suggestionId = computed(() => Number(route.params.id))

const refNo = computed(() =>
  item.value ? formatSuggestionRef(item.value.id, item.value.created_at) : '',
)
const headerTime = computed(() =>
  item.value ? formatSuggestionDetailTime(item.value.created_at) : '',
)
const statusText = computed(() => (item.value ? suggestionStatusLabel(item.value.status) : ''))
const statusClass = computed(() => (item.value ? suggestionStatusClass(item.value.status) : ''))

const problemLabel = computed(() =>
  item.value?.context_problem ? suggestionProblemLabel(item.value.context_problem) : '',
)
const problemLink = computed(() => {
  if (!item.value?.context_problem) return null
  return suggestionProblemPath(auth.role ?? undefined, item.value.context_problem)
})

const threadMessages = computed((): ThreadMessage[] => {
  const row = item.value
  if (!row) return []
  const list: ThreadMessage[] = [
    {
      key: `root-${row.id}`,
      kind: 'root',
      title: row.title,
      content: row.content,
      image_urls: row.image_urls,
    },
  ]
  for (const reply of row.replies ?? []) {
    list.push({
      key: `reply-${reply.id}`,
      kind: 'reply',
      title: '',
      fromLabel: reply.from_user_name,
      timeLabel: formatSuggestionDetailTime(reply.created_at),
      content: reply.content,
      image_urls: reply.image_urls,
    })
  }
  return list
})

const isClosedForReply = (status: string) => status === 'resolved' || status === 'closed'

const canReply = computed(() => {
  const row = item.value
  const uid = auth.user?.id
  if (!row || !uid) return false
  if (isClosedForReply(row.status)) return false
  if (auth.role === 'admin') return true
  return row.from_user_id === uid || row.to_user_id === uid
})

const canRate = computed(() => {
  const row = item.value
  const uid = auth.user?.id
  if (!row || !uid) return false
  return row.status === 'resolved' && row.from_user_id === uid && row.satisfaction_rating == null
})

const showRatedResult = computed(() => {
  const row = item.value
  const uid = auth.user?.id
  if (!row || !uid || row.satisfaction_rating == null) return false
  return row.from_user_id === uid
})

const canManage = computed(() => {
  const row = item.value
  if (!row) return false
  return auth.role === 'admin' || row.to_user_id === auth.user?.id
})

const load = async () => {
  loading.value = true
  try {
    item.value = await suggestionApi.get(suggestionId.value)
  } catch {
    item.value = null
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.push(suggestionListPath(auth.role))
}

const mark = async (status: string) => {
  if (!item.value) return
  await suggestionApi.updateStatus(item.value.id, status)
  if (status === 'resolved') {
    toast.success('已标记为已处理，已通知建议发送者')
  }
  await load()
}

const closeComposer = () => {
  composerOpen.value = false
  replyDraft.value = ''
  replyImages.value = []
}

const submitReply = async () => {
  if (!item.value) return
  const content = replyDraft.value.trim()
  const image_urls = replyImages.value
  if (!content && image_urls.length === 0) {
    toast.error('请填写回复文字或上传图片')
    return
  }
  replySubmitting.value = true
  try {
    await suggestionApi.createReply(item.value.id, { content, image_urls })
    toast.success('回复已发送')
    closeComposer()
    await load()
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '回复失败')
  } finally {
    replySubmitting.value = false
  }
}

const onPickImage = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  if (replyImages.value.length >= 3) {
    toast.error('最多 3 张图片')
    return
  }
  try {
    const url = await suggestionApi.uploadImage(file)
    replyImages.value = [...replyImages.value, url]
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '上传失败')
  }
}

const openPreview = (url: string) => {
  previewSrc.value = url
}

const mediaUrl = (url: string) => {
  if (url.startsWith('http')) return url
  const base = import.meta.env.VITE_API_BASE_URL?.replace(/\/api\/v1$/, '') || ''
  return `${base}${url}`
}

onMounted(load)
</script>

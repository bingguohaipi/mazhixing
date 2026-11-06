<template>
  <div class="surface-dark-card rounded-xl p-5">
    <h3 class="font-semibold text-gray-900 mb-4">老师通知</h3>
    <div v-if="loading" class="text-sm text-gray-500 py-4 text-center">加载中...</div>
    <div v-else-if="notices.length === 0" class="text-sm text-gray-500 py-6 text-center">
      暂无通知
    </div>
    <div v-else class="dashboard-panel-scroll dashboard-panel-scroll--notices space-y-3">
      <div
        v-for="notice in notices"
        :key="notice.id"
        class="notice-feed-card rounded-lg transition-colors"
        :class="
          notice.is_read
            ? 'surface-dark-card'
            : 'notice-feed-card--unread cursor-pointer'
        "
        role="button"
        :tabindex="notice.is_read ? -1 : 0"
        @click="onNoticeClick(notice)"
        @keydown.enter.prevent="onNoticeClick(notice)"
      >
        <div class="flex items-start justify-between gap-2 mb-1">
          <h4 class="text-sm font-medium text-gray-900 flex items-center gap-2">
            {{ notice.title }}
            <span v-if="!notice.is_read" class="text-[10px] font-normal px-1.5 py-0.5 rounded bg-blue-500/30 text-blue-200">
              未读
            </span>
          </h4>
          <span class="text-xs text-gray-400 shrink-0">{{ formatTime(notice.created_at) }}</span>
        </div>
        <p v-if="notice.is_read" class="text-sm text-gray-700 whitespace-pre-wrap">{{ notice.content }}</p>
        <p v-else class="text-xs text-blue-100/80">点击查看通知内容</p>
        <div class="text-xs text-gray-400 mt-2">
          {{ notice.teacher_name }}
          <template v-if="!isStudent"> · {{ notice.class_names.join('、') }}</template>
        </div>
      </div>
    </div>

    <div v-if="activeNotice" class="modal-mask" @click.self="closeModal">
      <div class="modal-box" style="width: 480px; max-width: calc(100vw - 32px);">
        <h3 class="modal-title">{{ activeNotice.title }}</h3>
        <p class="modal-sub">{{ formatTime(activeNotice.created_at) }} · {{ activeNotice.teacher_name }}</p>
        <div class="text-sm text-gray-200 whitespace-pre-wrap leading-relaxed max-h-[50vh] overflow-y-auto mb-5">
          {{ activeNotice.content }}
        </div>
        <div v-if="!isStudent" class="text-xs text-gray-500 mb-4">
          班级：{{ activeNotice.class_names.join('、') }}
        </div>
        <div class="modal-actions" style="justify-content: flex-end;">
          <button
            type="button"
            class="modal-btn-confirm"
            :disabled="confirming"
            @click="confirmRead"
          >
            {{ confirming ? '处理中…' : '确认' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { noticeApi } from '@/api/notices'
import { useAuthStore } from '@/stores/auth'
import type { NoticeFeedItem } from '@/types/notice'
import { toast } from '@/utils/toast'

const auth = useAuthStore()
const isStudent = computed(() => auth.user?.role === 'student')

const loading = ref(true)
const notices = ref<NoticeFeedItem[]>([])
const activeNotice = ref<NoticeFeedItem | null>(null)
const confirming = ref(false)

const formatTime = (iso: string) =>
  new Date(iso).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })

const loadNotices = async () => {
  loading.value = true
  try {
    notices.value = await noticeApi.feed()
  } catch {
    notices.value = []
  } finally {
    loading.value = false
  }
}

const onNoticeClick = (notice: NoticeFeedItem) => {
  if (notice.is_read) return
  activeNotice.value = notice
}

const closeModal = () => {
  if (confirming.value) return
  activeNotice.value = null
}

const confirmRead = async () => {
  const notice = activeNotice.value
  if (!notice || notice.is_read) {
    activeNotice.value = null
    return
  }
  confirming.value = true
  try {
    await noticeApi.markRead(notice.id)
    notice.is_read = true
    activeNotice.value = null
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '标记已读失败')
  } finally {
    confirming.value = false
  }
}

onMounted(loadNotices)

defineExpose({ reload: loadNotices })
</script>

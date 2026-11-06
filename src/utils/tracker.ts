import apiClient from '@/api/client'

export interface TrackEventPayload {
  event_name: string
  page?: string
  module?: string
  detail?: string
}

const queue: TrackEventPayload[] = []
let flushTimer: ReturnType<typeof setTimeout> | null = null

const flush = async () => {
  if (queue.length === 0) return
  const batch = queue.splice(0, 20)
  try {
    await apiClient.post('/events/track', { events: batch })
  } catch {
    /* 埋点失败不影响主流程 */
  }
}

export const trackEvent = (payload: TrackEventPayload): void => {
  queue.push(payload)
  if (flushTimer) clearTimeout(flushTimer)
  flushTimer = setTimeout(() => {
    flushTimer = null
    void flush()
  }, 800)
}

export const trackPageView = (page: string, module?: string): void => {
  trackEvent({ event_name: 'page_view', page, module })
}

export const trackError = (eventName: string, detail: string, page?: string): void => {
  trackEvent({ event_name: eventName, page, module: 'error', detail })
}

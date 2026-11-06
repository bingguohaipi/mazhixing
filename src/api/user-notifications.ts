import apiClient, { unwrapApi } from './client'
import type { ApiResponse } from '@/types/auth'

export interface UserNotificationItem {
  id: number
  event_key: string
  title: string
  body: string
  is_read: boolean
  created_at: string
  payload_json?: string | null
}

export const userNotificationApi = {
  async listUnread(eventKey?: string): Promise<UserNotificationItem[]> {
    const res = await apiClient.get<
      ApiResponse<{ items: UserNotificationItem[]; total: number; page: number; page_size: number }>
    >('/user-notifications', {
      params: { page: 1, page_size: 20, unread_only: true, event_key: eventKey },
    })
    return unwrapApi(res).items
  },

  async markRead(ids: number[]): Promise<void> {
    if (!ids.length) return
    await apiClient.post('/user-notifications/read', { ids, all: false })
  },
}

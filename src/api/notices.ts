import apiClient, { unwrapApi } from '@/api/client'
import type { ApiResponse } from '@/types/auth'
import type { NoticeCreatePayload, NoticeFeedItem, NoticeListItem } from '@/types/notice'

export const noticeApi = {
  async list(): Promise<NoticeListItem[]> {
    const res = await apiClient.get<ApiResponse<NoticeListItem[]>>('/notices')
    return unwrapApi(res)
  },

  async create(payload: NoticeCreatePayload): Promise<NoticeListItem> {
    const res = await apiClient.post<ApiResponse<NoticeListItem>>('/notices', payload)
    return unwrapApi(res)
  },

  async remove(noticeId: number): Promise<void> {
    const res = await apiClient.delete<ApiResponse<null>>(`/notices/${noticeId}`)
    unwrapApi(res)
  },

  async feed(): Promise<NoticeFeedItem[]> {
    const res = await apiClient.get<ApiResponse<NoticeFeedItem[]>>('/notices/feed')
    return unwrapApi(res)
  },

  async markRead(noticeId: number): Promise<void> {
    const res = await apiClient.post<ApiResponse<null>>('/notices/read', { notice_id: noticeId })
    unwrapApi(res)
  },
}

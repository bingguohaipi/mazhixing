import apiClient, { unwrapApi } from './client'
import type { ApiResponse } from '@/types/auth'
import type {
  SuggestionCreatePayload,
  SuggestionItem,
  SuggestionListResponse,
  SuggestionRecipient,
  SuggestionReplyItem,
  SuggestionRatingPayload,
  SuggestionReplyPayload,
} from '@/types/suggestion'

export const suggestionApi = {
  listRecipients(params?: { context_type?: string; context_id?: number }) {
    return apiClient
      .get<ApiResponse<SuggestionRecipient[]>>('/suggestions/recipients', { params })
      .then((res) => unwrapApi(res) ?? [])
  },
  create(payload: SuggestionCreatePayload) {
    return apiClient.post<ApiResponse<SuggestionItem>>('/suggestions', payload).then((res) => unwrapApi(res))
  },
  get(id: number) {
    return apiClient.get<ApiResponse<SuggestionItem>>(`/suggestions/${id}`).then((res) => unwrapApi(res))
  },
  inbox(page = 1, pageSize = 20, params?: { sender?: string; processed?: boolean }) {
    return apiClient
      .get<ApiResponse<SuggestionListResponse>>('/suggestions/inbox', {
        params: { page, page_size: pageSize, ...params },
      })
      .then((res) => unwrapApi(res))
  },
  sent(page = 1, pageSize = 20, params?: { sender?: string; processed?: boolean }) {
    return apiClient
      .get<ApiResponse<SuggestionListResponse>>('/suggestions/sent', {
        params: { page, page_size: pageSize, ...params },
      })
      .then((res) => unwrapApi(res))
  },
  unreadCount() {
    return apiClient.get<ApiResponse<{ count: number }>>('/suggestions/unread-count').then((res) => unwrapApi(res).count)
  },
  updateStatus(id: number, status: string) {
    return apiClient.patch<ApiResponse<SuggestionItem>>(`/suggestions/${id}/status`, { status }).then((res) => unwrapApi(res))
  },
  rate(id: number, payload: SuggestionRatingPayload) {
    return apiClient
      .post<ApiResponse<SuggestionItem>>(`/suggestions/${id}/rating`, payload)
      .then((res) => unwrapApi(res))
  },

  createReply(suggestionId: number, payload: SuggestionReplyPayload) {
    return apiClient
      .post<ApiResponse<SuggestionReplyItem>>(`/suggestions/${suggestionId}/replies`, payload)
      .then((res) => unwrapApi(res))
  },
  uploadImage(file: File) {
    const form = new FormData()
    form.append('file', file)
    return apiClient
      .post<ApiResponse<{ url: string }>>('/suggestions/upload-image', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then((res) => unwrapApi(res).url)
  },
}

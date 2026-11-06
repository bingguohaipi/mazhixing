export interface SuggestionRecipient {
  id: number
  role: string
  display_name: string
  account: string
}

export interface SuggestionProblemContext {
  id: number
  title: string
  scope: string
  private_no?: number | null
}

export interface SuggestionCreatePayload {
  to_user_id: number
  title?: string
  content: string
  context_type?: 'general' | 'problem'
  context_id?: number
  image_urls?: string[]
}

export interface SuggestionReplyItem {
  id: number
  suggestion_id: number
  from_user_id: number
  from_user_name: string
  from_user_role: string
  content: string
  image_urls: string[]
  created_at: string
}

export interface SuggestionReplyPayload {
  content?: string
  image_urls?: string[]
}

export interface SuggestionItem {
  id: number
  title: string
  from_user_id: number
  from_user_name: string
  from_user_role: string
  to_user_id: number
  to_user_name: string
  to_user_role: string
  context_type: string
  context_id: number | null
  context_problem?: SuggestionProblemContext | null
  content: string
  image_urls: string[]
  status: string
  satisfaction_rating: number | null
  created_at: string
  replies: SuggestionReplyItem[]
}

export interface SuggestionRatingPayload {
  score: number
}

export interface SuggestionListResponse {
  items: SuggestionItem[]
  total: number
  page: number
  page_size: number
}

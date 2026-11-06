export type WrongReviewStatus = 'pending' | 'reviewing' | 'mastered'
export type WrongSortBy = 'error_count' | 'last_error' | 'difficulty'

export interface WrongBookSummary {
  pending_count: number
  reviewing_count: number
  mastered_count: number
}

export interface WrongBookItem {
  problem_id: number
  title: string
  difficulty: string
  knowledge_point: string | null
  review_status: WrongReviewStatus
  error_count: number
  last_error_at: string
  last_submission_id: number
  last_status: string
  last_code: string
  ai_analysis: string | null
  error_reason: string | null
}

export interface WrongBookListResponse {
  summary: WrongBookSummary
  items: WrongBookItem[]
}

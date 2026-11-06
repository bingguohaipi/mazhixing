export type ParentPeriod = '7' | '30'

export interface ParentChildBrief {
  student_id: number
  display_name: string
  student_no: string | null
  class_names: string[]
}

export interface ParentKnowledgePointStat {
  name: string
  mastery_rate: number
}

export interface ParentTrendItem {
  date: string
  label: string
  count: number
}

export interface ParentWrongProblemItem {
  problem_id: number
  title: string
  knowledge_point: string | null
  wrong_count: number
}

export interface ParentHomeworkItem {
  homework_id: number
  title: string
  status: string
  progress: string
  end_time: string
  is_late_only: boolean
}

export interface ParentStudentOverview {
  student_id: number
  display_name: string
  student_no: string | null
  class_names: string[]
  period_days: number
  total_submissions: number
  accuracy: number
  completed_problems: number
  wrong_count: number
  knowledge_points: ParentKnowledgePointStat[]
  learning_trend: ParentTrendItem[]
  top_wrong_problems: ParentWrongProblemItem[]
  recent_homeworks: ParentHomeworkItem[]
}

export type WrongReviewStatus = 'pending' | 'reviewing' | 'mastered'
export type WrongSortBy = 'error_count' | 'last_error' | 'difficulty'

export interface ParentWrongBookSummary {
  pending_count: number
  reviewing_count: number
  mastered_count: number
}

export interface ParentWrongBookItem {
  problem_id: number
  title: string
  difficulty: string
  knowledge_point: string | null
  review_status: WrongReviewStatus
  error_count: number
  last_error_at: string
  last_status: string
  ai_analysis: string | null
  error_reason: string | null
}

export interface ParentWrongBookListResponse {
  summary: ParentWrongBookSummary
  items: ParentWrongBookItem[]
}

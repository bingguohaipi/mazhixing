export type AnalyticsPeriod = 'week' | 'month' | 'semester' | 'all'
export type SubmissionTrendRange = '7d' | '1m' | '3m' | '6m' | '1y' | '2y' | '3y'
export type TrendGranularity = 'day' | 'week' | 'month'
export type TrendChartType = 'bar' | 'line'

export interface RecentHomeworkBrief {
  id: number
  title: string
  class_names: string[]
  end_time: string
  status: string
  completion_rate: number
  submitted_count: number
  total_students: number
}

export interface TeacherDashboardOverview {
  class_count: number
  student_count: number
  problem_count: number
  active_homework_count: number
  week_submission_count: number
  week_pass_rate: number
  recent_homeworks: RecentHomeworkBrief[]
}

export interface KnowledgePointStat {
  name: string
  mastery_rate: number
  attempted_count: number
  ac_count: number
}

export interface DailyTrendItem {
  date: string
  label: string
  count: number
}

export interface SubmissionTrendResponse {
  range: SubmissionTrendRange
  granularity: TrendGranularity
  chart_type: TrendChartType
  items: DailyTrendItem[]
}

export interface TopWrongProblem {
  problem_id: number
  title: string
  knowledge_point: string | null
  wrong_count: number
}

export interface StudentSubmissionRow {
  student_id: number
  student_name: string
  homework_id: number | null
  homework_title: string | null
  problem_id: number
  problem_title: string
  status: string
  submitted_at: string
  is_late: boolean
}

export interface StudentSubmissionStatItem {
  student_name: string
  submission_count: number
  ac_count: number
  accuracy_rate: number
  problems_attempted: number
  last_submitted_at: string | null
}

export interface AttentionStudent {
  student_id: number
  student_name: string
  recent_scores: string
  weak_knowledge_points: string[]
  suggestion: string
}

export interface ClassAnalytics {
  class_id: number
  class_name: string
  period: AnalyticsPeriod
  completion_rate: number
  average_accuracy: number
  total_submissions: number
  late_submission_count: number
  student_count: number
  knowledge_points: KnowledgePointStat[]
  daily_trend: DailyTrendItem[]
  top_wrong_problems: TopWrongProblem[]
  student_submissions: StudentSubmissionRow[]
  late_submissions: StudentSubmissionRow[]
  student_submission_stats: StudentSubmissionStatItem[]
  late_submission_stats: StudentSubmissionStatItem[]
  attention_students: AttentionStudent[]
}

export interface AnalyticsQuery {
  class_id?: number
  homework_id?: number
  period?: AnalyticsPeriod
}

export interface WrongSummaryStudentBrief {
  student_id: number
  student_name: string
  real_name: string | null
  wrong_count: number
  last_status: string
  last_error_at: string
}

export interface ClassWrongProblemDetail {
  problem_id: number
  title: string
  knowledge_point: string | null
  wrong_count: number
  affected_student_count: number
  students: WrongSummaryStudentBrief[]
}

export interface ClassProblemWrongCodeItem {
  student_id: number
  student_name: string
  submission_id: number
  status: string
  language: string
  code: string
  submitted_at: string
}

export interface ClassProblemWrongCodesResponse {
  class_id: number
  problem_id: number
  problem_title: string
  items: ClassProblemWrongCodeItem[]
}

export interface ClassWrongSummary {
  class_id: number
  class_name: string
  period: AnalyticsPeriod
  total_wrong_submissions: number
  problem_count: number
  student_count: number
  problems: ClassWrongProblemDetail[]
}

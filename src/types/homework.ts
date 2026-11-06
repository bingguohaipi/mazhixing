export type HomeworkStatus = '未开始' | '进行中' | '已截止' | '已撤回'

export interface HomeworkListItem {
  id: number
  title: string
  status: HomeworkStatus
  class_ids: number[]
  class_names: string[]
  problem_count: number
  total_students: number
  submitted_count: number
  correct_count: number
  wrong_count: number
  progress_done?: number
  progress_total?: number
  late_submission_count?: number
  start_time: string
  end_time: string
  allow_late_submission: boolean
  created_at: string
}

export interface HomeworkClassBrief {
  id: number
  name: string
}

export interface HomeworkProblemBrief {
  id: number
  title: string
  language: string
  difficulty: string
}

export interface HomeworkDetail extends HomeworkListItem {
  description: string | null
  classes: HomeworkClassBrief[]
  problems: HomeworkProblemBrief[]
  student_ids: number[]
}

export interface HomeworkCreatePayload {
  title: string
  description?: string
  start_time: string
  end_time: string
  allow_late_submission: boolean
  class_ids: number[]
  problem_ids: number[]
  student_ids?: number[]
}

export type HomeworkUpdatePayload = Partial<HomeworkCreatePayload>

export interface HomeworkStudentProblemAttempt {
  problem_id: number
  problem_title: string
  status: string | null
  submission_id: number | null
  error_message: string | null
  is_late: boolean
}

export interface HomeworkStudentProgressRow {
  student_id: number
  display_name: string
  account: string
  student_no: string | null
  ac_count: number
  problem_count: number
  all_ac: boolean
  problems: HomeworkStudentProblemAttempt[]
}

export interface HomeworkSubmissionReport {
  homework_id: number
  homework_title: string
  problem_count: number
  problems: HomeworkProblemBrief[]
  all_ac_students: string[]
  students: HomeworkStudentProgressRow[]
}

export interface TeacherSubmissionDetail {
  id: number
  problem_id: number
  homework_id: number | null
  language: string
  status: string
  runtime_ms: number | null
  memory_kb: number | null
  is_late: boolean
  error_message: string | null
  compile_output: string | null
  ai_analysis: string | null
  ai_highlight_lines: number[]
  case_results: {
    case_index: number
    status: string
    is_sample: boolean
    actual_output: string | null
    runtime_ms: number | null
  }[]
  created_at: string
  points_awarded: number | null
  points_balance: number | null
  code: string
  student_display_name: string
  student_account: string
}

export interface StudentHomeworkItem {
  id: number
  title: string
  status: HomeworkStatus
  class_name: string
  problem_count: number
  start_time: string
  end_time: string
  allow_late_submission: boolean
  progress: string | null
  has_unread_update?: boolean
  content_updated_at?: string | null
}

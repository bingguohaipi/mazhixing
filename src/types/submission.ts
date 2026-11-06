export type SubmissionStatus = 'AC' | 'WA' | 'CE' | 'TLE' | 'RE' | 'PENDING'

export interface SubmissionCaseResult {
  case_index: number
  status: SubmissionStatus
  is_sample: boolean
  actual_output: string | null
  runtime_ms: number | null
}

export interface SubmissionDetail {
  id: number
  problem_id: number
  homework_id: number | null
  language: string
  status: SubmissionStatus
  runtime_ms: number | null
  memory_kb: number | null
  is_late: boolean
  error_message: string | null
  compile_output: string | null
  ai_analysis: string | null
  ai_highlight_lines?: number[]
  case_results: SubmissionCaseResult[]
  created_at: string
  points_awarded?: number | null
  points_balance?: number | null
}

export interface SubmissionListItem {
  id: number
  problem_id: number
  homework_id: number | null
  language: string
  status: SubmissionStatus
  runtime_ms: number | null
  is_late: boolean
  created_at: string
}

export interface SubmissionCreatePayload {
  problem_id: number
  homework_id?: number | null
  code: string
  language: 'Python' | 'C++'
}

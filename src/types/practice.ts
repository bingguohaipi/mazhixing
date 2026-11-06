import type { GespLevel, ProblemDifficulty, ProblemLanguage } from '@/types/problem'

export interface StudentTestCaseItem {
  id: number
  input_data: string | null
  expected_output: string | null
  is_sample: boolean
  sort_order: number
}

export type ProblemStatus = 'passed' | 'failed' | 'untried'

export interface PracticeProblemListItem {
  id: number
  title: string
  language: ProblemLanguage
  languages: ProblemLanguage[]
  difficulty: ProblemDifficulty
  gesp_level: GespLevel
  knowledge_point: string | null
  pass_rate: number
  submission_count: number
  my_status: ProblemStatus
  my_submission_count: number
  best_status: string | null
}

export interface PracticeProblemListResponse {
  items: PracticeProblemListItem[]
  total: number
  page: number
  page_size: number
}

export interface KnowledgePointTagItem {
  name: string
  problem_count: number
}

export interface KnowledgePointListResponse {
  items: KnowledgePointTagItem[]
  total_problems: number
  solved_count: number
}

export interface KnowledgePointDifficultyProgress {
  label: string
  total: number
  solved: number
  attempting: number
}

export interface KnowledgePointDetailResponse {
  name: string
  problem_count: number
  solved_count: number
  attempting_count: number
  description: string | null
  content_markdown: string | null
  difficulty_progress: KnowledgePointDifficultyProgress[]
  first_untried_problem_id: number | null
  first_problem_id: number | null
}

export type PracticeProblemSortBy = 'id' | 'difficulty'
export type PracticeProblemSortOrder = 'asc' | 'desc'

export interface KnowledgePointOptionItem {
  name: string
  summary: string
}

export interface PracticeProblemDetail {
  id: number
  title: string
  description: string
  image_urls?: string[]
  language: ProblemLanguage
  languages: ProblemLanguage[]
  difficulty: ProblemDifficulty
  gesp_level: GespLevel
  knowledge_point: string | null
  input_format: string | null
  output_format: string | null
  sample_input: string | null
  sample_output: string | null
  hint: string | null
  time_limit_ms: number
  memory_limit_mb: number
  test_cases: StudentTestCaseItem[]
  pass_rate: number
  submission_count: number
  my_best_status: string | null
  is_public_catalog?: boolean
}

export interface StudentHomeworkProblemItem {
  id: number
  title: string
  language: string
  difficulty: string
  best_status: string | null
  submission_count: number
}

export interface StudentHomeworkDetail {
  id: number
  title: string
  description: string | null
  status: string
  class_name: string
  start_time: string
  end_time: string
  allow_late_submission: boolean
  progress: string
  problems: StudentHomeworkProblemItem[]
  has_unread_update?: boolean
  update_notice?: string | null
}

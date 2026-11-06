export type ProblemLanguage = 'Python' | 'C++'
export type ProblemDifficulty = '入门' | '简单' | '中等' | '困难'
export type GespLevel = 'GESP1' | 'GESP2' | 'GESP3' | 'GESP4'

export interface TestCaseInput {
  input_data: string
  expected_output: string
  is_sample: boolean
  sort_order: number
}

export interface TestCaseItem extends TestCaseInput {
  id: number
}

export interface ProblemAcSolverItem {
  user_id: number
  display_name: string
  account: string
  student_no: string | null
  first_ac_at: string
}

export interface ProblemListItem {
  id: number
  /** 自有题库独立编号（仅教师私有题） */
  private_no?: number | null
  title: string
  language: ProblemLanguage
  languages: ProblemLanguage[]
  difficulty: ProblemDifficulty
  gesp_level: GespLevel
  knowledge_point: string | null
  knowledge_points: string[]
  test_case_count: number
  is_publishable: boolean
  pass_rate: number
  submission_count: number
  created_at: string
}

export interface ProblemDetail {
  id: number
  private_no?: number | null
  title: string
  description: string
  image_urls?: string[]
  language: ProblemLanguage
  languages: ProblemLanguage[]
  difficulty: ProblemDifficulty
  gesp_level: GespLevel
  knowledge_point: string | null
  knowledge_points: string[]
  input_format: string | null
  output_format: string | null
  sample_input: string | null
  sample_output: string | null
  reference_answer: string | null
  hint: string | null
  time_limit_ms: number
  memory_limit_mb: number
  test_cases: TestCaseItem[]
  is_publishable: boolean
  pass_rate: number
  submission_count: number
  created_at: string
  updated_at: string
}

export interface ProblemListResponse {
  items: ProblemListItem[]
  total: number
  page: number
  page_size: number
}

export interface ProblemCreatePayload {
  title: string
  description: string
  languages: ProblemLanguage[]
  difficulty: ProblemDifficulty
  gesp_level?: GespLevel
  knowledge_points: string[]
  input_format?: string
  output_format?: string
  sample_input?: string
  sample_output?: string
  reference_answer?: string
  hint?: string
  time_limit_ms: number
  memory_limit_mb: number
  test_cases: TestCaseInput[]
  image_urls?: string[]
}

export type ProblemUpdatePayload = Partial<Omit<ProblemCreatePayload, 'test_cases'>> & {
  test_cases?: TestCaseInput[]
}

export type ProblemCatalogSortBy = 'id' | 'difficulty'
export type ProblemCatalogSortOrder = 'asc' | 'desc'

export interface ProblemQuery {
  page?: number
  page_size?: number
  keyword?: string
  language?: ProblemLanguage | ''
  difficulty?: ProblemDifficulty | ''
  gesp_level?: GespLevel | ''
  knowledge_point?: string
  sort_by?: ProblemCatalogSortBy
  sort_order?: ProblemCatalogSortOrder
  /** 教师预览：仅列出本人已 AC 的题目 */
  my_passed?: boolean
}

export interface ProblemImportFailedRow {
  row: number
  title: string | null
  reason: string
}

export interface ProblemImportResult {
  success_count: number
  failed: ProblemImportFailedRow[]
  created_ids: number[]
}

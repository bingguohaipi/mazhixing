export interface LeaderboardScoreBreakdown {
  accuracy_rate: number
  accuracy_score: number
  avg_runtime_ms: number | null
  time_score: number
  total_score: number
}

export interface LeaderboardEntry {
  rank: number
  student_id: number
  display_name: string
  nickname?: string | null
  real_name?: string | null
  completed_problems: number
  accuracy_rate: number
  total_score: number
  is_me: boolean
}

export interface LeaderboardResponse {
  class_id: number
  class_name: string
  my_rank: number | null
  my_score: LeaderboardScoreBreakdown | null
  entries: LeaderboardEntry[]
  snapshot_date?: string | null
  refreshed_at?: string | null
  source?: 'snapshot' | 'live'
}

export type ArenaSessionStatus = 'in_progress' | 'submitted' | 'exited' | 'expired' | 'cancelled'
export type ArenaMyStatus = 'none' | 'in_progress' | 'pending_review' | 'rejected' | 'on_board'
export type ArenaReviewStatus = 'none' | 'pending' | 'approved' | 'rejected'

export interface ArenaSessionBrief {
  id: number
  problem_id: number
  language: 'Python' | 'C++'
  status: ArenaSessionStatus
  started_at: string
  expires_at: string
  submitted_at?: string | null
}

export interface ArenaProblemListItem {
  id: number
  title: string
  language: string
  languages?: string[]
  difficulty: string
  gesp_level: string
  knowledge_point: string | null
  champion_name: string | null
  champion_score: number | null
  participant_count: number
}

export interface ArenaProblemListResponse {
  items: ArenaProblemListItem[]
  total: number
  page: number
  page_size: number
}

export interface ArenaBoardEntry {
  rank: number
  user_id: number
  display_name: string
  student_no_suffix?: string | null
  arena_score: number
  duration_ms: number
  achieved_at: string
  is_me: boolean
}

export interface ArenaBoardResponse {
  problem_id: number
  language: string
  entries: ArenaBoardEntry[]
  my_entry: ArenaBoardEntry | null
  my_status: ArenaMyStatus
  total_participants: number
}

export interface ArenaGlobalLeaderboardEntry {
  rank: number
  user_id: number
  display_name: string
  student_no_suffix?: string | null
  problems_passed: number
  attempt_count: number
  ac_count: number
  accuracy_rate: number
  total_duration_ms: number
  composite_score: number
  is_me: boolean
}

export interface ArenaGlobalLeaderboardResponse {
  language: string
  entries: ArenaGlobalLeaderboardEntry[]
  my_entry: ArenaGlobalLeaderboardEntry | null
  total_participants: number
}

export interface ArenaOverviewResponse {
  active_session: ArenaSessionBrief | null
  unread_notifications: number
  hot_problems: ArenaProblemListItem[]
}

export interface ArenaResultBrief {
  review_status: ArenaReviewStatus
  arena_score: number | null
  duration_ms: number | null
  judge_status: string
}

export interface ArenaSubmitResponse {
  submission_id: number
  status: string
  arena_result: ArenaResultBrief | null
}

export interface ArenaNotificationItem {
  id: number
  event_key: string
  title: string
  body: string
  is_read: boolean
  created_at: string
}

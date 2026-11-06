import type { LeaderboardEntry } from '@/types/leaderboard'

export interface KnowledgeProgressItem {
  name: string
  mastery_rate: number
  status: string
}

export interface StudentDashboardOverview {
  completed_problems: number
  week_new_problems: number
  accuracy: number
  class_avg_accuracy: number
  wrong_pending_count: number
  class_rank: number | null
  class_student_count: number
  streak_days: number
  knowledge_progress: KnowledgeProgressItem[]
  leaderboard_preview: LeaderboardEntry[]
}

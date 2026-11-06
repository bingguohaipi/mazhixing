import type { SubmissionTrendRange } from '@/types/analytics'

export const SUBMISSION_TREND_RANGE_OPTIONS: ReadonlyArray<{
  value: SubmissionTrendRange
  label: string
}> = [
  { value: '7d', label: '近7天' },
  { value: '1m', label: '近1个月' },
  { value: '3m', label: '近3个月' },
  { value: '6m', label: '近6个月' },
  { value: '1y', label: '近1年' },
  { value: '2y', label: '近2年' },
  { value: '3y', label: '近3年' },
]

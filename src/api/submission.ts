import apiClient, { unwrapApi } from '@/api/client'
import type { AiAnalysisResponse } from '@/types/ai'
import type {
  SubmissionCreatePayload,
  SubmissionDetail,
  SubmissionListItem,
} from '@/types/submission'

const sleep = (ms: number): Promise<void> => new Promise((resolve) => setTimeout(resolve, ms))

const isRetryablePollError = (err: unknown): boolean => {
  if (!(err instanceof Error)) return false
  return (
    err.message.includes('网络连接异常')
    || err.message.includes('Network Error')
    || err.message.includes('timeout')
  )
}

export const submissionApi = {
  async submit(payload: SubmissionCreatePayload): Promise<SubmissionDetail> {
    const response = await apiClient.post('/submissions', payload, { timeout: 30000 })
    const result = unwrapApi<SubmissionDetail>(response)
    if (result.status === 'PENDING') {
      return pollSubmission(result.id)
    }
    return result
  },

  async poll(submissionId: number, maxAttempts = 30): Promise<SubmissionDetail> {
    return pollSubmission(submissionId, maxAttempts)
  },

  async list(problemId: number, homeworkId?: number | null): Promise<SubmissionListItem[]> {
    const response = await apiClient.get('/submissions', {
      params: { problem_id: problemId, homework_id: homeworkId ?? undefined },
    })
    return unwrapApi(response)
  },

  async get(submissionId: number): Promise<SubmissionDetail> {
    const response = await apiClient.get(`/submissions/${submissionId}`)
    return unwrapApi(response)
  },

  async analyzeAi(submissionId: number): Promise<AiAnalysisResponse> {
    const response = await apiClient.post(
      `/submissions/${submissionId}/ai-analysis`,
      {},
      { timeout: 20000 },
    )
    return unwrapApi(response)
  },
}

async function pollSubmission(submissionId: number, maxAttempts = 30): Promise<SubmissionDetail> {
  let networkRetries = 0
  const maxNetworkRetries = 8

  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    await sleep(1000)
    try {
      const detail = await submissionApi.get(submissionId)
      networkRetries = 0
      if (detail.status !== 'PENDING') {
        return detail
      }
    } catch (err) {
      if (isRetryablePollError(err) && networkRetries < maxNetworkRetries) {
        networkRetries += 1
        continue
      }
      throw err
    }
  }
  throw new Error('判题超时，请稍后刷新重试')
}

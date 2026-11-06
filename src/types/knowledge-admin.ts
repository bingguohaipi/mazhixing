export interface AdminKnowledgePointItem {
  id: number
  name: string
  summary: string
  content_markdown: string
  sort_order: number
  problem_count: number
}

export interface AdminKnowledgePointListResponse {
  items: AdminKnowledgePointItem[]
}

export interface AdminKnowledgePointCreatePayload {
  name: string
  summary?: string
  content_markdown?: string
  sort_order?: number
}

export interface AdminKnowledgePointUpdatePayload {
  name?: string
  summary?: string
  content_markdown?: string
  sort_order?: number
}

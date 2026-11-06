export interface NoticeListItem {
  id: number
  title: string
  content: string
  class_ids: number[]
  class_names: string[]
  created_at: string
}

export interface NoticeFeedItem {
  id: number
  title: string
  content: string
  class_names: string[]
  teacher_name: string
  created_at: string
  is_read: boolean
}

export interface NoticeCreatePayload {
  title: string
  content: string
  class_ids: number[]
}

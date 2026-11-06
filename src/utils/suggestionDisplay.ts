import { formatShanghaiDateTime, parseApiDateTime } from '@/utils/datetime'

/** 展示用编号，如 #20261104000004 */
export function formatSuggestionRef(id: number, createdAt: string): string {
  const date = parseApiDateTime(createdAt)
  let datePart = ''
  if (!Number.isNaN(date.getTime())) {
    const parts = new Intl.DateTimeFormat('en-CA', {
      timeZone: 'Asia/Shanghai',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).formatToParts(date)
    const y = parts.find((p) => p.type === 'year')?.value ?? ''
    const m = parts.find((p) => p.type === 'month')?.value ?? ''
    const d = parts.find((p) => p.type === 'day')?.value ?? ''
    datePart = `${y}${m}${d}`
  }
  const idPart = String(id).padStart(6, '0')
  return datePart ? `#${datePart}${idPart}` : `#${idPart}`
}

export function formatSuggestionListTime(iso: string): string {
  return formatShanghaiDateTime(iso, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })
}

export function formatSuggestionDetailTime(iso: string): string {
  return formatShanghaiDateTime(iso, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })
}

export function suggestionStatusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: '处理中',
    read: '处理中',
    resolved: '已处理',
    closed: '已关闭',
  }
  return map[status] ?? status
}

export function suggestionStatusClass(status: string): string {
  if (status === 'resolved') return 'suggestion-status--resolved'
  if (status === 'closed') return 'suggestion-status--closed'
  return 'suggestion-status--processing'
}

export function suggestionDetailPath(role: string | null | undefined, id: number): string {
  if (role === 'admin') return `/admin/suggestions/${id}`
  return `/suggestions/${id}`
}

export function suggestionListPath(role: string | null | undefined): string {
  if (role === 'admin') return '/admin/suggestions'
  return '/suggestions'
}

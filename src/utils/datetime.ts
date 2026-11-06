/** 后端时间为 UTC；无 Z 后缀的 ISO 字符串按 UTC 解析，展示为北京时间。 */
export function parseApiDateTime(iso: string): Date {
  const s = (iso || '').trim()
  if (!s) return new Date(Number.NaN)
  if (/[zZ]$/.test(s) || /[+-]\d{2}:\d{2}$/.test(s)) {
    return new Date(s)
  }
  return new Date(`${s.includes('T') ? s : `${s}T00:00:00`}Z`)
}

export function formatShanghaiDateTime(
  iso: string,
  options: Intl.DateTimeFormatOptions = {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  },
): string {
  const date = parseApiDateTime(iso)
  if (Number.isNaN(date.getTime())) return '-'
  return date.toLocaleString('zh-CN', { ...options, timeZone: 'Asia/Shanghai' })
}

export const CLASS_WEEKDAYS = [
  '周一',
  '周二',
  '周三',
  '周四',
  '周五',
  '周六',
  '周日',
] as const

export type ClassWeekday = (typeof CLASS_WEEKDAYS)[number]

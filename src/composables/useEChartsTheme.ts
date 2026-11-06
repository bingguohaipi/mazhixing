export const chartColors = {
  primary: '#1890FF',
  success: '#52C41A',
  warning: '#FAAD14',
  error: '#FF4D4F',
  neutral: '#8C8C8C',
  grid: '#F0F0F0',
  text: '#595959',
} as const

export const masteryColor = (rate: number): string => {
  if (rate >= 80) return chartColors.success
  if (rate >= 60) return chartColors.warning
  return chartColors.error
}

/** 自有题库展示编号（与公共题库全局 id 无关） */
export function formatPrivateProblemNo(privateNo: number | null | undefined): string {
  if (privateNo == null || privateNo < 1) return '—'
  return String(privateNo)
}

export function privateProblemLabel(
  privateNo: number | null | undefined,
  title: string,
): string {
  const no = formatPrivateProblemNo(privateNo)
  return no === '—' ? title : `#${no} ${title}`
}

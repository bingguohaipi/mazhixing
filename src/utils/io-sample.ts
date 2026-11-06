/** Show sample / test I/O in UI (handles legacy literal `\n` in DB). */
export function displayIoSample(text: string | null | undefined): string {
  if (text == null || text === '') return '-'
  return text.replace(/\\n/g, '\n')
}

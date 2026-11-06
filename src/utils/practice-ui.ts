import type { ProblemStatus } from '@/types/practice'

export function difficultyTextClass(difficulty: string): string {
  if (difficulty === '入门' || difficulty === '简单') return 'text-emerald-600'
  if (difficulty === '中等') return 'text-amber-600'
  return 'text-red-500'
}

export function statusIcon(status: ProblemStatus): string {
  if (status === 'passed') return '✓'
  if (status === 'failed') return '✗'
  return ''
}

export function statusIconClass(status: ProblemStatus): string {
  if (status === 'passed') return 'text-emerald-500 font-bold'
  if (status === 'failed') return 'text-red-400 font-bold'
  return 'text-transparent'
}

export function encodeTopicSlug(name: string): string {
  return encodeURIComponent(name)
}

export function decodeTopicSlug(slug: string): string {
  try {
    return decodeURIComponent(slug)
  } catch {
    return slug
  }
}

/** Legacy topic slugs merged into a canonical knowledge point name. */
export function resolveTopicName(name: string): string {
  const key = name.trim()
  if (key === '输出') return '输入输出'
  return key
}

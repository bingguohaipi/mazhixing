import type { UserRole } from '@/types/auth'
import type { SuggestionProblemContext } from '@/types/suggestion'

/** 建议关联题目的预览/做题页路径（按当前登录角色） */
export function suggestionProblemPath(
  role: UserRole | undefined,
  ctx: SuggestionProblemContext,
): string | null {
  if (!role) return null
  const id = ctx.id
  if (role === 'student') return `/student/coding/${id}`
  if (role === 'teacher') {
    return ctx.scope === 'private' ? `/teacher/coding/${id}` : `/teacher/coding/${id}`
  }
  if (role === 'admin' && ctx.scope === 'public') return `/admin/coding/${id}`
  return null
}

export function suggestionProblemLabel(ctx: SuggestionProblemContext): string {
  if (ctx.scope === 'private' && ctx.private_no != null) {
    return `#${ctx.private_no} ${ctx.title}`
  }
  return `#${ctx.id} ${ctx.title}`
}

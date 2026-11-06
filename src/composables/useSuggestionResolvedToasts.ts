import { userNotificationApi } from '@/api/user-notifications'
import { toast } from '@/utils/toast'

/** 进入应用时弹出「建议已处理」类未读通知，并标记已读 */
export async function flushSuggestionResolvedNotifications(): Promise<void> {
  try {
    const items = await userNotificationApi.listUnread('suggestion_resolved')
    if (!items.length) return
    for (const item of items) {
      toast.success(`${item.title}：${item.body}`)
    }
    await userNotificationApi.markRead(items.map((row) => row.id))
  } catch {
    /* 网络异常时不打断主流程 */
  }
}

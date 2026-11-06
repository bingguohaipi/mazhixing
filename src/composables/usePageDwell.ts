import { onUnmounted } from 'vue'
import { trackEvent } from '@/utils/tracker'

/** Report page dwell time on unmount (PRD analytics). */
export function usePageDwell(eventName: string, page: string, module: string, minSeconds = 3): void {
  const startedAt = Date.now()

  onUnmounted(() => {
    const dwellSeconds = Math.round((Date.now() - startedAt) / 1000)
    if (dwellSeconds >= minSeconds) {
      trackEvent({
        event_name: eventName,
        page,
        module,
        detail: `dwell_seconds=${dwellSeconds}`,
      })
    }
  })
}

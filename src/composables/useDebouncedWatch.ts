import { watch, type WatchSource } from 'vue'

const DEFAULT_DELAY_MS = 300

/** 监听源变化并在防抖后执行回调（不在首次挂载时触发）。 */
export function useDebouncedWatch<T>(
  source: WatchSource<T>,
  callback: (value: T, oldValue: T) => void | Promise<void>,
  delayMs = DEFAULT_DELAY_MS,
): void {
  let timer: ReturnType<typeof setTimeout> | null = null
  watch(source, (value, oldValue) => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      void callback(value, oldValue)
    }, delayMs)
  })
}

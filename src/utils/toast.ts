import { ref } from 'vue'

export type ToastType = 'success' | 'error' | 'info'

export interface ToastItem {
  id: number
  message: string
  type: ToastType
}

const toasts = ref<ToastItem[]>([])
let toastId = 0

const removeToast = (id: number) => {
  toasts.value = toasts.value.filter((item) => item.id !== id)
}

export const showToast = (message: string, type: ToastType = 'info', duration = 3000) => {
  const id = ++toastId
  toasts.value.push({ id, message, type })
  window.setTimeout(() => removeToast(id), duration)
}

export const toast = {
  success: (message: string) => showToast(message, 'success'),
  error: (message: string) => showToast(message, 'error'),
  info: (message: string) => showToast(message, 'info'),
}

export const useToastState = () => toasts

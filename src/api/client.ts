import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import type { ApiResponse } from '@/types/auth'
import { trackError } from '@/utils/tracker'

const TOKEN_KEY = 'mzx_access_token'
const REFRESH_KEY = 'mzx_refresh_token'

export const getAccessToken = (): string | null => localStorage.getItem(TOKEN_KEY)
export const getRefreshToken = (): string | null => localStorage.getItem(REFRESH_KEY)

export const setTokens = (accessToken: string, refreshToken: string): void => {
  localStorage.setItem(TOKEN_KEY, accessToken)
  localStorage.setItem(REFRESH_KEY, refreshToken)
}

export const clearTokens = (): void => {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let isRefreshing = false
let pendingRequests: Array<(token: string) => void> = []

const resolvePending = (token: string) => {
  pendingRequests.forEach((cb) => cb(token))
  pendingRequests = []
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiResponse<unknown>>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }
    const status = error.response?.status

    if (status === 401 && originalRequest && !originalRequest._retry && !originalRequest.url?.includes('/auth/login')) {
      const refreshToken = getRefreshToken()
      if (!refreshToken) {
        clearTokens()
        window.location.href = '/login'
        return Promise.reject(error)
      }

      if (isRefreshing) {
        return new Promise((resolve) => {
          pendingRequests.push((token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            resolve(apiClient(originalRequest))
          })
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const { data } = await axios.post<ApiResponse<{ access_token: string; refresh_token: string }>>(
          `${import.meta.env.VITE_API_BASE_URL || '/api/v1'}/auth/refresh`,
          { refresh_token: refreshToken },
        )
        if (data.code === 200 && data.data) {
          setTokens(data.data.access_token, data.data.refresh_token)
          resolvePending(data.data.access_token)
          originalRequest.headers.Authorization = `Bearer ${data.data.access_token}`
          return apiClient(originalRequest)
        }
      } catch {
        clearTokens()
        window.location.href = '/login'
      } finally {
        isRefreshing = false
      }
    }

    const responseData = error.response?.data as ApiResponse<unknown> & {
      detail?: string | { msg?: string }[]
    }
    let message = responseData?.message
    if (!message && typeof responseData?.detail === 'string') {
      message = responseData.detail === 'Not Found' ? '接口不存在或服务需更新，请刷新或联系管理员' : responseData.detail
    }
    if (!message && Array.isArray(responseData?.detail)) {
      const joined = responseData.detail.map((item) => item.msg).filter(Boolean).join('；')
      if (joined) message = joined
    }
    if (!message) {
      if (error.code === 'ECONNABORTED') {
        message = '请求超时，判题或网络较慢，请稍后刷新提交记录重试'
      } else if (error.code === 'ERR_NETWORK') {
        message = '无法连接后端，请确认已启动 API（默认 http://127.0.0.1:8001）'
      } else {
        message = '网络连接异常，请检查网络后重试'
      }
    }
    const isNetworkFailure = !error.response && error.code !== 'ERR_CANCELED'
    if (isNetworkFailure || (error.response?.status ?? 0) >= 500) {
      trackError('network_error', message, originalRequest?.url)
    }
    if (
      isNetworkFailure
      && !originalRequest?.url?.includes('/events/track')
      && !window.location.pathname.startsWith('/network-error')
      && !window.location.pathname.startsWith('/login')
    ) {
      const redirect = encodeURIComponent(window.location.pathname + window.location.search)
      window.location.href = `/network-error?redirect=${redirect}`
      return Promise.reject(new Error(message))
    }
    if (error.response?.status === 403) {
      trackError('access_denied', message, originalRequest?.url)
    }
    return Promise.reject(new Error(message))
  },
)

export default apiClient

export const unwrapApi = <T>(response: { data: ApiResponse<T> }): T => {
  const { code, message, data } = response.data
  if (code !== 200) {
    throw new Error(message)
  }
  return data as T
}

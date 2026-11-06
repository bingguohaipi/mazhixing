import apiClient, { unwrapApi } from '@/api/client'
import type {
  ApiResponse,
  ChangePasswordPayload,
  LoginPayload,
  LoginResponse,
  RegisterPayload,
  ResetPasswordPayload,
  SendCodePayload,
  UserInfo,
} from '@/types/auth'

export const authApi = {
  async login(payload: LoginPayload): Promise<LoginResponse> {
    const res = await apiClient.post<ApiResponse<LoginResponse>>('/auth/login', payload)
    return unwrapApi(res)
  },

  async register(payload: RegisterPayload): Promise<UserInfo> {
    const res = await apiClient.post<ApiResponse<UserInfo>>('/auth/register', payload)
    return unwrapApi(res)
  },

  async sendCode(payload: SendCodePayload): Promise<{ sent: boolean; dev_code?: string }> {
    const res = await apiClient.post<ApiResponse<{ sent: boolean; dev_code?: string }>>('/auth/send-code', payload)
    return unwrapApi(res)
  },

  async me(): Promise<UserInfo> {
    const res = await apiClient.get<ApiResponse<UserInfo>>('/auth/me')
    return unwrapApi(res)
  },

  async changePassword(payload: ChangePasswordPayload): Promise<void> {
    const res = await apiClient.post<ApiResponse<null>>('/auth/change-password', payload)
    unwrapApi(res)
  },

  async resetPassword(payload: ResetPasswordPayload): Promise<void> {
    const res = await apiClient.post<ApiResponse<null>>('/auth/reset-password', payload)
    unwrapApi(res)
  },
}

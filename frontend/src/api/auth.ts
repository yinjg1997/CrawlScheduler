import apiClient from './client'
import type { User } from '@/store/auth'

export interface LoginData {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

export const authApi = {
  login: (data: LoginData): Promise<TokenResponse> => {
    return apiClient.post('/auth/login', data)
  },

  getCurrentUser: (): Promise<User> => {
    return apiClient.get('/auth/me')
  },
}

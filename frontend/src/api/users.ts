import apiClient from './client'
import type { User } from '@/store/auth'

export interface UserCreate {
  username: string
  email: string
  password: string
}

export interface UserUpdate {
  email?: string
  is_active?: boolean
}

export interface UserChangePassword {
  old_password: string
  new_password: string
  confirm_password: string
}

export interface PaginatedUserResponse {
  items: User[]
  total: number
  skip: number
  limit: number
}

export const usersApi = {
  list: (params?: { skip?: number; limit?: number }): Promise<PaginatedUserResponse> => {
    return apiClient.get('/users/', { params })
  },

  create: (data: UserCreate): Promise<User> => {
    return apiClient.post('/users/', data)
  },

  get: (id: number): Promise<User> => {
    return apiClient.get(`/users/${id}`)
  },

  update: (id: number, data: UserUpdate): Promise<User> => {
    return apiClient.put(`/users/${id}`, data)
  },

  changePassword: (id: number, data: UserChangePassword): Promise<User> => {
    return apiClient.put(`/users/${id}/password`, data)
  },

  delete: (id: number): Promise<void> => {
    return apiClient.delete(`/users/${id}`)
  },
}

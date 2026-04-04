import api from './client'

export interface PythonEnvironment {
  id: number
  name: string
  description?: string
  path: string
  version?: string
  is_active: boolean
  is_default: boolean
  created_at: string
  updated_at: string
}

export interface PythonEnvironmentListItem {
  id: number
  name: string
  path: string
  version?: string
  type: 'user' | 'system' | 'conda'
  is_active: boolean
}

export interface PythonEnvironmentCreate {
  name: string
  description?: string
  path: string
  version?: string
  is_active: boolean
  is_default?: boolean
}

export interface PythonEnvironmentUpdate {
  name?: string
  description?: string
  path?: string
  version?: string
  is_active?: boolean
  is_default?: boolean
}

export const pythonEnvironmentsApi = {
  list: (params?: { skip?: number; limit?: number }) =>
    api.get<PythonEnvironment[]>('/python-environments/', { params }),

  get: (id: number) =>
    api.get<PythonEnvironment>(`/python-environments/${id}`),

  create: (data: PythonEnvironmentCreate) =>
    api.post<PythonEnvironment>('/python-environments/', data),

  update: (id: number, data: PythonEnvironmentUpdate) =>
    api.put<PythonEnvironment>(`/python-environments/${id}`, data),

  delete: (id: number) =>
    api.delete(`/python-environments/${id}`),

  getAllEnvironments: () =>
    api.get<PythonEnvironmentListItem[]>('/python-environments/all/environments')
}

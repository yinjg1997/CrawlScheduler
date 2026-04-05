import api from './client'

export interface Project {
  id: number
  name: string
  description?: string
  working_directory: string
  python_executable?: string
  is_active: boolean
  created_at: string
  updated_at: string
  crawler_count: number
}

export interface ProjectCreate {
  name: string
  description?: string
  working_directory: string
  python_executable?: string
  is_active?: boolean
}

export interface ProjectUpdate {
  name?: string
  description?: string
  working_directory?: string
  python_executable?: string
  is_active?: boolean
}

export interface PaginatedProjects {
  total: number
  items: Project[]
}

export const projectsApi = {
  list: (params?: { skip?: number; limit?: number }) =>
    api.get<PaginatedProjects>('/projects/', { params }),

  getActive: () =>
    api.get<Project[]>('/projects/active'),

  get: (id: number) =>
    api.get<Project>(`/projects/${id}`),

  create: (data: ProjectCreate) =>
    api.post<Project>('/projects/', data),

  update: (id: number, data: ProjectUpdate) =>
    api.put<Project>(`/projects/${id}`, data),

  delete: (id: number) =>
    api.delete(`/projects/${id}`)
}

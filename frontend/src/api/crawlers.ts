import api from './client'

export interface PythonEnvironment {
  name: string
  path: string
  version: string
  type: 'system' | 'conda'
  is_active?: boolean
}

export interface Crawler {
  id: number
  name: string
  description?: string
  command: string
  working_directory: string
  file_path?: string
  python_executable?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CrawlerCreate {
  name: string
  description?: string
  command: string
  working_directory: string
  file_path?: string
  python_executable?: string
  is_active: boolean
}

export interface CrawlerUpdate {
  name?: string
  description?: string
  command?: string
  working_directory?: string
  file_path?: string
  python_executable?: string
  is_active?: boolean
}

export interface PaginatedCrawlers {
  total: number
  items: Crawler[]
}

export const crawlersApi = {
  list: (params?: { skip?: number; limit?: number }) =>
    api.get<PaginatedCrawlers>('/crawlers/', { params }),

  get: (id: number) =>
    api.get<Crawler>(`/crawlers/${id}`),

  create: (data: CrawlerCreate) =>
    api.post<Crawler>('/crawlers/', data),

  update: (id: number, data: CrawlerUpdate) =>
    api.put<Crawler>(`/crawlers/${id}`, data),

  delete: (id: number) =>
    api.delete(`/crawlers/${id}`),

  execute: (id: number) =>
    api.post<{ task_id: number; message: string }>(`/crawlers/${id}/execute`),

  getPythonEnvironments: () =>
    api.get<{ environments: PythonEnvironment[] }>('/crawlers/python/environments')
}

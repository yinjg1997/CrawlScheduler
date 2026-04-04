import api from './client'

export interface TaskExecution {
  id: number
  crawler_id: number
  status: string
  started_at?: string
  finished_at?: string
  duration?: number
  exit_code?: number
  log_file_path?: string
  triggered_by: string
  schedule_id?: number
  error_message?: string
  created_at: string
  updated_at: string
  crawler?: {
    id: number
    name: string
    command: string
  }
  schedule?: {
    id: number
    name: string
  }
}

export interface TaskLogs {
  task_id: number
  logs: string[]
  offset: number
  limit: number
}

export interface PaginatedTasks {
  total: number
  items: TaskExecution[]
}

export const tasksApi = {
  list: (params?: {
    skip?: number;
    limit?: number;
    crawler_id?: number;
    status_filter?: string;
    search?: string;
    date_from?: string;
    date_to?: string
  }) =>
    api.get<PaginatedTasks>('/tasks/', { params }),

  get: (id: number) =>
    api.get<TaskExecution>(`/tasks/${id}`),

  getLogs: (id: number, params?: { offset?: number; limit?: number }) =>
    api.get<TaskLogs>(`/tasks/${id}/logs`, { params }),

  cancel: (id: number) =>
    api.post<{ message: string }>(`/tasks/${id}/cancel`),

  retry: (id: number) =>
    api.post<{ task_id: number; message: string }>(`/tasks/${id}/retry`),

  getStatus: (id: number) =>
    api.get<{ task_id: number; status: string; is_running: boolean }>(`/tasks/${id}/status`),

  getStatistics: (params?: { crawler_id?: number }) =>
    api.get<{ total: number; success: number; failed: number; running: number }>('/tasks/statistics', { params }),

  delete: (id: number) =>
    api.delete(`/tasks/${id}`),

  bulkDelete: (taskIds: number[]) =>
    api.delete('/tasks/', { data: { task_ids: taskIds } })
}

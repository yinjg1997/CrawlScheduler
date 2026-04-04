import api from './client'

export interface Schedule {
  id: number
  name: string
  crawler_id: number
  cron_expression: string
  is_active: boolean
  next_run_time?: string
  description?: string
  created_at: string
  updated_at: string
  crawler?: {
    id: number
    name: string
  }
}

export interface ScheduleCreate {
  name: string
  crawler_id: number
  cron_expression: string
  is_active: boolean
  description?: string
}

export interface ScheduleUpdate {
  name?: string
  crawler_id?: number
  cron_expression?: string
  is_active?: boolean
  description?: string
  next_run_time?: string
}

export interface PaginatedSchedules {
  total: number
  items: Schedule[]
}

export const schedulesApi = {
  list: (params?: {
    skip?: number
    limit?: number
    search?: string
    start_date?: string
    end_date?: string
  }) =>
    api.get<PaginatedSchedules>('/schedules/', { params }),

  get: (id: number) =>
    api.get<Schedule>(`/schedules/${id}`),

  create: (data: ScheduleCreate) =>
    api.post<Schedule>('/schedules/', data),

  update: (id: number, data: ScheduleUpdate) =>
    api.put<Schedule>(`/schedules/${id}`, data),

  delete: (id: number) =>
    api.delete(`/schedules/${id}`),

  toggle: (id: number) =>
    api.put<Schedule>(`/schedules/${id}/toggle`),

  getHistory: (id: number, params?: { skip?: number; limit?: number }) =>
    api.get<{ schedule_id: number; history: any[]; total: number }>(`/schedules/${id}/history`, { params }),

  previewNextRun: (cronExpression: string) =>
    api.get<{ cron_expression: string; next_run_time: string; next_run_time_utc: string }>('/schedules/_preview_next_run', { params: { cron_expression: cronExpression } })
}

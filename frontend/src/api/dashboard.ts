import api from './client'

export interface SystemInfo {
  cpu: {
    percent: number
    count: number
  }
  memory: {
    total: number
    used: number
    available: number
    percent: number
    total_human: string
    used_human: string
    available_human: string
  }
  disk: {
    total: number
    used: number
    free: number
    percent: number
    total_human: string
    used_human: string
    free_human: string
  }
  logs: {
    total_size: number
    total_size_human: string
  }
  running_tasks: number
}

export const dashboardApi = {
  getSystemInfo: () =>
    api.get<SystemInfo>('/dashboard/system'),
}

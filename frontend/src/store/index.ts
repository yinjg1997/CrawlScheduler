import { defineStore } from 'pinia'
import { ref } from 'vue'
import { crawlersApi, type Crawler } from '@/api/crawlers'
import { tasksApi, type TaskExecution } from '@/api/tasks'
import { schedulesApi, type Schedule } from '@/api/schedules'

export const useAppStore = defineStore('app', () => {
  const crawlers = ref<Crawler[]>([])
  const tasks = ref<TaskExecution[]>([])
  const schedules = ref<Schedule[]>([])
  const loading = ref(false)

  // Crawler actions
  const fetchCrawlers = async () => {
    loading.value = true
    try {
      crawlers.value = await crawlersApi.list()
    } catch (error) {
      console.error('Failed to fetch crawlers:', error)
    } finally {
      loading.value = false
    }
  }

  const createCrawler = async (data: any) => {
    await crawlersApi.create(data)
    await fetchCrawlers()
  }

  const updateCrawler = async (id: number, data: any) => {
    await crawlersApi.update(id, data)
    await fetchCrawlers()
  }

  const deleteCrawler = async (id: number) => {
    await crawlersApi.delete(id)
    await fetchCrawlers()
  }

  const executeCrawler = async (id: number) => {
    const result = await crawlersApi.execute(id)
    await fetchTasks()
    return result
  }

  // Task actions
  const fetchTasks = async () => {
    loading.value = true
    try {
      tasks.value = await tasksApi.list()
    } catch (error) {
      console.error('Failed to fetch tasks:', error)
    } finally {
      loading.value = false
    }
  }

  const cancelTask = async (id: number) => {
    await tasksApi.cancel(id)
    await fetchTasks()
  }

  // Schedule actions
  const fetchSchedules = async (params?: {
    skip?: number
    limit?: number
    search?: string
    start_date?: string
    end_date?: string
  }) => {
    loading.value = true
    try {
      schedules.value = await schedulesApi.list(params)
    } catch (error) {
      console.error('Failed to fetch schedules:', error)
    } finally {
      loading.value = false
    }
  }

  const createSchedule = async (data: any, params?: any) => {
    await schedulesApi.create(data)
    await fetchSchedules(params)
  }

  const updateSchedule = async (id: number, data: any, params?: any) => {
    await schedulesApi.update(id, data)
    await fetchSchedules(params)
  }

  const deleteSchedule = async (id: number, params?: any) => {
    await schedulesApi.delete(id)
    await fetchSchedules(params)
  }

  const toggleSchedule = async (id: number, params?: any) => {
    await schedulesApi.toggle(id)
    await fetchSchedules(params)
  }

  return {
    crawlers,
    tasks,
    schedules,
    loading,
    fetchCrawlers,
    createCrawler,
    updateCrawler,
    deleteCrawler,
    executeCrawler,
    fetchTasks,
    cancelTask,
    fetchSchedules,
    createSchedule,
    updateSchedule,
    deleteSchedule,
    toggleSchedule
  }
})

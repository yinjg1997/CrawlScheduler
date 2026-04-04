<template>
  <div class="task-detail-view">
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">任务详情 - #{{ task?.id }}</span>
      </template>
    </el-page-header>

    <div v-if="task" class="task-info">
      <el-descriptions :column="3" border>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(task.status)" size="large">
            {{ getStatusLabel(task.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="爬虫">
          {{ task.crawler?.name || `#${task.crawler_id}` }}
        </el-descriptions-item>
        <el-descriptions-item label="触发方式">
          {{ task.triggered_by === 'manual' ? '手动' : '定时' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDate(task.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="开始时间">
          {{ task.started_at ? formatDate(task.started_at) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="结束时间">
          {{ task.finished_at ? formatDate(task.finished_at) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="耗时">
          {{ task.duration ? `${task.duration} 秒` : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="退出码">
          {{ task.exit_code !== null ? task.exit_code : '-' }}
        </el-descriptions-item>
        <el-descriptions-item v-if="task.error_message" label="错误信息" :span="3">
          <el-text type="danger">{{ task.error_message }}</el-text>
        </el-descriptions-item>
      </el-descriptions>

      <div class="task-actions">
        <el-button
          v-if="task.status === 'pending' || task.status === 'running'"
          type="danger"
          @click="cancelTask"
        >
          <el-icon><VideoPause /></el-icon>
          取消任务
        </el-button>
        <el-button @click="refreshTask">
          <el-icon><Refresh /></el-icon>
          刷新状态
        </el-button>
      </div>
    </div>

    <div class="logs-container">
      <div class="logs-header">
        <h3>执行日志</h3>
        <div class="logs-status" v-if="wsConnected">
          <el-icon class="live-indicator"><VideoPlay /></el-icon>
          <span>实时日志</span>
        </div>
      </div>
      <div class="logs-content" ref="logsContainer">
        <div v-if="logs.length === 0" class="no-logs">
          暂无日志
        </div>
        <div v-else class="log-lines">
          <div v-for="(log, index) in logs" :key="index" class="log-line">
            {{ log }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { tasksApi, type TaskExecution } from '@/api/tasks'
import { VideoPause, Refresh, VideoPlay } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const task = ref<TaskExecution | null>(null)
const logs = ref<string[]>([])
const wsConnected = ref(false)
const logsContainer = ref<HTMLElement>()
let ws: WebSocket | null = null
let refreshTimer: ReturnType<typeof setInterval> | null = null

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const getStatusType = (status: string) => {
  const types: Record<string, any> = {
    pending: 'info',
    running: 'warning',
    success: 'success',
    failed: 'danger',
    cancelled: 'info'
  }
  return types[status] || ''
}

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    pending: '等待中',
    running: '运行中',
    success: '成功',
    failed: '失败',
    cancelled: '已取消'
  }
  return labels[status] || status
}

const fetchTask = async () => {
  try {
    const id = parseInt(route.params.id as string)
    task.value = await tasksApi.get(id)

    // Fetch logs if task is not running
    if (task.value.status !== 'pending' && task.value.status !== 'running') {
      await fetchLogs()
    }
  } catch (error) {
    console.error('Failed to fetch task:', error)
    ElMessage.error('获取任务详情失败')
  }
}

const fetchLogs = async () => {
  try {
    const id = parseInt(route.params.id as string)
    const result = await tasksApi.getLogs(id)
    logs.value = result.logs
    await scrollToBottom()
  } catch (error) {
    console.error('Failed to fetch logs:', error)
  }
}

const scrollToBottom = async () => {
  await nextTick()
  if (logsContainer.value) {
    logsContainer.value.scrollTop = logsContainer.value.scrollHeight
  }
}

const connectWebSocket = () => {
  const id = route.params.id as string
  const wsUrl = `ws://localhost:5173/ws/tasks/${id}/logs`

  ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    wsConnected.value = true
    console.log('WebSocket connected')
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)

      if (data.type === 'log') {
        logs.value.push(data.data)
        scrollToBottom()
      } else if (data.type === 'complete') {
        wsConnected.value = false
        fetchTask() // Refresh task status
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error)
    }
  }

  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
    wsConnected.value = false
  }

  ws.onclose = () => {
    wsConnected.value = false
    console.log('WebSocket closed')
  }
}

const cancelTask = async () => {
  try {
    const id = parseInt(route.params.id as string)
    await tasksApi.cancel(id)
    ElMessage.success('任务已取消')
    fetchTask()
  } catch (error) {
    console.error('Failed to cancel task:', error)
  }
}

const refreshTask = async () => {
  await fetchTask()
  if (task.value?.status !== 'pending' && task.value?.status !== 'running') {
    await fetchLogs()
  }
  ElMessage.success('刷新成功')
}

const goBack = () => {
  router.back()
}

onMounted(async () => {
  await fetchTask()

  // Connect to WebSocket if task is pending or running
  if (task.value && (task.value.status === 'pending' || task.value.status === 'running')) {
    connectWebSocket()

    // Auto-refresh task status
    refreshTimer = setInterval(() => {
      fetchTask()
    }, 3000)
  }
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.task-detail-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: calc(100vh - 120px);
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  font-size: 18px;
  font-weight: 500;
}

.task-info {
  flex-shrink: 0;
}

.task-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.logs-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid #e6e6e6;
  border-radius: 4px;
  overflow: hidden;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background-color: #f5f5f5;
  border-bottom: 1px solid #e6e6e6;
}

.logs-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
}

.logs-status {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #67c23a;
  font-size: 14px;
}

.live-indicator {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.logs-content {
  flex: 1;
  overflow-y: auto;
  background-color: #1e1e1e;
  padding: 16px;
}

.no-logs {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #888;
}

.log-lines {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  color: #d4d4d4;
}

.log-line {
  white-space: pre-wrap;
  word-break: break-all;
}
</style>

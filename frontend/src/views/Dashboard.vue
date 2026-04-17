<template>
  <div class="dashboard-view">
    <div class="page-header">
      <h2>看板</h2>
    </div>

    <!-- 系统资源卡片 -->
    <el-row :gutter="20" class="card-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="card-header">
            <span class="card-title">CPU 使用率</span>
            <el-tag size="small" type="info">{{ sysInfo.cpu.count }} 核</el-tag>
          </div>
          <div class="card-body">
            <el-progress
              type="dashboard"
              :percentage="sysInfo.cpu.percent"
              :color="getProgressColor(sysInfo.cpu.percent)"
              :width="120"
            >
              <template #default="{ percentage }">
                <span class="percentage-value">{{ percentage }}%</span>
              </template>
            </el-progress>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="card-header">
            <span class="card-title">内存使用</span>
            <el-tag size="small" type="info">{{ sysInfo.memory.used_human }} / {{ sysInfo.memory.total_human }}</el-tag>
          </div>
          <div class="card-body">
            <el-progress
              type="dashboard"
              :percentage="sysInfo.memory.percent"
              :color="getProgressColor(sysInfo.memory.percent)"
              :width="120"
            >
              <template #default="{ percentage }">
                <span class="percentage-value">{{ percentage }}%</span>
              </template>
            </el-progress>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="card-header">
            <span class="card-title">磁盘使用</span>
            <el-tag size="small" type="info">{{ sysInfo.disk.used_human }} / {{ sysInfo.disk.total_human }}</el-tag>
          </div>
          <div class="card-body">
            <el-progress
              type="dashboard"
              :percentage="sysInfo.disk.percent"
              :color="getProgressColor(sysInfo.disk.percent)"
              :width="120"
            >
              <template #default="{ percentage }">
                <span class="percentage-value">{{ percentage }}%</span>
              </template>
            </el-progress>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="card-header">
            <span class="card-title">日志文件</span>
          </div>
          <div class="card-body log-card-body">
            <div class="log-size-value">{{ sysInfo.logs.total_size_human }}</div>
            <div class="log-size-label">日志总大小</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 任务统计卡片 -->
    <el-row :gutter="20" class="card-row">
      <el-col :span="6">
        <el-card shadow="hover" class="task-stat-card" @click="goToTasks('running')">
          <div class="task-stat-body">
            <div class="task-stat-number" style="color: #e6a23c">{{ taskStats.running }}</div>
            <div class="task-stat-label">运行中</div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="hover" class="task-stat-card" @click="goToTasks('success')">
          <div class="task-stat-body">
            <div class="task-stat-number" style="color: #67c23a">{{ taskStats.success }}</div>
            <div class="task-stat-label">成功</div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="hover" class="task-stat-card" @click="goToTasks('failed')">
          <div class="task-stat-body">
            <div class="task-stat-number" style="color: #f56c6c">{{ taskStats.failed }}</div>
            <div class="task-stat-label">失败</div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="hover" class="task-stat-card" @click="goToTasks()">
          <div class="task-stat-body">
            <div class="task-stat-number" style="color: #409eff">{{ taskStats.total }}</div>
            <div class="task-stat-label">任务总数</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { dashboardApi, type SystemInfo } from '@/api/dashboard'
import { tasksApi } from '@/api/tasks'

const router = useRouter()

const sysInfo = reactive<SystemInfo>({
  cpu: { percent: 0, count: 0 },
  memory: { total: 0, used: 0, available: 0, percent: 0, total_human: '-', used_human: '-', available_human: '-' },
  disk: { total: 0, used: 0, free: 0, percent: 0, total_human: '-', used_human: '-', free_human: '-' },
  logs: { total_size: 0, total_size_human: '-' },
  running_tasks: 0,
})

const taskStats = reactive({
  total: 0,
  success: 0,
  failed: 0,
  running: 0,
})

const loading = ref(false)

const getProgressColor = (percentage: number) => {
  if (percentage < 60) return '#67c23a'
  if (percentage < 80) return '#e6a23c'
  return '#f56c6c'
}

const fetchData = async () => {
  loading.value = true
  try {
    const [sys, stats] = await Promise.all([
      dashboardApi.getSystemInfo(),
      tasksApi.getStatistics(),
    ])
    Object.assign(sysInfo, sys)
    Object.assign(taskStats, stats)
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error)
  } finally {
    loading.value = false
  }
}

const goToTasks = (tab?: string) => {
  const query: Record<string, string> = {}
  if (tab) query.tab = tab
  router.push({ path: '/tasks', query })
}

let refreshTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  fetchData()
  refreshTimer = setInterval(fetchData, 10000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
})
</script>

<style scoped>
.dashboard-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-header h2 {
  margin: 0;
}

.card-row {
  margin-bottom: 0;
}

.stat-card {
  height: 220px;
  display: flex;
  flex-direction: column;
}

.stat-card :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-title {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
}

.card-body {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.log-card-body {
  flex-direction: column;
  gap: 8px;
}

.log-size-value {
  font-size: 32px;
  font-weight: 600;
  color: #409eff;
}

.log-size-label {
  font-size: 13px;
  color: #909399;
}

.percentage-value {
  font-size: 18px;
  font-weight: 600;
}

.task-stat-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.task-stat-card:hover {
  transform: translateY(-2px);
}

.task-stat-body {
  text-align: center;
  padding: 16px 0;
}

.task-stat-number {
  font-size: 36px;
  font-weight: 600;
  line-height: 1.2;
}

.task-stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}
</style>

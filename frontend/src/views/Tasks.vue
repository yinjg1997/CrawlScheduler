<template>
  <div class="tasks-view">
    <div class="page-header">
      <h2>任务列表</h2>
    </div>

    <div class="filter-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索爬虫名称"
        style="width: 200px"
        clearable
        @input="handleSearchDebounced"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <el-select
        v-model="selectedCrawlerId"
        placeholder="按爬虫筛选"
        style="width: 200px"
        clearable
        @change="handleCrawlerFilter"
      >
        <el-option
          v-for="crawler in crawlers"
          :key="crawler.id"
          :label="crawler.name"
          :value="crawler.id"
        />
      </el-select>

      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        format="YYYY-MM-DD"
        value-format="YYYY-MM-DD"
        style="width: 240px"
        @change="handleDateRangeChange"
      />

      <el-button @click="resetFilters">重置</el-button>
    </div>

    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane label="运行中" name="running" />
      <el-tab-pane label="成功" name="success" />
      <el-tab-pane label="失败" name="failed" />
    </el-tabs>

    <div class="table-container">
      <el-table
        :data="filteredTasks"
        v-loading="loading"
        stripe
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="爬虫" min-width="140">
          <template #default="{ row }">
            <span v-if="row.crawler">{{ row.crawler.name }}</span>
            <span v-else class="text-gray-400">#{{ row.crawler_id }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="触发方式" width="100">
          <template #default="{ row }">
            <el-tag :type="row.triggered_by === 'manual' ? '' : 'warning'" size="small">
              {{ row.triggered_by === 'manual' ? '手动' : '定时' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="命令" min-width="250" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.crawler">{{ row.crawler.command }}</span>
            <span v-else class="text-gray-400">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="耗时(秒)" width="100">
          <template #default="{ row }">
            {{ row.duration || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="exit_code" label="退出码" width="80">
          <template #default="{ row }">
            <span v-if="row.exit_code !== null">{{ row.exit_code }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="170">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              text
              @click="viewTask(row)"
            >
              详情
            </el-button>
            <el-button
              type="warning"
              size="small"
              text
              @click="retryTask(row)"
            >
              重试
            </el-button>
            <el-button
              v-if="row.status === 'pending' || row.status === 'running'"
              type="danger"
              size="small"
              text
              @click="cancelTask(row)"
            >
              取消
            </el-button>
            <el-popconfirm
              v-if="row.status !== 'running'"
              title="确定要删除这条任务记录吗？"
              @confirm="deleteTask(row)"
            >
              <template #reference>
                <el-button
                  type="danger"
                  size="small"
                  text
                >
                  删除
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="pagination-toolbar">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        background
      />

      <el-button
        type="danger"
        :disabled="selectedTasks.length === 0"
        @click="handleBulkDelete"
      >
        <el-icon><Delete /></el-icon>
        批量删除 ({{ selectedTasks.length }})
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAppStore } from '@/store'
import { tasksApi, type TaskExecution } from '@/api/tasks'
import { Search, Delete } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const store = useAppStore()

// 从 URL query 恢复过滤条件
const activeTab = ref((route.query.tab as string) || 'all')
const loading = ref(false)
const selectedCrawlerId = ref<number | undefined>(
  route.query.crawler_id ? Number(route.query.crawler_id) : undefined
)
const searchKeyword = ref((route.query.search as string) || '')
const dateRange = ref<[string, string] | null>(
  route.query.date_from && route.query.date_to
    ? [route.query.date_from as string, route.query.date_to as string]
    : null
)
const crawlers = ref<{ id: number; name: string }[]>([])
const selectedTasks = ref<TaskExecution[]>([])
const currentPage = ref(Number(route.query.page) || 1)
const pageSize = ref(Number(route.query.size) || 20)
const total = ref(0)

// 将当前过滤条件同步到 URL query
const syncFiltersToQuery = () => {
  const query: Record<string, string> = {}
  if (activeTab.value !== 'all') query.tab = activeTab.value
  if (selectedCrawlerId.value !== undefined) query.crawler_id = String(selectedCrawlerId.value)
  if (searchKeyword.value.trim()) query.search = searchKeyword.value.trim()
  if (dateRange.value) {
    query.date_from = dateRange.value[0]
    query.date_to = dateRange.value[1]
  }
  if (currentPage.value > 1) query.page = String(currentPage.value)
  if (pageSize.value !== 20) query.size = String(pageSize.value)
  router.replace({ path: '/tasks', query })
}

// Debounced search handler
let searchDebounceTimer: ReturnType<typeof setTimeout> | null = null
const handleSearchDebounced = () => {
  if (searchDebounceTimer) {
    clearTimeout(searchDebounceTimer)
  }
  searchDebounceTimer = setTimeout(() => {
    handleSearch()
  }, 500) // 500ms debounce
}

const handleSearch = () => {
  currentPage.value = 1
  fetchTasks()
}

const handleDateRangeChange = () => {
  currentPage.value = 1
  fetchTasks()
}

const handleCrawlerFilter = () => {
  currentPage.value = 1
  fetchTasks()
}

const handleTabChange = () => {
  currentPage.value = 1
  fetchTasks()
}

const resetFilters = () => {
  searchKeyword.value = ''
  dateRange.value = null
  selectedCrawlerId.value = undefined
  activeTab.value = 'all'
  currentPage.value = 1
  fetchTasks()
}

const filteredTasks = computed(() => {
  return store.tasks
})

const handleSizeChange = (newSize: number) => {
  pageSize.value = newSize
  currentPage.value = 1
  fetchTasks()
}

const handleCurrentChange = (newPage: number) => {
  currentPage.value = newPage
  fetchTasks()
}

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

const fetchTasks = async () => {
  const params: {
    crawler_id?: number
    status_filter?: string
    search?: string
    date_from?: string
    date_to?: string
    skip?: number
    limit?: number
  } = {
    skip: (currentPage.value - 1) * pageSize.value,
    limit: pageSize.value
  }

  if (selectedCrawlerId.value !== undefined) {
    params.crawler_id = selectedCrawlerId.value
  }

  if (activeTab.value !== 'all') {
    params.status_filter = activeTab.value
  }

  if (searchKeyword.value.trim()) {
    params.search = searchKeyword.value.trim()
  }

  if (dateRange.value && dateRange.value.length === 2) {
    params.date_from = dateRange.value[0]
    params.date_to = dateRange.value[1]
  }

  const response = await tasksApi.list(params)
  store.tasks = response.items
  total.value = response.total
  await store.fetchCrawlers()
  // Update crawlers list from store
  crawlers.value = store.crawlers.map(c => ({ id: c.id, name: c.name }))
  syncFiltersToQuery()
}

const viewTask = (task: TaskExecution) => {
  router.push(`/tasks/${task.id}`)
}

const cancelTask = async (task: TaskExecution) => {
  try {
    await store.cancelTask(task.id)
    await fetchTasks()
    ElMessage.success('任务已取消')
  } catch (error) {
    console.error('Failed to cancel:', error)
  }
}

const retryTask = async (task: TaskExecution) => {
  try {
    const result = await tasksApi.retry(task.id)
    ElMessage.success(`任务已重新执行: ID ${result.task_id}`)
    router.push(`/tasks/${result.task_id}`)
  } catch (error) {
    console.error('Failed to retry:', error)
    ElMessage.error('重试失败')
  }
}

const handleSelectionChange = (selection: TaskExecution[]) => {
  selectedTasks.value = selection
}

const deleteTask = async (task: TaskExecution) => {
  try {
    await tasksApi.delete(task.id)
    await fetchTasks()
    ElMessage.success('删除成功')
  } catch (error) {
    console.error('Failed to delete:', error)
    ElMessage.error('删除失败')
  }
}

const handleBulkDelete = async () => {
  try {
    const taskIds = selectedTasks.value
      .filter(task => task.status !== 'running')
      .map(task => task.id)

    if (taskIds.length === 0) {
      ElMessage.warning('请选择要删除的任务（运行中的任务无法删除）')
      return
    }

    await ElMessageBox.confirm(
      `确定要删除选中的 ${taskIds.length} 条任务记录吗？`,
      '批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const result = await tasksApi.bulkDelete(taskIds)
    await fetchTasks()
    selectedTasks.value = []

    if (result.skipped_count > 0) {
      ElMessage.warning(
        `成功删除 ${result.deleted_count} 条，跳过 ${result.skipped_count} 条（运行中或不存在）`
      )
    } else {
      ElMessage.success(`成功删除 ${result.deleted_count} 条任务记录`)
    }
  } catch (error) {
    console.error('Failed to bulk delete:', error)
  }
}

let refreshTimer: ReturnType<typeof setInterval> | null = null

onMounted(async () => {
  await fetchTasks()
  refreshTimer = setInterval(() => fetchTasks(), 10000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
})
</script>

<style scoped>
.tasks-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
}

:deep(.el-tabs) {
  margin-bottom: 20px;
}

.pagination-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0 0 0;
  flex-shrink: 0;
}

.filter-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.table-container {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

:deep(.el-table) {
  height: 100% !important;
}

.text-gray-400 {
  color: #909399;
}
</style>

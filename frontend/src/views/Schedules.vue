<template>
  <div class="schedules-view">
    <div class="page-header">
      <h2>定时任务</h2>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        添加定时任务
      </el-button>
    </div>

    <!-- Filter Bar -->
    <div class="filter-bar">
      <el-input
        v-model="filters.search"
        placeholder="搜索任务名称或描述"
        clearable
        style="width: 250px"
        @clear="handleFilterChange"
        @keyup.enter="handleFilterChange"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        value-format="YYYY-MM-DD"
        @change="handleFilterChange"
        style="width: 280px"
      />

      <el-button type="primary" @click="handleFilterChange">
        查询
      </el-button>
      <el-button @click="resetFilters">
        重置
      </el-button>
    </div>

    <div class="table-container">
      <el-table :data="schedules" v-loading="store.loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="爬虫" width="150">
          <template #default="{ row }">
            {{ row.crawler?.name || `#${row.crawler_id}` }}
          </template>
        </el-table-column>
        <el-table-column prop="cron_expression" label="Cron表达式" width="150">
          <template #default="{ row }">
            <el-text class="cron-text">{{ row.cron_expression }}</el-text>
          </template>
        </el-table-column>
        <el-table-column prop="next_run_time" label="下次运行时间" width="180">
          <template #default="{ row }">
            {{ row.next_run_time ? formatDate(row.next_run_time) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-switch :model-value="row.is_active" @change="toggleSchedule(row)" />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button
            type="primary"
            size="small"
            text
            @click="showEditDialog(row)"
          >
            编辑
          </el-button>
          <el-popconfirm
            title="确定要删除这个定时任务吗？"
            @confirm="deleteSchedule(row.id)"
          >
            <template #reference>
              <el-button type="danger" size="small" text>删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
    </div>

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

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑定时任务' : '添加定时任务'"
      width="600px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
      >
        <el-form-item label="爬虫" prop="crawler_id">
          <el-select v-model="form.crawler_id" placeholder="请选择爬虫" style="width: 100%">
            <el-option
              v-for="crawler in store.crawlers"
              :key="crawler.id"
              :label="crawler.name"
              :value="crawler.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="Cron表达式" prop="cron_expression">
          <el-input
            v-model="form.cron_expression"
            placeholder="例如: 0 0 * * * (每天0点)"
            @input="handleCronChange"
          />
          <el-text class="hint" size="small" type="info">
            格式: 分 时 日 月 周 (例如: 0 0 * * * 表示每天0点执行)
          </el-text>
          <el-text v-if="cronError" class="next-run-preview error-preview">
            {{ cronError }}
          </el-text>
          <el-text v-else-if="nextRunPreview" class="next-run-preview" type="success">
            下次运行时间: {{ formatPreviewDate(nextRunPreview) }}
          </el-text>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入定时任务描述"
          />
        </el-form-item>
        <el-form-item label="状态" prop="is_active">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAppStore } from '@/store'
import type { Schedule, ScheduleCreate, ScheduleUpdate } from '@/api/schedules'
import { schedulesApi } from '@/api/schedules'
import { Plus, Search } from '@element-plus/icons-vue'

const store = useAppStore()

const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref()
const nextRunPreview = ref<string | null>(null)
const schedules = ref<Schedule[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const form = reactive<ScheduleCreate & { id?: number }>({
  name: '',
  crawler_id: 0,
  cron_expression: '',
  description: '',
  is_active: true
})

// Filters
const filters = reactive({
  search: ''
})

const dateRange = ref<[string, string] | null>(null)
const cronError = ref<string | null>(null)

const rules = {
  crawler_id: [{ required: true, message: '请选择爬虫', trigger: 'change' }],
  cron_expression: [{ required: true, message: '请输入Cron表达式', trigger: 'blur' }]
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const formatPreviewDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
}

// Debounce timer for cron preview
let cronPreviewTimer: ReturnType<typeof setTimeout> | null = null

const handleCronChange = () => {
  if (cronPreviewTimer) {
    clearTimeout(cronPreviewTimer)
  }

  if (!form.cron_expression.trim()) {
    nextRunPreview.value = null
    cronError.value = null
    return
  }

  cronPreviewTimer = setTimeout(async () => {
    try {
      const result = await schedulesApi.previewNextRun(form.cron_expression)
      nextRunPreview.value = result.next_run_time
      cronError.value = null
    } catch (error: any) {
      console.error('Failed to preview next run:', error)
      nextRunPreview.value = null
      // Extract error message from API response
      if (error.response?.data?.detail) {
        cronError.value = error.response.data.detail
      } else if (error.response?.data?.cron_expression) {
        cronError.value = error.response.data.cron_expression
      } else {
        cronError.value = 'Cron表达式格式错误'
      }
    }
  }, 500) // 500ms debounce
}

const showCreateDialog = () => {
  isEdit.value = false
  Object.assign(form, {
    name: '',
    crawler_id: 0,
    cron_expression: '',
    description: '',
    is_active: true
  })
  nextRunPreview.value = null
  cronError.value = null
  dialogVisible.value = true
}

const showEditDialog = (schedule: Schedule) => {
  isEdit.value = true
  Object.assign(form, schedule)
  nextRunPreview.value = schedule.next_run_time || null
  cronError.value = null
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value.validate()
  submitting.value = true

  try {
    if (isEdit.value) {
      await store.updateSchedule(form.id!, form as ScheduleUpdate, getFilterParams())
      await fetchSchedules()
      ElMessage.success('更新成功')
    } else {
      // Auto-fill name with crawler name when creating
      const submitData = { ...form }
      const crawler = store.crawlers.find(c => c.id === form.crawler_id)
      if (crawler) {
        submitData.name = crawler.name
      }
      await store.createSchedule(submitData, getFilterParams())
      await fetchSchedules()
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
  } catch (error) {
    console.error('Failed to submit:', error)
  } finally {
    submitting.value = false
  }
}

const toggleSchedule = async (schedule: Schedule) => {
  try {
    await store.toggleSchedule(schedule.id, getFilterParams())
    await fetchSchedules()
    ElMessage.success(schedule.is_active ? '已启用' : '已禁用')
  } catch (error) {
    console.error('Failed to toggle:', error)
  }
}

const deleteSchedule = async (id: number) => {
  try {
    await store.deleteSchedule(id, getFilterParams())
    await fetchSchedules()
    ElMessage.success('删除成功')
  } catch (error) {
    console.error('Failed to delete:', error)
  }
}

// Filter handlers
const getFilterParams = () => {
  const params: any = {
    search: filters.search || undefined,
    skip: (currentPage.value - 1) * pageSize.value,
    limit: pageSize.value
  }

  if (dateRange.value && dateRange.value.length === 2) {
    params.start_date = new Date(dateRange.value[0]).toISOString()
    params.end_date = new Date(dateRange.value[1]).toISOString()
  }

  return params
}

const fetchSchedules = async () => {
  const response = await schedulesApi.list(getFilterParams())
  schedules.value = response.items
  total.value = response.total
}

const handleFilterChange = async () => {
  currentPage.value = 1
  await fetchSchedules()
}

const resetFilters = async () => {
  filters.search = ''
  dateRange.value = null
  currentPage.value = 1
  await fetchSchedules()
}

const handleSizeChange = (newSize: number) => {
  pageSize.value = newSize
  currentPage.value = 1
  fetchSchedules()
}

const handleCurrentChange = (newPage: number) => {
  currentPage.value = newPage
  fetchSchedules()
}

onMounted(async () => {
  await Promise.all([store.fetchCrawlers(), fetchSchedules()])
})
</script>

<style scoped>
.schedules-view {
  height: 100%;
  display: flex;
  flex-direction: column;
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

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 8px;
  align-items: center;
}

:deep(.el-table) {
  flex: 1;
}

.table-container {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

:deep(.el-table__body-wrapper) {
  overflow-y: auto;
  max-height: calc(100vh - 400px);
}

.el-pagination {
  padding: 16px 0 0 0;
  flex-shrink: 0;
}

.cron-text {
  font-family: 'Courier New', monospace;
  background-color: #f5f5f5;
  padding: 4px 8px;
  border-radius: 4px;
}

.hint {
  display: block;
  margin-top: 4px;
}

.next-run-preview {
  display: block;
  margin-top: 8px;
  padding: 6px 10px;
  background-color: #f0f9ff;
  border-left: 3px solid #409eff;
  border-radius: 4px;
}

.next-run-preview.error-preview {
  background-color: #fef0f0;
  border-left-color: #f56c6c;
}
</style>

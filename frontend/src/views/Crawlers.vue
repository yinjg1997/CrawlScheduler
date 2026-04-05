<template>
  <div class="crawlers-view">
    <div class="page-header">
      <h2>爬虫管理</h2>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        添加爬虫
      </el-button>
    </div>

    <div class="filter-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索爬虫名称或命令"
        clearable
        style="width: 300px"
        @input="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select
        v-model="filterProjectId"
        placeholder="筛选项目"
        clearable
        style="width: 200px"
        @change="handleSearch"
      >
        <el-option
          v-for="project in projects"
          :key="project.id"
          :label="project.name"
          :value="project.id"
        />
      </el-select>
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        value-format="YYYY-MM-DD"
        @change="handleSearch"
        clearable
      />
      <el-button @click="resetFilters">重置</el-button>
    </div>

    <div class="table-container">
      <el-table :data="crawlers" v-loading="store.loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="command" label="命令" show-overflow-tooltip />
        <el-table-column label="项目" width="120">
          <template #default="{ row }">
            <span v-if="row.project_name">{{ row.project_name }}</span>
            <span v-else class="text-gray-400">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220">
        <template #default="{ row }">
          <el-button
            type="primary"
            size="small"
            @click="executeCrawler(row)"
          >
            执行
          </el-button>
          <el-button
            type="primary"
            size="small"
            text
            @click="showEditDialog(row)"
          >
            编辑
          </el-button>
          <el-popconfirm
            title="确定要删除这个爬虫吗？"
            @confirm="deleteCrawler(row.id)"
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
      :title="isEdit ? '编辑爬虫' : '添加爬虫'"
      width="600px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
      >
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入爬虫名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入爬虫描述"
          />
        </el-form-item>
        <el-form-item label="所属项目" prop="project_id">
          <el-select
            v-model="form.project_id"
            placeholder="请选择项目"
            style="width: 100%"
            filterable
          >
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
          <el-text class="hint" size="small" type="info">
            爬虫将使用项目配置的工作目录和 Python 环境
          </el-text>
        </el-form-item>
        <el-form-item label="执行命令" prop="command">
          <el-input
            v-model="form.command"
            placeholder="例如: python main.py"
          />
          <el-text class="hint" size="small" type="info">
            Python 解释器和工作目录将使用项目配置
          </el-text>
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
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAppStore } from '@/store'
import { crawlersApi, type Crawler, type CrawlerCreate, type CrawlerUpdate } from '@/api/crawlers'
import { projectsApi, type Project } from '@/api/projects'
import { Plus, Search } from '@element-plus/icons-vue'

const router = useRouter()
const store = useAppStore()

const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref()
const projects = ref<Project[]>([])
const crawlers = ref<Crawler[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// Filter states
const searchKeyword = ref('')
const filterProjectId = ref<number | undefined>(undefined)
const dateRange = ref<[string, string] | null>(null)

const form = reactive<CrawlerCreate & { id?: number }>({
  name: '',
  description: '',
  command: '',
  project_id: undefined
})

const rules = {
  name: [{ required: true, message: '请输入爬虫名称', trigger: 'blur' }],
  command: [{ required: true, message: '请输入执行命令', trigger: 'blur' }],
  project_id: [{ required: true, message: '请选择所属项目', trigger: 'change' }]
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const fetchProjects = async () => {
  try {
    const response = await projectsApi.list({ limit: 100 })
    projects.value = response.items
  } catch (error) {
    console.error('Failed to fetch projects:', error)
  }
}

const showCreateDialog = async () => {
  isEdit.value = false
  Object.assign(form, {
    name: '',
    description: '',
    command: '',
    project_id: undefined
  })

  await fetchProjects()
  dialogVisible.value = true
}

const showEditDialog = async (crawler: Crawler) => {
  isEdit.value = true
  Object.assign(form, {
    id: crawler.id,
    name: crawler.name,
    description: crawler.description,
    command: crawler.command,
    project_id: crawler.project_id
  })

  await fetchProjects()
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value.validate()
  submitting.value = true

  try {
    if (isEdit.value) {
      await store.updateCrawler(form.id!, form as CrawlerUpdate)
      await fetchCrawlers()
      ElMessage.success('更新成功')
    } else {
      await store.createCrawler(form)
      await fetchCrawlers()
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
  } catch (error) {
    console.error('Failed to submit:', error)
  } finally {
    submitting.value = false
  }
}

const deleteCrawler = async (id: number) => {
  try {
    await store.deleteCrawler(id)
    await fetchCrawlers()
    ElMessage.success('删除成功')
  } catch (error) {
    console.error('Failed to delete:', error)
  }
}

const executeCrawler = async (crawler: Crawler) => {
  try {
    const result = await store.executeCrawler(crawler.id)
    ElMessage.success(`任务已创建: ID ${result.task_id}`)
    router.push(`/tasks/${result.task_id}`)
  } catch (error) {
    console.error('Failed to execute:', error)
  }
}

const fetchCrawlers = async () => {
  const params: any = {
    skip: (currentPage.value - 1) * pageSize.value,
    limit: pageSize.value
  }

  // Add filters if present
  if (searchKeyword.value) {
    params.search = searchKeyword.value
  }
  if (filterProjectId.value) {
    params.project_id = filterProjectId.value
  }
  if (dateRange.value && dateRange.value.length === 2) {
    params.date_from = dateRange.value[0]
    params.date_to = dateRange.value[1]
  }

  const response = await crawlersApi.list(params)
  crawlers.value = response.items
  total.value = response.total
}

const handleSearch = () => {
  currentPage.value = 1
  fetchCrawlers()
}

const resetFilters = () => {
  searchKeyword.value = ''
  filterProjectId.value = undefined
  dateRange.value = null
  currentPage.value = 1
  fetchCrawlers()
}

const handleSizeChange = (newSize: number) => {
  pageSize.value = newSize
  currentPage.value = 1
  fetchCrawlers()
}

const handleCurrentChange = (newPage: number) => {
  currentPage.value = newPage
  fetchCrawlers()
}

onMounted(() => {
  fetchProjects()
  fetchCrawlers()
})
</script>

<style scoped>
.crawlers-view {
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
  margin-bottom: 16px;
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

.env-option {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.env-option span:first-child {
  flex: 1;
}

.env-version {
  color: #909399;
  font-size: 12px;
}

.hint {
  display: block;
  margin-top: 4px;
}

.text-gray-400 {
  color: #909399;
}
</style>

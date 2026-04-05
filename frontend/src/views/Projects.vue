<template>
  <div class="projects-view">
    <div class="page-header">
      <h2>项目管理</h2>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        添加项目
      </el-button>
    </div>

    <div class="filter-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索项目名称或描述"
        clearable
        style="width: 300px"
        @input="handleSearch"
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
        @change="handleSearch"
        clearable
      />
      <el-button @click="resetFilters">重置</el-button>
    </div>

    <div class="table-container">
      <el-table :data="projects" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="项目名称" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="working_directory" label="工作目录" show-overflow-tooltip />
        <el-table-column label="爬虫数量" width="100">
          <template #default="{ row }">
            {{ row.crawler_count }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
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
              text
              @click="showEditDialog(row)"
            >
              编辑
            </el-button>
            <el-popconfirm
              :title="'确定要删除项目「' + row.name + '」吗？删除项目将同时删除其下所有爬虫。'"
              @confirm="deleteProject(row.id)"
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
      :title="isEdit ? '编辑项目' : '添加项目'"
      width="600px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
      >
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入项目描述"
          />
        </el-form-item>
        <el-form-item label="默认工作目录" prop="working_directory">
          <el-input
            v-model="form.working_directory"
            placeholder="例如: ./data/projects/my_project"
          />
          <el-text class="hint" size="small" type="info">
            创建爬虫时将自动使用此目录
          </el-text>
        </el-form-item>
        <el-form-item label="默认Python环境" prop="python_executable">
          <el-select
            v-model="form.python_executable"
            placeholder="选择Python环境（可选）"
            style="width: 100%"
            filterable
            clearable
          >
            <el-option
              v-for="env in pythonEnvironments"
              :key="env.path"
              :label="`${env.name} - ${env.version}`"
              :value="env.path"
            >
              <div class="env-option">
                <span>{{ env.name }}</span>
                <span class="env-version">{{ env.version }}</span>
                <el-tag v-if="env.is_active" type="success" size="small">当前</el-tag>
              </div>
            </el-option>
          </el-select>
          <el-text class="hint" size="small" type="info">
            创建爬虫时将自动使用此Python环境
          </el-text>
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
import { projectsApi, type Project, type ProjectCreate, type ProjectUpdate } from '@/api/projects'
import { pythonEnvironmentsApi, type PythonEnvironmentListItem } from '@/api/python_environments'
import { Plus, Search } from '@element-plus/icons-vue'

const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref()
const pythonEnvironments = ref<PythonEnvironmentListItem[]>([])
const projects = ref<Project[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// Filter states
const searchKeyword = ref('')
const dateRange = ref<[string, string] | null>(null)

const form = reactive<ProjectCreate & { id?: number }>({
  name: '',
  description: '',
  working_directory: '',
  python_executable: '',
  is_active: true
})

const rules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
  working_directory: [{ required: true, message: '请输入默认工作目录', trigger: 'blur' }]
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const fetchPythonEnvironments = async () => {
  try {
    const response = await pythonEnvironmentsApi.getAllEnvironments()
    pythonEnvironments.value = response.items
  } catch (error) {
    console.error('Failed to fetch Python environments:', error)
  }
}

const showCreateDialog = async () => {
  isEdit.value = false
  Object.assign(form, {
    name: '',
    description: '',
    working_directory: '',
    python_executable: '',
    is_active: true
  })

  await fetchPythonEnvironments()
  dialogVisible.value = true
}

const showEditDialog = async (project: Project) => {
  isEdit.value = true
  Object.assign(form, project)

  await fetchPythonEnvironments()
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value.validate()
  submitting.value = true

  try {
    if (isEdit.value) {
      const data: ProjectUpdate = {
        name: form.name,
        description: form.description,
        working_directory: form.working_directory,
        python_executable: form.python_executable,
        is_active: form.is_active
      }
      await projectsApi.update(form.id!, data)
      ElMessage.success('更新成功')
    } else {
      await projectsApi.create(form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    await fetchProjects()
  } catch (error) {
    console.error('Failed to submit:', error)
  } finally {
    submitting.value = false
  }
}

const deleteProject = async (id: number) => {
  try {
    await projectsApi.delete(id)
    ElMessage.success('删除成功')
    await fetchProjects()
  } catch (error) {
    console.error('Failed to delete:', error)
  }
}

const fetchProjects = async () => {
  loading.value = true
  try {
    const params: any = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    }

    // Add filters if present
    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }
    if (dateRange.value && dateRange.value.length === 2) {
      params.date_from = dateRange.value[0]
      params.date_to = dateRange.value[1]
    }

    const response = await projectsApi.list(params)
    projects.value = response.items
    total.value = response.total
  } catch (error) {
    console.error('Failed to fetch projects:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchProjects()
}

const resetFilters = () => {
  searchKeyword.value = ''
  dateRange.value = null
  currentPage.value = 1
  fetchProjects()
}

const handleSizeChange = (newSize: number) => {
  pageSize.value = newSize
  currentPage.value = 1
  fetchProjects()
}

const handleCurrentChange = (newPage: number) => {
  currentPage.value = newPage
  fetchProjects()
}

onMounted(() => {
  fetchProjects()
})
</script>

<style scoped>
.projects-view {
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
</style>

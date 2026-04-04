<template>
  <div class="python-environments-view">
    <div class="page-header">
      <h2>Python环境管理</h2>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        添加环境
      </el-button>
    </div>

    <el-table
      :data="environments"
      v-loading="loading"
      stripe
      :row-key="(row: any) => row.id"
      border
    >
      <el-table-column prop="name" label="名称" width="250" />
      <el-table-column prop="path" label="路径" min-width="300" show-overflow-tooltip />
      <el-table-column prop="version" label="版本" width="150" />
      <el-table-column label="类型" width="120">
        <template #default="{ row }">
          <el-tag :type="getTypeColor(row.type)" size="small">
            {{ getTypeLabel(row.type) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.type === 'user'"
            type="primary"
            size="small"
            text
            @click="showEditDialog(row)"
          >
            编辑
          </el-button>
          <el-popconfirm
            v-if="row.type === 'user'"
            title="确定要删除这个环境吗？"
            @confirm="deleteEnvironment(row.id)"
          >
            <template #reference>
              <el-button type="danger" size="small" text>删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑Python环境' : '添加Python环境'"
      width="600px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
      >
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="例如: my-env-3.10" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="2"
            placeholder="例如: Python 3.10 环境用于数据分析"
          />
        </el-form-item>
        <el-form-item label="Python路径" prop="path">
          <el-input
            v-model="form.path"
            placeholder="例如: /usr/bin/python3.10 或 /opt/anaconda3/envs/myenv/bin/python"
          />
          <el-text class="hint" size="small" type="info">
            Python解释器的完整路径
          </el-text>
        </el-form-item>
        <el-form-item label="版本" prop="version">
          <el-input
            v-model="form.version"
            placeholder="例如: Python 3.10.0"
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
import {
  pythonEnvironmentsApi,
  type PythonEnvironmentListItem,
  type PythonEnvironmentCreate,
  type PythonEnvironmentUpdate,
  type PythonEnvironment
} from '@/api/python_environments'
import { Plus } from '@element-plus/icons-vue'

const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref()
const environments = ref<PythonEnvironmentListItem[]>([])
const currentUserEnv = ref<PythonEnvironment | null>(null)

const form = reactive<PythonEnvironmentCreate & { id?: number }>({
  name: '',
  description: '',
  path: '',
  version: '',
  is_active: true
})

const rules = {
  name: [{ required: true, message: '请输入环境名称', trigger: 'blur' }],
  path: [{ required: true, message: '请输入Python路径', trigger: 'blur' }]
}

const getTypeColor = (type: string) => {
  switch (type) {
    case 'system':
      return 'warning'
    case 'conda':
      return 'success'
    case 'user':
      return 'primary'
    default:
      return 'info'
  }
}

const getTypeLabel = (type: string) => {
  switch (type) {
    case 'system':
      return '系统'
    case 'conda':
      return 'Conda'
    case 'user':
      return '自定义'
    default:
      return type
  }
}

const fetchEnvironments = async () => {
  loading.value = true
  try {
    environments.value = await pythonEnvironmentsApi.getAllEnvironments()
  } catch (error) {
    console.error('Failed to fetch environments:', error)
    ElMessage.error('获取Python环境列表失败')
  } finally {
    loading.value = false
  }
}

const showCreateDialog = () => {
  isEdit.value = false
  Object.assign(form, {
    name: '',
    description: '',
    path: '',
    version: '',
    is_active: true
  })
  dialogVisible.value = true
}

const showEditDialog = async (env: PythonEnvironmentListItem) => {
  isEdit.value = true
  // Fetch full environment details for editing
  try {
    currentUserEnv.value = await pythonEnvironmentsApi.get(env.id)
    Object.assign(form, currentUserEnv.value)
  } catch (error) {
    console.error('Failed to fetch environment details:', error)
    ElMessage.error('获取环境详情失败')
    return
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value.validate()
  submitting.value = true

  try {
    if (isEdit.value) {
      await pythonEnvironmentsApi.update(form.id!, form as PythonEnvironmentUpdate)
      ElMessage.success('更新成功')
    } else {
      await pythonEnvironmentsApi.create(form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    await fetchEnvironments()
  } catch (error) {
    console.error('Failed to submit:', error)
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

const deleteEnvironment = async (id: number) => {
  try {
    await pythonEnvironmentsApi.delete(id)
    ElMessage.success('删除成功')
    await fetchEnvironments()
  } catch (error) {
    console.error('Failed to delete:', error)
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  fetchEnvironments()
})
</script>

<style scoped>
.python-environments-view {
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

:deep(.el-table) {
  flex: 1;
  overflow: auto;
}

.hint {
  display: block;
  margin-top: 4px;
}
</style>

<template>
  <div class="python-environments-view">
    <div class="page-header">
      <h2>Python环境管理</h2>
    </div>

    <div class="table-container">
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  pythonEnvironmentsApi,
  type PythonEnvironmentListItem,
} from '@/api/python_environments'

const loading = ref(false)
const environments = ref<PythonEnvironmentListItem[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

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
    const response = await pythonEnvironmentsApi.getAllEnvironments({
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    })
    environments.value = response.items
    total.value = response.total
  } catch (error) {
    console.error('Failed to fetch environments:', error)
  } finally {
    loading.value = false
  }
}

const handleSizeChange = (newSize: number) => {
  pageSize.value = newSize
  currentPage.value = 1
  fetchEnvironments()
}

const handleCurrentChange = (newPage: number) => {
  currentPage.value = newPage
  fetchEnvironments()
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
  height: 100%;
}

:deep(.el-table__body-wrapper) {
  overflow-y: auto;
}

.table-container {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.el-pagination {
  padding: 16px 0 0 0;
  flex-shrink: 0;
}
</style>

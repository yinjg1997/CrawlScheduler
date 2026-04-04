<template>
  <div class="crawler-detail-view">
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">爬虫详情 - {{ crawler?.name }}</span>
      </template>
    </el-page-header>

    <el-descriptions v-if="crawler" :column="2" border class="crawler-info">
      <el-descriptions-item label="ID">{{ crawler.id }}</el-descriptions-item>
      <el-descriptions-item label="状态">
        <el-tag :type="crawler.is_active ? 'success' : 'info'">
          {{ crawler.is_active ? '启用' : '禁用' }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="名称">{{ crawler.name }}</el-descriptions-item>
      <el-descriptions-item label="创建时间">
        {{ formatDate(crawler.created_at) }}
      </el-descriptions-item>
      <el-descriptions-item label="执行命令" :span="2">
        <el-text class="command-text">{{ crawler.command }}</el-text>
      </el-descriptions-item>
      <el-descriptions-item label="工作目录" :span="2">
        <el-text>{{ crawler.working_directory }}</el-text>
      </el-descriptions-item>
      <el-descriptions-item label="文件路径" :span="2">
        <el-text>{{ crawler.file_path || '-' }}</el-text>
      </el-descriptions-item>
      <el-descriptions-item label="描述" :span="2">
        <el-text>{{ crawler.description || '-' }}</el-text>
      </el-descriptions-item>
    </el-descriptions>

    <div class="actions">
      <el-button type="primary" @click="executeCrawler" :disabled="!crawler?.is_active">
        <el-icon><VideoPlay /></el-icon>
        执行爬虫
      </el-button>
      <el-button @click="goToTasks">
        <el-icon><List /></el-icon>
        查看任务历史
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { crawlersApi, type Crawler } from '@/api/crawlers'
import { useAppStore } from '@/store'
import { VideoPlay, List } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const store = useAppStore()

const crawler = ref<Crawler | null>(null)
const loading = ref(false)

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const fetchCrawler = async () => {
  loading.value = true
  try {
    const id = parseInt(route.params.id as string)
    crawler.value = await crawlersApi.get(id)
  } catch (error) {
    console.error('Failed to fetch crawler:', error)
    ElMessage.error('获取爬虫详情失败')
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.back()
}

const executeCrawler = async () => {
  if (!crawler.value) return

  try {
    const result = await store.executeCrawler(crawler.value.id)
    ElMessage.success(`任务已创建: ID ${result.task_id}`)
    router.push(`/tasks/${result.task_id}`)
  } catch (error) {
    console.error('Failed to execute:', error)
  }
}

const goToTasks = () => {
  router.push({ name: 'Tasks', query: { crawler_id: crawler.value?.id } })
}

onMounted(() => {
  fetchCrawler()
})
</script>

<style scoped>
.crawler-detail-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  font-size: 18px;
  font-weight: 500;
}

.crawler-info {
  margin-top: 20px;
}

.command-text {
  font-family: 'Courier New', monospace;
  background-color: #f5f5f5;
  padding: 8px 12px;
  border-radius: 4px;
}

.actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}
</style>

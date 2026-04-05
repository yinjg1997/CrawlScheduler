<template>
  <div id="app">
    <!-- Show login page if not authenticated -->
    <router-view v-if="route.path === '/login'" />

    <!-- Show main app if authenticated -->
    <el-container v-else class="app-container">
      <el-header class="app-header">
        <h1 class="app-title">
          <el-icon><Spider /></el-icon>
          CrawlScheduler
        </h1>
        <div class="header-right">
          <span class="user-info">
            <el-icon><User /></el-icon>
            {{ authStore.user?.username }}
          </span>
          <el-button type="danger" size="small" @click="handleLogout">
            退出
          </el-button>
        </div>
      </el-header>
      <el-container>
        <el-aside width="200px" class="app-aside">
          <el-menu
            :default-active="activeMenu"
            router
            class="el-menu-vertical"
          >
            <el-menu-item index="/projects">
              <el-icon><Folder /></el-icon>
              <span>项目管理</span>
            </el-menu-item>
            <el-menu-item index="/crawlers">
              <el-icon><Monitor /></el-icon>
              <span>爬虫管理</span>
            </el-menu-item>
            <el-menu-item index="/schedules">
              <el-icon><Timer /></el-icon>
              <span>定时任务</span>
            </el-menu-item>
            <el-menu-item index="/tasks">
              <el-icon><List /></el-icon>
              <span>任务列表</span>
            </el-menu-item>
            <el-menu-item v-if="authStore.isSuperuser" index="/users">
              <el-icon><User /></el-icon>
              <span>用户管理</span>
            </el-menu-item>
            <el-menu-item index="/python-environments">
              <el-icon><Setting /></el-icon>
              <span>Python环境</span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        <el-main class="app-main">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/store/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)

// Handle logout
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要退出登录吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    authStore.logout()
    router.push('/login')
  } catch {
    // User cancelled
  }
}

// Check authentication status on mount
onMounted(async () => {
  if (authStore.isAuthenticated && route.path !== '/login') {
    await authStore.checkAuth()
  }
})
</script>

<style scoped>
#app {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.app-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.app-header {
  background-color: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.app-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: 20px;
  font-weight: 500;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 14px;
}

.app-aside {
  background-color: #f5f5f5;
  border-right: 1px solid #e6e6e6;
}

.app-main {
  background-color: #fff;
  padding: 20px;
  overflow-y: auto;
}

.el-menu-vertical {
  border-right: none;
  height: 100%;
}
</style>

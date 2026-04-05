<template>
  <div id="app">
    <!-- Show login page if not authenticated -->
    <router-view v-if="route.path === '/login'" />

    <!-- Show main app if authenticated -->
    <div v-else class="common-layout">
      <el-container>
        <el-aside width="200px" class="app-aside">
          <div class="aside-header">
            <h1 class="app-title">
              <el-icon><Spider /></el-icon>
              CrawlScheduler
            </h1>
          </div>
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
        <el-container>
          <el-header class="app-header">
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
          <el-main class="app-main">
            <router-view />
          </el-main>
        </el-container>
      </el-container>
    </div>
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

<style>
/* Global styles to remove browser defaults */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  width: 100%;
  overflow: hidden;
}

#app {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.common-layout {
  height: 100%;
  width: 100%;
}

.common-layout .el-container {
  height: 100%;
}

.common-layout .el-container:nth-child(2) {
  display: flex;
  flex-direction: column;
}
</style>

<style scoped>
.app-aside {
  background-color: #304156;
  border-right: none;
  display: flex;
  flex-direction: column;
}

.aside-header {
  background-color: #2b3a4d;
  padding: 15px;
  border-bottom: 1px solid #3a4b5c;
  width: 100%;
  text-align: center;
  display: flex;
  justify-content: center;
}

.app-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin: 0 auto;
  padding: 0;
  font-size: 18px;
  font-weight: 500;
  color: #fff;
  width: fit-content;
  min-width: 100%;
}

.app-header {
  background-color: #fff;
  color: #333;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0 20px;
  height: 60px;
  flex-shrink: 0;
  border-bottom: 1px solid #e6e6e6;
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
  color: #606266;
}

.app-main {
  background-color: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}

.el-menu-vertical {
  border-right: none;
  background-color: #304156;
  flex: 1;
  overflow-y: auto;
}

.el-menu-vertical .el-menu-item {
  color: #bfcbd9;
}

.el-menu-vertical .el-menu-item:hover {
  background-color: #263445;
  color: #fff;
}

.el-menu-vertical .el-menu-item.is-active {
  background-color: #409eff;
  color: #fff;
}

.el-menu-vertical .el-menu-item .el-icon {
  color: inherit;
}
</style>

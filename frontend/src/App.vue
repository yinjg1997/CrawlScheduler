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
              <el-icon><Platform /></el-icon>
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
              <el-dropdown trigger="click" @command="handleCommand">
                <div class="user-info">
                  <div class="user-avatar">
                    <el-icon><User /></el-icon>
                  </div>
                  <div class="user-details">
                    <span class="user-name">{{ authStore.user?.username }}</span>
                    <span class="user-role">{{ authStore.user?.is_superuser ? '管理员' : '普通用户' }}</span>
                  </div>
                  <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
                </div>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="logout">
                      <el-icon><Switch /></el-icon>
                      退出登录
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
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
import { ElMessageBox, ElMessage } from 'element-plus'
import { ArrowDown, Switch } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)

// Handle dropdown menu commands
const handleCommand = async (command: string) => {
  if (command === 'logout') {
    await handleLogout()
  }
}

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
  gap: 20px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: transparent;
}

.user-info:hover {
  background-color: #f5f7fa;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 20px;
  flex-shrink: 0;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 80px;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  line-height: 1.2;
}

.user-role {
  font-size: 12px;
  color: #909399;
  line-height: 1.2;
}

.dropdown-icon {
  font-size: 14px;
  color: #909399;
  transition: transform 0.3s ease;
}

.user-info:hover .dropdown-icon {
  transform: rotate(180deg);
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

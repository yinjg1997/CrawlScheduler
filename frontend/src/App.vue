<template>
  <div id="app">
    <el-container class="app-container">
      <el-header class="app-header">
        <div class="header-content">
          <h1 class="app-title">
            <el-icon><Spider /></el-icon>
            CrawlScheduler
          </h1>
          <el-button
            type="primary"
            @click="refreshData"
            :loading="refreshing"
          >
            <el-icon><Refresh /></el-icon>
            刷新
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
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const refreshing = ref(false)

const activeMenu = computed(() => route.path)

const refreshData = () => {
  refreshing.value = true
  setTimeout(() => {
    refreshing.value = false
  }, 500)
}
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
  padding: 0 20px;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.app-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: 20px;
  font-weight: 500;
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

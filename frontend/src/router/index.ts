import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    redirect: '/crawlers'
  },
  {
    path: '/crawlers',
    name: 'Crawlers',
    component: () => import('@/views/Crawlers.vue')
  },
  {
    path: '/crawlers/:id',
    name: 'CrawlerDetail',
    component: () => import('@/views/CrawlerDetail.vue')
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: () => import('@/views/Tasks.vue')
  },
  {
    path: '/tasks/:id',
    name: 'TaskDetail',
    component: () => import('@/views/TaskDetail.vue')
  },
  {
    path: '/schedules',
    name: 'Schedules',
    component: () => import('@/views/Schedules.vue')
  },
  {
    path: '/python-environments',
    name: 'PythonEnvironments',
    component: () => import('@/views/PythonEnvironments.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

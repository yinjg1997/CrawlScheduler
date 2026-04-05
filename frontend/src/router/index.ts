import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    redirect: '/crawlers',
    meta: { requiresAuth: true }
  },
  {
    path: '/crawlers',
    name: 'Crawlers',
    component: () => import('@/views/Crawlers.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/crawlers/:id',
    name: 'CrawlerDetail',
    component: () => import('@/views/CrawlerDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: () => import('@/views/Tasks.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/tasks/:id',
    name: 'TaskDetail',
    component: () => import('@/views/TaskDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/schedules',
    name: 'Schedules',
    component: () => import('@/views/Schedules.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/python-environments',
    name: 'PythonEnvironments',
    component: () => import('@/views/PythonEnvironments.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/users',
    name: 'Users',
    component: () => import('@/views/Users.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard to protect routes
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  const isAuthenticated = authStore.isAuthenticated
  const requiresAuth = to.meta.requiresAuth !== false // Default to true if not specified
  const requiresAdmin = to.meta.requiresAdmin === true // Only true if explicitly set

  if (requiresAuth && !isAuthenticated) {
    // If route requires authentication and user is not logged in, redirect to login
    next('/login')
  } else if (requiresAdmin && !authStore.isSuperuser) {
    // If route requires admin and user is not admin, redirect to home
    next('/')
  } else if (to.path === '/login' && isAuthenticated) {
    // If user is already logged in and tries to access login page, redirect to home
    next('/')
  } else {
    // Otherwise, proceed
    next()
  }
})

export default router

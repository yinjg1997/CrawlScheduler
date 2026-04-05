import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

export interface User {
  id: number
  username: string
  email: string
  is_active: boolean
  is_superuser: boolean
  created_at: string
  updated_at: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!token.value)
  const isSuperuser = computed(() => user.value?.is_superuser || false)

  // Load token from localStorage on store initialization
  const loadToken = () => {
    const savedToken = localStorage.getItem('token')
    const savedUser = localStorage.getItem('user')
    if (savedToken) {
      token.value = savedToken
    }
    if (savedUser) {
      try {
        user.value = JSON.parse(savedUser)
      } catch (e) {
        console.error('Failed to parse saved user:', e)
      }
    }
  }

  // Save token to localStorage
  const saveToken = () => {
    if (token.value) {
      localStorage.setItem('token', token.value)
    } else {
      localStorage.removeItem('token')
    }
  }

  // Save user to localStorage
  const saveUser = () => {
    if (user.value) {
      localStorage.setItem('user', JSON.stringify(user.value))
    } else {
      localStorage.removeItem('user')
    }
  }

  // Login action
  const login = async (username: string, password: string) => {
    loading.value = true
    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Login failed')
      }

      const data = await response.json()
      token.value = data.access_token
      user.value = data.user

      saveToken()
      saveUser()

      ElMessage.success('登录成功')
      return true
    } catch (error: any) {
      console.error('Login error:', error)
      ElMessage.error(error.message || '登录失败')
      return false
    } finally {
      loading.value = false
    }
  }

  // Logout action
  const logout = () => {
    token.value = null
    user.value = null
    saveToken()
    saveUser()
    ElMessage.info('已退出登录')
  }

  // Check authentication status
  const checkAuth = async () => {
    if (!token.value) {
      return false
    }

    try {
      const response = await fetch('/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${token.value}`,
        },
      })

      if (!response.ok) {
        logout()
        return false
      }

      const data = await response.json()
      user.value = data
      saveUser()
      return true
    } catch (error) {
      console.error('Auth check error:', error)
      logout()
      return false
    }
  }

  // Update token (used for token refresh)
  const updateToken = (newToken: string) => {
    token.value = newToken
    saveToken()
  }

  // Initialize store
  loadToken()

  return {
    user,
    token,
    loading,
    isAuthenticated,
    isSuperuser,
    login,
    logout,
    checkAuth,
    updateToken,
  }
})

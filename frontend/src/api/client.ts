import axios, { AxiosInstance, AxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'

// Type for API methods that return data directly
type ApiClient = Omit<AxiosInstance, 'get' | 'post' | 'put' | 'delete' | 'patch'> & {
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T>
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>
  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T>
  patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>
}

const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 30000
}) as ApiClient

// Request interceptor - Add Authorization header
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error: any) => {
    return Promise.reject(error)
  }
)

// Response interceptor - Handle 401 errors
apiClient.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error: any) => {
    // Handle 401 Unauthorized errors
    if (error.response?.status === 401) {
      // Clear token and user from localStorage
      localStorage.removeItem('token')
      localStorage.removeItem('user')

      // Show error message
      ElMessage.error('登录已过期，请重新登录')

      // Redirect to login page
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    } else {
      const message = error.response?.data?.detail || error.message || '请求失败'
      ElMessage.error(message)
    }

    return Promise.reject(error)
  }
)

export default apiClient

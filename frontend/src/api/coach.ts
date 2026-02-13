import axios from 'axios'
import type { DailyAnalysisResponse } from '../types'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 如果需要认证，在这里添加 token
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器（统一错误处理）
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('API Error:', error.response.data)
    } else if (error.request) {
      console.error('Network Error:', error.request)
    } else {
      console.error('Error:', error.message)
    }
    return Promise.reject(error)
  }
)

export const coachApi = {
  /**
   * 获取每日分析
   */
  getDailyAnalysis: async (date?: string): Promise<DailyAnalysisResponse> => {
    const response = await apiClient.get<DailyAnalysisResponse>(
      '/api/coach/daily-analysis',
      {
        params: date ? { target_date: date } : {},
      }
    )
    return response.data
  },

  /**
   * 健康检查
   */
  healthCheck: async (): Promise<{ status: string }> => {
    const response = await apiClient.get('/health')
    return response.data
  },
}

import axios from 'axios'
import type { AnalyzeRequest, AnalyzeResponse } from '../types'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const analyzeETF = (data: AnalyzeRequest): Promise<AnalyzeResponse> => {
  return apiClient.post('/analyze', data)
}

export default apiClient

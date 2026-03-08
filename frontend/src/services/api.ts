import axios from 'axios'
import type {
  AnalyzeRequest,
  AnalyzeResponse,
  BacktestRequest,
  BacktestResponse,
  StrategyParams
} from '../types'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
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

// ETF分析API
export const analyzeETF = (data: AnalyzeRequest): Promise<AnalyzeResponse> => {
  return apiClient.post('/analyze', data)
}

// 回测API
export const runBacktest = (data: BacktestRequest): Promise<BacktestResponse> => {
  return apiClient.post('/backtest', data)
}

// 获取策略参数
export const getStrategyParams = (): Promise<StrategyParams> => {
  return apiClient.get('/strategy/params')
}

// 更新策略参数
export const updateStrategyParams = (params: StrategyParams): Promise<StrategyParams> => {
  return apiClient.post('/strategy/params', params)
}

export default apiClient

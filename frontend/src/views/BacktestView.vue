<template>
  <div class="backtest-view">
    <el-container>
      <el-header>
        <h1>ETF策略回测</h1>
        <div class="header-actions">
          <el-button type="default" @click="goToDashboard">
            <el-icon><ArrowLeft /></el-icon>
            返回分析
          </el-button>
        </div>
      </el-header>

      <el-main>
        <el-row :gutter="20">
          <el-col :span="8">
            <!-- 回测表单 -->
            <BacktestForm :loading="loading" @submit="handleRunBacktest" />
          </el-col>

          <el-col :span="16">
            <div v-if="loading" class="loading-container">
              <el-icon class="is-loading" :size="40">
                <Loading />
              </el-icon>
              <p>正在回测中，请稍候...</p>
              <el-progress
                :percentage="loadingProgress"
                :status="loadingProgress === 100 ? 'success' : undefined"
                style="width: 300px; margin-top: 20px"
              />
            </div>

            <div v-else-if="error" class="error-container">
              <el-result icon="error" :title="error" sub-title="回测失败，请稍后重试">
                <template #extra>
                  <el-button type="primary" @click="error = ''">重新尝试</el-button>
                </template>
              </el-result>
            </div>

            <div v-else-if="result">
              <!-- 绩效指标 -->
              <BacktestMetrics :metrics="result.metrics" />

              <!-- K线图（带交易信号） -->
              <KlineChart
                :klineData="result.klines"
                :signals="result.signals"
              />

              <!-- 权益曲线图 -->
              <BacktestEquityChart
                :equityCurve="result.equity_curve"
                :initialCapital="result.metrics.initial_capital"
              />

              <!-- 回撤分析图 -->
              <BacktestDrawdownChart :equityCurve="result.equity_curve" />

              <!-- 交易记录列表 -->
              <BacktestTradeList :trades="result.trades" />
            </div>

            <div v-else class="placeholder">
              <el-empty description="请输入ETF代码和参数，点击开始回测按钮运行回测">
                <el-button type="primary" @click="loadExample">加载示例</el-button>
              </el-empty>
            </div>
          </el-col>
        </el-row>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import BacktestForm from '../components/backtest/BacktestForm.vue'
import BacktestMetrics from '../components/backtest/BacktestMetrics.vue'
import BacktestEquityChart from '../components/backtest/BacktestEquityChart.vue'
import BacktestDrawdownChart from '../components/backtest/BacktestDrawdownChart.vue'
import BacktestTradeList from '../components/backtest/BacktestTradeList.vue'
import KlineChart from '../components/KlineChart.vue'
import { runBacktest } from '../services/api'
import type { BacktestRequest, BacktestResponse } from '../types'

const router = useRouter()

const loading = ref(false)
const loadingProgress = ref(0)
const error = ref('')
const result = ref<BacktestResponse | null>(null)

const goToDashboard = () => {
  router.push('/')
}

const handleRunBacktest = async (data: BacktestRequest) => {
  loading.value = true
  loadingProgress.value = 0
  error.value = ''
  result.value = null

  // Simulate progress
  const progressInterval = setInterval(() => {
    if (loadingProgress.value < 90) {
      loadingProgress.value += Math.random() * 10
    }
  }, 500)

  try {
    const response = await runBacktest(data)
    loadingProgress.value = 100
    result.value = response
    ElMessage.success(`回测完成！共执行 ${response.metrics.total_trades} 笔交易`)
  } catch (err: any) {
    console.error('Backtest error:', err)
    error.value = err.response?.data?.detail || err.message || '回测失败，请稍后重试'
    ElMessage.error(error.value)
  } finally {
    clearInterval(progressInterval)
    loading.value = false
  }
}

const loadExample = () => {
  // This would load a pre-filled example
  ElMessage.info('请在左侧表单中输入参数并开始回测')
}
</script>

<style scoped>
.backtest-view {
  min-height: 100vh;
  background: #f5f5f5;
}

.el-header {
  background: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 40px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.el-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 500;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.el-main {
  padding: 40px;
}

.loading-container {
  background: white;
  padding: 80px 40px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.loading-container .el-icon {
  color: #409eff;
}

.loading-container p {
  margin-top: 20px;
  font-size: 16px;
  color: #606266;
}

.error-container {
  background: white;
  padding: 40px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.placeholder {
  background: white;
  padding: 100px 40px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}
</style>

<template>
  <div class="app-container">
    <el-container>
      <el-header>
        <h1>ETF量化交易计算器</h1>
      </el-header>
      <el-main>
        <el-row :gutter="20">
          <el-col :span="8">
            <InputForm :loading="loading" @submit="handleAnalyze" />
          </el-col>
          <el-col :span="16">
            <div v-if="loading" class="loading-container">
              <el-icon class="is-loading" :size="40">
                <Loading />
              </el-icon>
              <p>正在分析中，请稍候...</p>
            </div>
            <div v-else-if="error" class="error-container">
              <el-result icon="error" :title="error" sub-title="分析失败，请稍后重试">
                <template #extra>
                  <el-button type="primary" @click="error = ''">重新尝试</el-button>
                </template>
              </el-result>
            </div>
            <div v-else-if="result">
              <ResultCard :data="result" />
              <IndicatorList :data="result" />
            </div>
            <div v-else class="placeholder">
              <el-empty description="请输入ETF代码并点击分析按钮开始分析"></el-empty>
            </div>
          </el-col>
        </el-row>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import InputForm from './components/InputForm.vue'
import ResultCard from './components/ResultCard.vue'
import IndicatorList from './components/IndicatorList.vue'
import { analyzeETF } from './services/api'
import type { AnalyzeResponse, RiskPreference } from './types'

const loading = ref(false)
const error = ref('')
const result = ref<AnalyzeResponse | null>(null)

const handleAnalyze = async (data: {
  etfCode: string
  totalCapital: number
  holdingAmount: number
  currentYield: number
  riskPreference: RiskPreference
}) => {
  loading.value = true
  error.value = ''
  result.value = null

  try {
    const response = await analyzeETF({
      etf_code: data.etfCode,
      risk_preference: data.riskPreference,
      use_cache: true
    })
    result.value = response
    ElMessage.success('分析完成')
  } catch (err: any) {
    console.error('Analysis error:', err)
    error.value = err.response?.data?.detail || err.message || '分析失败，请稍后重试'
    ElMessage.error(error.value)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  background: #f5f5f5;
}

.el-header {
  background: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.el-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 500;
}

.el-main {
  padding: 40px;
}

.placeholder {
  background: white;
  padding: 60px 40px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}
</style>

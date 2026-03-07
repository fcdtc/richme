<template>
  <el-card class="result-card" v-if="data">
    <template #header>
      <div class="card-header">
        <span>{{ data.etf_code }} - {{ data.etf_name }}</span>
        <SignalBadge :signalType="data.signal.signal_type" :strength="data.signal.strength" />
      </div>
    </template>

    <div class="result-content">
      <el-row :gutter="20">
        <el-col :span="12">
          <div class="price-section">
            <div class="price-label">当前价格</div>
            <div class="price-value">¥{{ data.current_price.toFixed(3) }}</div>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="score-section">
            <div class="score-label">综合评分</div>
            <div class="score-value" :class="scoreClass">
              {{ (data.overall_score * 100).toFixed(0) }}分
            </div>
          </div>
        </el-col>
      </el-row>

      <el-divider />

      <div class="signal-details">
        <div class="detail-item">
          <span class="detail-label">信号强度：</span>
          <span class="detail-value">{{ (data.signal.strength * 100).toFixed(0) }}%</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">置信度：</span>
          <span class="detail-value">{{ (data.signal.confidence * 100).toFixed(0) }}%</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">分析时间：</span>
          <span class="detail-value">{{ formatDate(data.timestamp) }}</span>
        </div>
      </div>

      <el-divider />

      <div class="quality-section">
        <div class="quality-title">数据质量</div>
        <div class="quality-indicators">
          <div class="quality-item">
            <span class="quality-label">完整性：</span>
            <el-progress
              :percentage="data.data_quality.completeness * 100"
              :color="getProgressColor(data.data_quality.completeness)"
            />
          </div>
          <div class="quality-item">
            <span class="quality-label">可靠性：</span>
            <el-progress
              :percentage="data.data_quality.reliability * 100"
              :color="getProgressColor(data.data_quality.reliability)"
            />
          </div>
          <div class="quality-item">
            <span class="quality-label">时效性：</span>
            <el-progress
              :percentage="data.data_quality.recency * 100"
              :color="getProgressColor(data.data_quality.recency)"
            />
          </div>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import SignalBadge from './SignalBadge.vue'
import type { AnalyzeResponse } from '../types'

interface Props {
  data: AnalyzeResponse | null
}

defineProps<Props>()

const scoreClass = computed(() => {
  return (props: Props) => {
    if (!props.data) return ''
    const score = props.data.overall_score
    if (score >= 0.7) return 'score-high'
    if (score >= 0.4) return 'score-medium'
    return 'score-low'
  }
})

const formatDate = (timestamp: string) => {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getProgressColor = (value: number) => {
  if (value >= 0.8) return '#67c23a'
  if (value >= 0.6) return '#e6a23c'
  return '#f56c6c'
}
</script>

<style scoped>
.result-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: 500;
}

.result-content {
  padding: 10px 0;
}

.price-section, .score-section {
  text-align: center;
  padding: 10px;
}

.price-label, .score-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.price-value {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
}

.score-value {
  font-size: 32px;
  font-weight: bold;
}

.score-high {
  color: #67c23a;
}

.score-medium {
  color: #e6a23c;
}

.score-low {
  color: #f56c6c;
}

.signal-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.detail-label {
  color: #909399;
}

.detail-value {
  color: #303133;
  font-weight: 500;
}

.quality-section {
  margin-top: 10px;
}

.quality-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 12px;
}

.quality-indicators {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.quality-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.quality-label {
  font-size: 13px;
  color: #909399;
  width: 60px;
  flex-shrink: 0;
}
</style>

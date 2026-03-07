<template>
  <el-card class="position-card" v-if="position">
    <template #header>
      <div class="card-header">
        <span>仓位建议</span>
        <el-tag :type="actionType" size="large">
          {{ actionText }}
        </el-tag>
      </div>
    </template>

    <div class="position-content">
      <!-- 操作建议 -->
      <div class="action-section" v-if="position.action !== 'hold'">
        <el-alert
          :title="actionTitle"
          :type="actionType === 'success' ? 'success' : 'warning'"
          :description="position.reason"
          show-icon
          :closable="false"
        />
      </div>

      <!-- 核心数据 -->
      <el-row :gutter="20" class="core-data">
        <el-col :span="6">
          <div class="data-item">
            <div class="data-label">建议金额</div>
            <div class="data-value" :class="actionClass">
              ¥{{ position.amount.toLocaleString() }}
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="data-item">
            <div class="data-label">建议股数</div>
            <div class="data-value">{{ position.shares.toLocaleString() }}股</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="data-item">
            <div class="data-label">目标仓位</div>
            <div class="data-value">{{ position.percentage }}%</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="data-item">
            <div class="data-label">风险比例</div>
            <div class="data-value">{{ position.risk_percentage }}%</div>
          </div>
        </el-col>
      </el-row>

      <!-- 止损止盈 -->
      <el-divider />
      <div class="price-section">
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="price-item stop-loss">
              <div class="price-label">止损价</div>
              <div class="price-value">¥{{ position.stop_loss_price.toFixed(3) }}</div>
              <div class="price-note">风险金额: ¥{{ position.risk_amount.toLocaleString() }}</div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="price-item take-profit">
              <div class="price-label">止盈价</div>
              <div class="price-value">¥{{ position.take_profit_price.toFixed(3) }}</div>
              <div class="price-note">盈亏比: 1:2</div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 仓位进度 -->
      <el-divider />
      <div class="position-progress">
        <div class="progress-header">
          <span>仓位情况</span>
          <span class="progress-text">
            {{ position.current_position.toLocaleString() }} / {{ position.max_position.toLocaleString() }}
          </span>
        </div>
        <el-progress
          :percentage="positionPercentage"
          :color="progressColor"
          :stroke-width="20"
          :text-inside="true"
        />
        <div class="progress-legend">
          <span class="legend-item">
            <span class="legend-dot current"></span>
            当前持仓: ¥{{ position.current_position.toLocaleString() }}
          </span>
          <span class="legend-item">
            <span class="legend-dot target"></span>
            目标持仓: ¥{{ position.target_position.toLocaleString() }}
          </span>
          <span class="legend-item">
            <span class="legend-dot max"></span>
            最大持仓: ¥{{ position.max_position.toLocaleString() }}
          </span>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PositionRecommendation } from '../types'

interface Props {
  position: PositionRecommendation | null
}

const props = defineProps<Props>()

const actionType = computed(() => {
  if (!props.position) return 'info'
  switch (props.position.action) {
    case 'buy': return 'success'
    case 'sell': return 'warning'
    default: return 'info'
  }
})

const actionText = computed(() => {
  if (!props.position) return ''
  switch (props.position.action) {
    case 'buy': return '建议买入'
    case 'sell': return '建议卖出'
    default: return '建议持有'
  }
})

const actionTitle = computed(() => {
  if (!props.position) return ''
  const action = props.position.action === 'buy' ? '买入' : '卖出'
  return `建议${action} ¥${props.position.amount.toLocaleString()} (${props.position.shares}股)`
})

const actionClass = computed(() => {
  if (!props.position) return ''
  return props.position.action === 'buy' ? 'text-success' : props.position.action === 'sell' ? 'text-warning' : ''
})

const positionPercentage = computed(() => {
  if (!props.position || props.position.max_position === 0) return 0
  return Math.round((props.position.target_position / props.position.max_position) * 100)
})

const progressColor = computed(() => {
  const pct = positionPercentage.value
  if (pct < 30) return '#67c23a'
  if (pct < 60) return '#409eff'
  if (pct < 80) return '#e6a23c'
  return '#f56c6c'
})
</script>

<style scoped>
.position-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: 500;
}

.position-content {
  padding: 10px 0;
}

.action-section {
  margin-bottom: 20px;
}

.core-data {
  text-align: center;
}

.data-item {
  padding: 15px 10px;
  background: #f5f7fa;
  border-radius: 8px;
}

.data-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.data-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.data-value.text-success {
  color: #67c23a;
}

.data-value.text-warning {
  color: #e6a23c;
}

.price-section {
  margin: 10px 0;
}

.price-item {
  padding: 20px;
  border-radius: 8px;
  text-align: center;
}

.price-item.stop-loss {
  background: linear-gradient(135deg, #fff5f5 0%, #fff 100%);
  border: 1px solid #fde2e2;
}

.price-item.take-profit {
  background: linear-gradient(135deg, #f0f9eb 0%, #fff 100%);
  border: 1px solid #e1f3d8;
}

.price-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.price-value {
  font-size: 28px;
  font-weight: bold;
}

.stop-loss .price-value {
  color: #f56c6c;
}

.take-profit .price-value {
  color: #67c23a;
}

.price-note {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}

.position-progress {
  padding: 10px 0;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
  font-size: 14px;
  font-weight: 500;
}

.progress-text {
  color: #909399;
}

.progress-legend {
  display: flex;
  justify-content: space-around;
  margin-top: 15px;
  font-size: 13px;
  color: #606266;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.legend-dot.current {
  background: #409eff;
}

.legend-dot.target {
  background: #67c23a;
}

.legend-dot.max {
  background: #e6a23c;
}
</style>

<template>
  <el-card class="position-card" v-if="position">
    <template #header>
      <div class="card-header">
        <span>交易策略建议</span>
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
      <div class="action-section" v-else>
        <el-alert
          title="持有不动"
          type="info"
          :description="position.reason"
          show-icon
          :closable="false"
        />
      </div>

      <!-- 量化依据 -->
      <div class="quant-section">
        <div class="quant-title">量化依据</div>
        <el-row :gutter="15">
          <el-col :span="6">
            <div class="quant-item">
              <div class="quant-label">综合得分</div>
              <div class="quant-value" :class="scoreClass">
                {{ position.signal_score > 0 ? '+' : '' }}{{ position.signal_score.toFixed(2) }}
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="quant-item">
              <div class="quant-label">趋势方向</div>
              <div class="quant-value" :class="trendClass">
                {{ trendText }}
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="quant-item">
              <div class="quant-label">趋势强度</div>
              <div class="quant-value">
                {{ (position.trend_strength * 100).toFixed(0) }}%
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="quant-item">
              <div class="quant-label">交易金额</div>
              <div class="quant-value amount">
                ¥{{ position.amount.toLocaleString() }}
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 核心数据 -->
      <el-divider />
      <el-row :gutter="20" class="core-data">
        <el-col :span="6">
          <div class="data-item">
            <div class="data-label">目标仓位</div>
            <div class="data-value">{{ position.percentage }}%</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="data-item">
            <div class="data-label">当前持仓</div>
            <div class="data-value">¥{{ position.current_position.toLocaleString() }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="data-item">
            <div class="data-label">目标持仓</div>
            <div class="data-value">¥{{ position.target_position.toLocaleString() }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="data-item">
            <div class="data-label">最大持仓</div>
            <div class="data-value">¥{{ position.max_position.toLocaleString() }}</div>
          </div>
        </el-col>
      </el-row>

      <!-- 支撑阻力位 -->
      <el-divider />
      <div class="price-section">
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="price-item support">
              <div class="price-label">支撑位</div>
              <div class="price-value">¥{{ position.support_level.toFixed(3) }}</div>
              <div class="price-note">下跌保护参考</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="price-item stop-loss">
              <div class="price-label">止损价</div>
              <div class="price-value">¥{{ position.stop_loss_price.toFixed(3) }}</div>
              <div class="price-note">风险: ¥{{ position.risk_amount.toLocaleString() }}</div>
            </div>
          </el-col>
          <el-col :span="8">
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
            当前: {{ (position.current_position / maxCapital * 100).toFixed(1) }}%
          </span>
          <span class="legend-item">
            <span class="legend-dot target"></span>
            目标: {{ position.percentage }}%
          </span>
          <span class="legend-item">
            <span class="legend-dot max"></span>
            上限: {{ maxPositionPct }}%
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
  maxCapital?: number
}

const props = withDefaults(defineProps<Props>(), {
  maxCapital: 100000
})

const actionType = computed(() => {
  if (!props.position) return 'info'
  switch (props.position.action) {
    case 'buy': return 'danger'    // 买入 - 红色
    case 'sell': return 'success'  // 卖出 - 绿色
    default: return 'info'
  }
})

const actionText = computed(() => {
  if (!props.position) return ''
  switch (props.position.action) {
    case 'buy': return '建议加仓'
    case 'sell': return '建议减仓'
    default: return '持有不动'
  }
})

const actionTitle = computed(() => {
  if (!props.position) return ''
  const action = props.position.action === 'buy' ? '加仓' : '减仓'
  return `建议${action} ¥${props.position.amount.toLocaleString()}`
})

const scoreClass = computed(() => {
  if (!props.position) return ''
  if (props.position.signal_score > 0.3) return 'score-bullish'
  if (props.position.signal_score < -0.3) return 'score-bearish'
  return 'score-neutral'
})

const trendText = computed(() => {
  if (!props.position) return ''
  switch (props.position.trend_direction) {
    case 'up': return '上涨'
    case 'down': return '下跌'
    default: return '震荡'
  }
})

const trendClass = computed(() => {
  if (!props.position) return ''
  switch (props.position.trend_direction) {
    case 'up': return 'trend-up'
    case 'down': return 'trend-down'
    default: return 'trend-neutral'
  }
})

const positionPercentage = computed(() => {
  if (!props.position || props.position.max_position === 0) return 0
  return Math.min(100, Math.round((props.position.target_position / props.position.max_position) * 100))
})

const maxPositionPct = computed(() => {
  if (!props.position) return '50'
  return ((props.position.max_position / props.maxCapital) * 100).toFixed(0)
})

const progressColor = computed(() => {
  const pct = positionPercentage.value
  if (pct < 30) return '#26a69a'  // 低仓位 - 绿色
  if (pct < 60) return '#409eff'
  if (pct < 80) return '#e6a23c'
  return '#ef5350'  // 高仓位 - 红色
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

.quant-section {
  margin-top: 15px;
}

.quant-title {
  font-size: 14px;
  font-weight: 500;
  color: #606266;
  margin-bottom: 12px;
}

.quant-item {
  padding: 12px 10px;
  background: #f5f7fa;
  border-radius: 6px;
  text-align: center;
}

.quant-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
}

.quant-value {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.quant-value.amount {
  color: #409eff;
}

.quant-value.score-bullish {
  color: #ef5350;  /* 多头 - 红色 */
}

.quant-value.score-bearish {
  color: #26a69a;  /* 空头 - 绿色 */
}

.quant-value.score-neutral {
  color: #909399;
}

.quant-value.trend-up {
  color: #ef5350;  /* 上涨 - 红色 */
}

.quant-value.trend-down {
  color: #26a69a;  /* 下跌 - 绿色 */
}

.quant-value.trend-neutral {
  color: #909399;
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
  font-size: 20px;
  font-weight: bold;
  color: #303133;
}

.price-section {
  margin: 10px 0;
}

.price-item {
  padding: 15px;
  border-radius: 8px;
  text-align: center;
}

.price-item.support {
  background: linear-gradient(135deg, #f0f9eb 0%, #fff 100%);
  border: 1px solid #e1f3d8;
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
  font-size: 24px;
  font-weight: bold;
}

.support .price-value {
  color: #409eff;
}

.stop-loss .price-value {
  color: #26a69a;  /* 止损 - 绿色 */
}

.take-profit .price-value {
  color: #ef5350;  /* 止盈 - 红色 */
}

.price-note {
  font-size: 12px;
  color: #909399;
  margin-top: 6px;
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
  background: #ef5350;  /* 目标仓位 - 红色 */
}

.legend-dot.max {
  background: #e6a23c;
}
</style>

<template>
  <el-row :gutter="20" v-if="metrics">
    <el-col :span="6">
      <el-card class="metric-card" shadow="hover">
        <div class="metric-content">
          <div class="metric-icon" :style="{ background: returnColor }">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="metric-info">
            <div class="metric-label">总收益率</div>
            <div class="metric-value" :style="{ color: returnColor }">
              {{ (metrics.total_return * 100).toFixed(2) }}%
            </div>
          </div>
        </div>
      </el-card>
    </el-col>

    <el-col :span="6">
      <el-card class="metric-card" shadow="hover">
        <div class="metric-content">
          <div class="metric-icon" style="background: #67c23a">
            <el-icon><DataAnalysis /></el-icon>
          </div>
          <div class="metric-info">
            <div class="metric-label">年化收益率</div>
            <div class="metric-value" style="color: #67c23a">
              {{ (metrics.annualized_return * 100).toFixed(2) }}%
            </div>
          </div>
        </div>
      </el-card>
    </el-col>

    <el-col :span="6">
      <el-card class="metric-card" shadow="hover">
        <div class="metric-content">
          <div class="metric-icon" style="background: #f56c6c">
            <el-icon><Bottom /></el-icon>
          </div>
          <div class="metric-info">
            <div class="metric-label">最大回撤</div>
            <div class="metric-value" style="color: #f56c6c">
              {{ (metrics.max_drawdown * 100).toFixed(2) }}%
            </div>
          </div>
        </div>
      </el-card>
    </el-col>

    <el-col :span="6">
      <el-card class="metric-card" shadow="hover">
        <div class="metric-content">
          <div class="metric-icon" style="background: #e6a23c">
            <el-icon><ScaleToOriginal /></el-icon>
          </div>
          <div class="metric-info">
            <div class="metric-label">夏普比率</div>
            <div class="metric-value" :style="{ color: sharpeColor }">
              {{ metrics.sharpe_ratio.toFixed(2) }}
            </div>
          </div>
        </div>
      </el-card>
    </el-col>
  </el-row>

  <el-row :gutter="20" v-if="metrics" style="margin-top: 20px">
    <el-col :span="6">
      <el-card class="metric-card" shadow="hover">
        <div class="metric-content">
          <div class="metric-icon" style="background: #409eff">
            <el-icon><DocumentChecked /></el-icon>
          </div>
          <div class="metric-info">
            <div class="metric-label">交易次数</div>
            <div class="metric-value">{{ metrics.total_trades }}</div>
          </div>
        </div>
      </el-card>
    </el-col>

    <el-col :span="6">
      <el-card class="metric-card" shadow="hover">
        <div class="metric-content">
          <div class="metric-icon" :style="{ background: winRateColor }">
            <el-icon><Trophy /></el-icon>
          </div>
          <div class="metric-info">
            <div class="metric-label">胜率</div>
            <div class="metric-value" :style="{ color: winRateColor }">
              {{ (metrics.win_rate * 100).toFixed(2) }}%
            </div>
          </div>
        </div>
      </el-card>
    </el-col>

    <el-col :span="6">
      <el-card class="metric-card" shadow="hover">
        <div class="metric-content">
          <div class="metric-icon" style="background: #909399">
            <el-icon><Coin /></el-icon>
          </div>
          <div class="metric-info">
            <div class="metric-label">盈利因子</div>
            <div class="metric-value">{{ metrics.profit_factor.toFixed(2) }}</div>
          </div>
        </div>
      </el-card>
    </el-col>

    <el-col :span="6">
      <el-card class="metric-card" shadow="hover">
        <div class="metric-content">
          <div class="metric-icon" style="background: #a855f7">
            <el-icon><Wallet /></el-icon>
          </div>
          <div class="metric-info">
            <div class="metric-label">最终资金</div>
            <div class="metric-value" style="color: #a855f7">
              ¥{{ metrics.final_capital.toFixed(2) }}
            </div>
          </div>
        </div>
      </el-card>
    </el-col>
  </el-row>

  <el-card class="detail-card" v-if="metrics" shadow="hover" style="margin-top: 20px">
    <template #header>
      <span>详细信息</span>
    </template>
    <el-row :gutter="20">
      <el-col :span="12">
        <div class="detail-item">
          <span class="detail-label">初始资金：</span>
          <span class="detail-value">¥{{ metrics.initial_capital.toFixed(2) }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">平均盈利：</span>
          <span class="detail-value" style="color: #67c23a">¥{{ metrics.avg_win.toFixed(2) }}</span>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="detail-item">
          <span class="detail-label">平均亏损：</span>
          <span class="detail-value" style="color: #f56c6c">¥{{ metrics.avg_loss.toFixed(2) }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">盈亏比：</span>
          <span class="detail-value">{{ (metrics.avg_win / Math.abs(metrics.avg_loss)).toFixed(2) }}</span>
        </div>
      </el-col>
    </el-row>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  TrendCharts,
  DataAnalysis,
  Bottom,
  ScaleToOriginal,
  DocumentChecked,
  Trophy,
  Coin,
  Wallet
} from '@element-plus/icons-vue'
import type { BacktestMetrics } from '../../types'

interface Props {
  metrics: BacktestMetrics | null
}

const props = defineProps<Props>()

const returnColor = computed(() => {
  if (!props.metrics) return '#909399'
  return props.metrics.total_return >= 0 ? '#67c23a' : '#f56c6c'
})

const sharpeColor = computed(() => {
  if (!props.metrics) return '#909399'
  if (props.metrics.sharpe_ratio >= 2) return '#67c23a'
  if (props.metrics.sharpe_ratio >= 1) return '#e6a23c'
  return '#f56c6c'
})

const winRateColor = computed(() => {
  if (!props.metrics) return '#909399'
  if (props.metrics.win_rate >= 0.6) return '#67c23a'
  if (props.metrics.win_rate >= 0.5) return '#e6a23c'
  return '#f56c6c'
})
</script>

<style scoped>
.metric-card {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.metric-content {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 10px;
}

.metric-icon {
  width: 50px;
  height: 50px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
  flex-shrink: 0;
}

.metric-info {
  flex: 1;
}

.metric-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.detail-card {
  border-radius: 8px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-label {
  font-size: 14px;
  color: #909399;
}

.detail-value {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}
</style>

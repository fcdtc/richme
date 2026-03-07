<template>
  <el-card class="indicator-list-card" v-if="data">
    <template #header>
      <div class="card-header">
        <span>技术指标分析</span>
      </div>
    </template>

    <div class="indicator-content">
      <el-collapse v-model="activeNames">
        <!-- 移动平均线 -->
        <el-collapse-item title="移动平均线 (MA)" name="ma">
          <div class="indicator-section">
            <div class="indicator-row">
              <span class="indicator-label">MA5:</span>
              <span class="indicator-value">{{ data.indicators.ma5.value.toFixed(3) }}</span>
              <el-tag :type="getSignalType(data.indicators.ma5.signal)" size="small">
                {{ getSignalText(data.indicators.ma5.signal) }}
              </el-tag>
            </div>
            <div class="indicator-row">
              <span class="indicator-label">MA10:</span>
              <span class="indicator-value">{{ data.indicators.ma10.value.toFixed(3) }}</span>
              <el-tag :type="getSignalType(data.indicators.ma10.signal)" size="small">
                {{ getSignalText(data.indicators.ma10.signal) }}
              </el-tag>
            </div>
            <div class="indicator-row">
              <span class="indicator-label">MA20:</span>
              <span class="indicator-value">{{ data.indicators.ma20.value.toFixed(3) }}</span>
              <el-tag :type="getSignalType(data.indicators.ma20.signal)" size="small">
                {{ getSignalText(data.indicators.ma20.signal) }}
              </el-tag>
            </div>
            <div class="indicator-row">
              <span class="indicator-label">MA60:</span>
              <span class="indicator-value">{{ data.indicators.ma60.value.toFixed(3) }}</span>
              <el-tag :type="getSignalType(data.indicators.ma60.signal)" size="small">
                {{ getSignalText(data.indicators.ma60.signal) }}
              </el-tag>
            </div>
          </div>
        </el-collapse-item>

        <!-- RSI -->
        <el-collapse-item title="相对强弱指标 (RSI)" name="rsi">
          <div class="indicator-section">
            <div class="indicator-row">
              <span class="indicator-label">RSI:</span>
              <span class="indicator-value">{{ data.indicators.rsi.value.toFixed(2) }}</span>
              <el-tag :type="getSignalType(data.indicators.rsi.signal)" size="small">
                {{ getSignalText(data.indicators.rsi.signal) }}
              </el-tag>
            </div>
            <div class="indicator-interpretation">
              {{ data.indicators.rsi.interpretation }}
            </div>
          </div>
        </el-collapse-item>

        <!-- MACD -->
        <el-collapse-item title="指数平滑异同移动平均线 (MACD)" name="macd">
          <div class="indicator-section">
            <div class="indicator-row">
              <span class="indicator-label">MACD:</span>
              <span class="indicator-value">{{ data.indicators.macd.macd.value.toFixed(6) }}</span>
              <el-tag :type="getSignalType(data.indicators.macd.macd.signal)" size="small">
                {{ getSignalText(data.indicators.macd.macd.signal) }}
              </el-tag>
            </div>
            <div class="indicator-row">
              <span class="indicator-label">Signal:</span>
              <span class="indicator-value">{{ data.indicators.macd.signal.value.toFixed(6) }}</span>
              <el-tag :type="getSignalType(data.indicators.macd.signal.signal)" size="small">
                {{ getSignalText(data.indicators.macd.signal.signal) }}
              </el-tag>
            </div>
            <div class="indicator-row">
              <span class="indicator-label">Histogram:</span>
              <span class="indicator-value">{{ data.indicators.macd.histogram.value.toFixed(6) }}</span>
              <el-tag :type="getSignalType(data.indicators.macd.histogram.signal)" size="small">
                {{ getSignalText(data.indicators.macd.histogram.signal) }}
              </el-tag>
            </div>
          </div>
        </el-collapse-item>

        <!-- KDJ -->
        <el-collapse-item title="随机指标 (KDJ)" name="kdj">
          <div class="indicator-section">
            <div class="indicator-row">
              <span class="indicator-label">K:</span>
              <span class="indicator-value">{{ data.indicators.kdj.k.value.toFixed(2) }}</span>
              <el-tag :type="getSignalType(data.indicators.kdj.k.signal)" size="small">
                {{ getSignalText(data.indicators.kdj.k.signal) }}
              </el-tag>
            </div>
            <div class="indicator-row">
              <span class="indicator-label">D:</span>
              <span class="indicator-value">{{ data.indicators.kdj.d.value.toFixed(2) }}</span>
              <el-tag :type="getSignalType(data.indicators.kdj.d.signal)" size="small">
                {{ getSignalText(data.indicators.kdj.d.signal) }}
              </el-tag>
            </div>
            <div class="indicator-row">
              <span class="indicator-label">J:</span>
              <span class="indicator-value">{{ data.indicators.kdj.j.value.toFixed(2) }}</span>
              <el-tag :type="getSignalType(data.indicators.kdj.j.signal)" size="small">
                {{ getSignalText(data.indicators.kdj.j.signal) }}
              </el-tag>
            </div>
          </div>
        </el-collapse-item>

        <!-- 布林带 -->
        <el-collapse-item title="布林带 (Bollinger)" name="bollinger">
          <div class="indicator-section">
            <div class="indicator-row">
              <span class="indicator-label">上轨:</span>
              <span class="indicator-value">{{ data.indicators.bollinger.upper.toFixed(3) }}</span>
            </div>
            <div class="indicator-row">
              <span class="indicator-label">中轨:</span>
              <span class="indicator-value">{{ data.indicators.bollinger.middle.toFixed(3) }}</span>
            </div>
            <div class="indicator-row">
              <span class="indicator-label">下轨:</span>
              <span class="indicator-value">{{ data.indicators.bollinger.lower.toFixed(3) }}</span>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>

      <el-divider />

      <div class="analysis-section">
        <div class="section-title">综合分析</div>
        <div class="analysis-list">
          <div
            v-for="(item, index) in data.analysis"
            :key="index"
            class="analysis-item"
          >
            <div class="analysis-header">
              <span class="analysis-indicator">{{ item.indicator }}</span>
              <span class="analysis-value">{{ item.value.toFixed(3) }}</span>
              <el-tag :type="getSignalType(item.signal)" size="small">
                {{ getSignalText(item.signal) }}
              </el-tag>
            </div>
            <div class="analysis-interpretation">
              {{ item.interpretation }}
            </div>
            <div class="analysis-weight">
              权重: {{ (item.weight * 100).toFixed(0) }}%
            </div>
          </div>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { AnalyzeResponse } from '../types'

interface Props {
  data: AnalyzeResponse | null
}

defineProps<Props>()

const activeNames = ref(['ma', 'rsi', 'macd'])

const getSignalType = (signal: 'bullish' | 'bearish' | 'neutral') => {
  switch (signal) {
    case 'bullish':
      return 'success'
    case 'bearish':
      return 'danger'
    case 'neutral':
      return 'info'
    default:
      return 'info'
  }
}

const getSignalText = (signal: 'bullish' | 'bearish' | 'neutral') => {
  switch (signal) {
    case 'bullish':
      return '多头'
    case 'bearish':
      return '空头'
    case 'neutral':
      return '中性'
    default:
      return '未知'
  }
}
</script>

<style scoped>
.indicator-list-card {
  margin-bottom: 20px;
}

.card-header {
  font-size: 18px;
  font-weight: 500;
}

.indicator-content {
  padding: 10px 0;
}

.indicator-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.indicator-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.indicator-label {
  font-weight: 500;
  color: #303133;
  min-width: 80px;
}

.indicator-value {
  color: #409eff;
  font-family: monospace;
  font-size: 14px;
  flex: 1;
  text-align: right;
  margin-right: 12px;
}

.indicator-interpretation {
  font-size: 13px;
  color: #909399;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
  line-height: 1.6;
}

.section-title {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 16px;
  color: #303133;
}

.analysis-section {
  margin-top: 20px;
}

.analysis-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.analysis-item {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  border-left: 3px solid #409eff;
}

.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.analysis-indicator {
  font-weight: 500;
  color: #303133;
  font-size: 14px;
}

.analysis-value {
  color: #409eff;
  font-family: monospace;
  font-size: 14px;
}

.analysis-interpretation {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 6px;
}

.analysis-weight {
  font-size: 12px;
  color: #909399;
  text-align: right;
}
</style>

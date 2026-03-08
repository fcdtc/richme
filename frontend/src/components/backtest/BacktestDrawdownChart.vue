<template>
  <el-card class="drawdown-chart-card" v-if="equityCurve.length > 0">
    <template #header>
      <div class="card-header">
        <span>回撤分析</span>
        <el-tag :type="maxDrawdownTagType" size="small">
          最大回撤: {{ (maxDrawdown * 100).toFixed(2) }}%
        </el-tag>
      </div>
    </template>

    <div class="chart-container">
      <v-chart
        :option="chartOption"
        :autoresize="true"
        style="height: 300px; width: 100%"
      />
    </div>

    <div class="drawdown-stats" v-if="drawdownStats">
      <el-row :gutter="20">
        <el-col :span="8">
          <div class="stat-item">
            <div class="stat-label">平均回撤</div>
            <div class="stat-value">{{ drawdownStats.avg.toFixed(2) }}%</div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="stat-item">
            <div class="stat-label">回撤次数</div>
            <div class="stat-value">{{ drawdownStats.count }}</div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="stat-item">
            <div class="stat-label">平均恢复周期</div>
            <div class="stat-value">{{ drawdownStats.avgRecoveryDays }}天</div>
          </div>
        </el-col>
      </el-row>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DataZoomComponent
} from 'echarts/components'
import type { EquityPoint } from '../../types'

use([
  CanvasRenderer,
  BarChart,
  LineChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DataZoomComponent
])

interface Props {
  equityCurve: EquityPoint[]
}

const props = defineProps<Props>()

const maxDrawdown = computed(() => {
  if (!props.equityCurve.length) return 0
  return Math.min(...props.equityCurve.map(e => e.drawdown))
})

const maxDrawdownTagType = computed(() => {
  if (Math.abs(maxDrawdown.value) < 0.05) return 'success'
  if (Math.abs(maxDrawdown.value) < 0.1) return 'warning'
  return 'danger'
})

const drawdownStats = computed(() => {
  if (!props.equityCurve.length) return null

  const drawdowns = props.equityCurve.map(e => e.drawdown)
  const negativeDrawdowns = drawdowns.filter(d => d < 0)

  let count = 0
  let totalRecoveryDays = 0
  let inDrawdown = false
  let drawdownStart = 0

  for (let i = 0; i < drawdowns.length; i++) {
    if (drawdowns[i] < 0 && !inDrawdown) {
      inDrawdown = true
      drawdownStart = i
      count++
    } else if (drawdowns[i] >= 0 && inDrawdown) {
      inDrawdown = false
      totalRecoveryDays += i - drawdownStart
    }
  }

  const avg = negativeDrawdowns.length > 0
    ? negativeDrawdowns.reduce((sum, d) => sum + d, 0) / negativeDrawdowns.length * 100
    : 0

  return {
    avg: Math.abs(avg),
    count,
    avgRecoveryDays: count > 0 ? Math.round(totalRecoveryDays / count) : 0
  }
})

const chartOption = computed(() => {
  if (!props.equityCurve.length) return {}

  const dates = props.equityCurve.map(e => e.date)
  const drawdowns = props.equityCurve.map(e => e.drawdown * 100)
  const colors = drawdowns.map(d => d < 0 ? '#f56c6c' : '#67c23a')

  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#ddd',
      borderWidth: 1,
      textStyle: { color: '#333' },
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params: any) => {
        const data = params[0]
        const idx = data.dataIndex
        return `
          <div style="padding: 10px;">
            <div style="font-weight: bold; margin-bottom: 8px;">${dates[idx]}</div>
            <div>回撤: <span style="color: ${drawdowns[idx] < 0 ? '#f56c6c' : '#67c23a'}; font-weight: bold;">${drawdowns[idx].toFixed(2)}%</span></div>
          </div>
        `
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: true,
      axisLine: { lineStyle: { color: '#e0e0e0' } },
      axisLabel: { color: '#909399' }
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLine: { show: false },
      axisLabel: {
        color: '#909399',
        formatter: '{value}%'
      },
      splitLine: { lineStyle: { color: '#f0f0f0', type: 'dashed' } }
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        type: 'slider',
        bottom: '5%',
        start: 0,
        end: 100,
        height: 25,
        borderColor: 'transparent',
        fillerColor: 'rgba(245, 108, 108, 0.2)',
        handleSize: '80%',
        showDetail: false
      }
    ],
    series: [
      {
        name: '回撤',
        type: 'bar',
        data: drawdowns.map((d, i) => ({
          value: d,
          itemStyle: { color: colors[i] }
        })),
        barWidth: '60%',
        markLine: {
          data: [
            {
              type: 'average',
              name: '平均线',
              lineStyle: {
                color: '#909399',
                type: 'dashed',
                width: 2
              }
            },
            {
              yAxis: 0,
              name: '零轴',
              lineStyle: {
                color: '#409eff',
                width: 1
              }
            }
          ]
        }
      }
    ]
  }
})
</script>

<style scoped>
.drawdown-chart-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: 500;
}

.chart-container {
  padding: 10px 0;
}

.drawdown-stats {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
}

.stat-item {
  text-align: center;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
}
</style>

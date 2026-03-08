<template>
  <el-card class="equity-chart-card" v-if="equityCurve.length > 0">
    <template #header>
      <div class="card-header">
        <span>权益曲线</span>
        <el-radio-group v-model="chartType" size="small">
          <el-radio-button label="value">资金</el-radio-button>
          <el-radio-button label="drawdown">回撤</el-radio-button>
        </el-radio-group>
      </div>
    </template>

    <div class="chart-container">
      <v-chart
        :option="chartOption"
        :autoresize="true"
        style="height: 400px; width: 100%"
      />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DataZoomComponent,
  MarkAreaComponent
} from 'echarts/components'
import type { EquityPoint } from '../../types'

use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DataZoomComponent,
  MarkAreaComponent
])

interface Props {
  equityCurve: EquityPoint[]
  initialCapital?: number
}

const props = withDefaults(defineProps<Props>(), {
  initialCapital: 0
})

const chartType = ref<'value' | 'drawdown'>('value')

const chartOption = computed(() => {
  if (!props.equityCurve.length) return {}

  const dates = props.equityCurve.map(e => e.date)
  const values = props.equityCurve.map(e => e.value)
  const drawdowns = props.equityCurve.map(e => e.drawdown * 100)

  if (chartType.value === 'value') {
    return {
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#ddd',
        borderWidth: 1,
        textStyle: { color: '#333' },
        formatter: (params: any) => {
          const data = params[0]
          const idx = data.dataIndex
          const point = props.equityCurve[idx]
          const returnPct = ((point.value - props.initialCapital) / props.initialCapital * 100).toFixed(2)
          return `
            <div style="padding: 10px;">
              <div style="font-weight: bold; margin-bottom: 8px;">${point.date}</div>
              <div>资金: <span style="color: #409eff; font-weight: bold;">¥${point.value.toFixed(2)}</span></div>
              <div>收益率: <span style="color: ${returnPct >= 0 ? '#67c23a' : '#f56c6c'};">${returnPct}%</span></div>
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
        boundaryGap: false,
        axisLine: { lineStyle: { color: '#e0e0e0' } },
        axisLabel: { color: '#909399' }
      },
      yAxis: {
        type: 'value',
        scale: true,
        axisLine: { show: false },
        axisLabel: { color: '#909399' },
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
          fillerColor: 'rgba(64, 158, 255, 0.2)',
          handleSize: '80%',
          showDetail: false
        }
      ],
      series: [
        {
          name: '权益',
          type: 'line',
          data: values,
          smooth: true,
          symbol: 'none',
          lineStyle: {
            width: 2,
            color: '#409eff'
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
                { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
              ]
            }
          },
          markPoint: {
            data: [
              { type: 'max', name: '最高点' },
              { type: 'min', name: '最低点' }
            ],
            symbolSize: 50,
            label: {
              formatter: '¥{c}'
            }
          },
          markLine: {
            data: [
              {
                type: 'average',
                name: '平均线',
                lineStyle: {
                  color: '#909399',
                  type: 'dashed'
                }
              }
            ]
          }
        }
      ]
    }
  } else {
    // Drawdown chart
    return {
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#ddd',
        borderWidth: 1,
        textStyle: { color: '#333' },
        formatter: (params: any) => {
          const data = params[0]
          const idx = data.dataIndex
          const point = props.equityCurve[idx]
          return `
            <div style="padding: 10px;">
              <div style="font-weight: bold; margin-bottom: 8px;">${point.date}</div>
              <div>回撤: <span style="color: #f56c6c; font-weight: bold;">${point.drawdown < 0 ? (point.drawdown * 100).toFixed(2) : '0.00'}%</span></div>
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
        boundaryGap: false,
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
          type: 'line',
          data: drawdowns,
          smooth: true,
          symbol: 'none',
          lineStyle: {
            width: 2,
            color: '#f56c6c'
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(245, 108, 108, 0.3)' },
                { offset: 1, color: 'rgba(245, 108, 108, 0.05)' }
              ]
            }
          },
          markPoint: {
            data: [
              { type: 'min', name: '最大回撤' }
            ],
            symbolSize: 50,
            label: {
              formatter: '{c}%'
            }
          }
        }
      ]
    }
  }
})
</script>

<style scoped>
.equity-chart-card {
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
</style>

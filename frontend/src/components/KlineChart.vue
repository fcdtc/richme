<template>
  <el-card class="kline-card" v-if="klineData && klineData.klines.length > 0">
    <template #header>
      <div class="card-header">
        <span>K线图 - {{ klineData.period }}</span>
        <div class="chart-controls">
          <el-radio-group v-model="chartType" size="small">
            <el-radio-button label="candlestick">K线</el-radio-button>
            <el-radio-button label="line">折线</el-radio-button>
          </el-radio-group>
        </div>
      </div>
    </template>

    <div class="chart-container" ref="chartContainer">
      <v-chart
        :option="chartOption"
        :autoresize="true"
        style="height: 400px; width: 100%"
      />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { CandlestickChart, LineChart, BarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent
} from 'echarts/components'
import type { KlineData } from '../types'

// 注册ECharts组件
use([
  CanvasRenderer,
  CandlestickChart,
  LineChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent
])

interface Props {
  klineData: KlineData | null
  currentPrice?: number
  signals?: Array<{ date: string; type: 'buy' | 'sell'; price?: number }>
}

const props = withDefaults(defineProps<Props>(), {
  currentPrice: 0,
  signals: () => []
})

const chartType = ref<'candlestick' | 'line'>('candlestick')

// 处理K线数据
const chartOption = computed(() => {
  if (!props.klineData || !props.klineData.klines.length) {
    return {}
  }

  const klines = props.klineData.klines
  const dates = klines.map(k => k.date)
  const ohlc = klines.map(k => [k.open, k.close, k.low, k.high])
  const volumes = klines.map(k => k.volume)
  const ma5 = klines.map(k => k.ma5)
  const ma10 = klines.map(k => k.ma10)
  const ma30 = klines.map(k => k.ma30)

  if (chartType.value === 'candlestick') {
    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        borderColor: '#ddd',
        borderWidth: 1,
        textStyle: { color: '#333' },
        formatter: function(params: any) {
          const data = params[0]
          const idx = data.dataIndex
          const k = klines[idx]
          const change = ((k.close - k.open) / k.open * 100).toFixed(2)
          const color = k.close >= k.open ? '#f56c6c' : '#67c23a'
          return `
            <div style="padding: 8px;">
              <div style="font-weight: bold; margin-bottom: 8px;">${k.date}</div>
              <div>开盘: <span style="color: #409eff;">${k.open.toFixed(3)}</span></div>
              <div>收盘: <span style="color: ${color};">${k.close.toFixed(3)}</span></div>
              <div>最高: <span style="color: #f56c6c;">${k.high.toFixed(3)}</span></div>
              <div>最低: <span style="color: #67c23a;">${k.low.toFixed(3)}</span></div>
              <div>涨跌: <span style="color: ${color};">${change}%</span></div>
              <div>成交量: ${(k.volume / 10000).toFixed(0)}万</div>
            </div>
          `
        }
      },
      legend: {
        data: ['K线', 'MA5', 'MA10', 'MA30', '成交量'],
        bottom: 10
      },
      grid: [
        { left: '10%', right: '8%', top: '10%', height: '50%' },
        { left: '10%', right: '8%', top: '68%', height: '20%' }
      ],
      xAxis: [
        {
          type: 'category',
          data: dates,
          boundaryGap: true,
          axisLine: { onZero: false },
          splitLine: { show: false },
          min: 'dataMin',
          max: 'dataMax'
        },
        {
          type: 'category',
          gridIndex: 1,
          data: dates,
          boundaryGap: true,
          axisLine: { onZero: false },
          axisTick: { show: false },
          splitLine: { show: false },
          axisLabel: { show: false },
          min: 'dataMin',
          max: 'dataMax'
        }
      ],
      yAxis: [
        {
          scale: true,
          splitArea: { show: true }
        },
        {
          scale: true,
          gridIndex: 1,
          splitNumber: 2,
          axisLabel: { show: false },
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { show: false }
        }
      ],
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: [0, 1],
          start: 70,
          end: 100
        },
        {
          show: true,
          xAxisIndex: [0, 1],
          type: 'slider',
          bottom: '5%',
          start: 70,
          end: 100
        }
      ],
      series: [
        {
          name: 'K线',
          type: 'candlestick',
          data: ohlc,
          itemStyle: {
            color: '#f56c6c',        // 阳线填充色
            color0: '#67c23a',       // 阴线填充色
            borderColor: '#f56c6c',  // 阳线边框色
            borderColor0: '#67c23a'  // 阴线边框色
          },
          markPoint: {
            symbol: 'pin',
            symbolSize: 40,
            data: props.signals.map(signal => ({
              name: signal.type === 'buy' ? '买入信号' : '卖出信号',
              coord: [signal.date, signal.price || ohlc[dates.indexOf(signal.date)]?.[1] || 0],
              value: signal.type === 'buy' ? '买' : '卖',
              itemStyle: {
                color: signal.type === 'buy' ? '#67c23a' : '#f56c6c'
              },
              label: {
                color: 'white',
                fontSize: 12,
                fontWeight: 'bold'
              }
            }))
          }
        },
        {
          name: 'MA5',
          type: 'line',
          data: ma5,
          smooth: true,
          lineStyle: { width: 1 },
          itemStyle: { color: '#409eff' },
          symbol: 'none'
        },
        {
          name: 'MA10',
          type: 'line',
          data: ma10,
          smooth: true,
          lineStyle: { width: 1 },
          itemStyle: { color: '#e6a23c' },
          symbol: 'none'
        },
        {
          name: 'MA30',
          type: 'line',
          data: ma30,
          smooth: true,
          lineStyle: { width: 1 },
          itemStyle: { color: '#909399' },
          symbol: 'none'
        },
        {
          name: '成交量',
          type: 'bar',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: volumes,
          itemStyle: {
            color: function(params: any) {
              const idx = params.dataIndex
              if (idx === 0) return '#409eff'
              return klines[idx].close >= klines[idx-1].close ? '#f56c6c' : '#67c23a'
            }
          }
        }
      ]
    }
  } else {
    // 折线图模式
    return {
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        borderColor: '#ddd',
        borderWidth: 1,
        textStyle: { color: '#333' }
      },
      legend: {
        data: ['收盘价', 'MA5', 'MA10', 'MA30'],
        bottom: 10
      },
      grid: { left: '10%', right: '8%', top: '10%', bottom: '15%' },
      xAxis: {
        type: 'category',
        data: dates,
        boundaryGap: false
      },
      yAxis: {
        type: 'value',
        scale: true
      },
      dataZoom: [
        { type: 'inside', start: 70, end: 100 },
        { type: 'slider', start: 70, end: 100 }
      ],
      series: [
        {
          name: '收盘价',
          type: 'line',
          data: klines.map(k => k.close),
          smooth: true,
          lineStyle: { width: 2 },
          itemStyle: { color: '#409eff' },
          areaStyle: { opacity: 0.1 }
        },
        {
          name: 'MA5',
          type: 'line',
          data: ma5,
          smooth: true,
          lineStyle: { width: 1 },
          itemStyle: { color: '#f56c6c' },
          symbol: 'none'
        },
        {
          name: 'MA10',
          type: 'line',
          data: ma10,
          smooth: true,
          lineStyle: { width: 1 },
          itemStyle: { color: '#e6a23c' },
          symbol: 'none'
        },
        {
          name: 'MA30',
          type: 'line',
          data: ma30,
          smooth: true,
          lineStyle: { width: 1 },
          itemStyle: { color: '#909399' },
          symbol: 'none'
        }
      ]
    }
  }
})
</script>

<style scoped>
.kline-card {
  margin-bottom: 20px;
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

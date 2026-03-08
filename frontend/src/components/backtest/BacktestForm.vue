<template>
  <el-card class="backtest-form-card">
    <template #header>
      <div class="card-header">
        <span>回测参数设置</span>
        <el-button type="primary" size="small" @click="showParams = !showParams">
          {{ showParams ? '收起' : '参数' }}
        </el-button>
      </div>
    </template>

    <el-form :model="formData" :rules="rules" ref="formRef" label-width="120px">
      <el-form-item label="ETF 代码" prop="etfCode">
        <el-input
          v-model="formData.etfCode"
          placeholder="请输入ETF代码，如：512400"
          clearable
        />
      </el-form-item>

      <el-form-item label="数据周期" prop="period">
        <el-select v-model="formData.period" placeholder="选择数据周期" style="width: 100%">
          <el-option label="日线" value="daily" />
          <el-option label="周线" value="weekly" />
          <el-option label="月线" value="monthly" />
        </el-select>
      </el-form-item>

      <el-form-item label="初始资金" prop="initialCapital">
        <el-input-number
          v-model="formData.initialCapital"
          :min="10000"
          :max="10000000"
          :step="10000"
          :precision="2"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="开始日期" prop="startDate">
        <el-date-picker
          v-model="formData.startDate"
          type="date"
          placeholder="选择开始日期"
          value-format="YYYY-MM-DD"
          style="width: 100%"
          :disabled-date="disabledStartDate"
        />
      </el-form-item>

      <el-form-item label="结束日期" prop="endDate">
        <el-date-picker
          v-model="formData.endDate"
          type="date"
          placeholder="选择结束日期"
          value-format="YYYY-MM-DD"
          style="width: 100%"
          :disabled-date="disabledEndDate"
        />
      </el-form-item>

      <el-form-item>
        <el-button
          type="primary"
          @click="handleSubmit"
          :loading="loading"
          size="large"
          style="width: 100%"
        >
          {{ loading ? '回测中...' : '开始回测' }}
        </el-button>
      </el-form-item>
    </el-form>

    <!-- 策略参数编辑器 -->
    <el-collapse-transition>
      <div v-show="showParams" class="strategy-params">
        <el-divider content-position="left">策略参数</el-divider>

        <el-form label-width="150px" size="small">
          <!-- 趋势跟踪参数 -->
          <div class="param-section">
            <h4>趋势跟踪策略</h4>
            <el-form-item label="短期均线周期">
              <el-input-number
                v-model="strategyParams.trend.ma_short_period"
                :min="1"
                :max="200"
                :step="1"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="长期均线周期">
              <el-input-number
                v-model="strategyParams.trend.ma_long_period"
                :min="1"
                :max="200"
                :step="1"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="RSI超卖阈值">
              <el-input-number
                v-model="strategyParams.trend.rsi_oversold"
                :min="0"
                :max="50"
                :step="1"
                :precision="1"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="RSI超买阈值">
              <el-input-number
                v-model="strategyParams.trend.rsi_overbought"
                :min="50"
                :max="100"
                :step="1"
                :precision="1"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="成交量激增倍数">
              <el-input-number
                v-model="strategyParams.trend.volume_surge_threshold"
                :min="1.0"
                :max="5.0"
                :step="0.1"
                :precision="1"
                style="width: 100%"
              />
            </el-form-item>
          </div>

          <!-- 底部吸筹参数 -->
          <div class="param-section">
            <h4>底部吸筹策略</h4>
            <el-form-item label="布林带周期">
              <el-input-number
                v-model="strategyParams.bottom.bollinger_period"
                :min="5"
                :max="100"
                :step="1"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="布林带标准差">
              <el-input-number
                v-model="strategyParams.bottom.bollinger_std"
                :min="0.5"
                :max="4.0"
                :step="0.1"
                :precision="1"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="RSI底部阈值">
              <el-input-number
                v-model="strategyParams.bottom.rsi_bottom_threshold"
                :min="0"
                :max="40"
                :step="1"
                :precision="1"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="支撑位回看周期">
              <el-input-number
                v-model="strategyParams.bottom.support_lookback"
                :min="5"
                :max="100"
                :step="1"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="成交量萎缩阈值">
              <el-input-number
                v-model="strategyParams.bottom.volume_shrink_threshold"
                :min="0.1"
                :max="1.0"
                :step="0.05"
                :precision="2"
                style="width: 100%"
              />
            </el-form-item>
          </div>

          <!-- 凯利公式参数 -->
          <div class="param-section">
            <h4>凯利公式</h4>
            <el-form-item label="胜率估计">
              <el-input-number
                v-model="strategyParams.kelly.win_rate_estimate"
                :min="0.1"
                :max="0.9"
                :step="0.01"
                :precision="2"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="盈亏比">
              <el-input-number
                v-model="strategyParams.kelly.avg_win_avg_loss_ratio"
                :min="1.0"
                :max="5.0"
                :step="0.1"
                :precision="1"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="最大仓位比例">
              <el-input-number
                v-model="strategyParams.kelly.max_position_pct"
                :min="0.05"
                :max="1.0"
                :step="0.05"
                :precision="2"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="最小仓位比例">
              <el-input-number
                v-model="strategyParams.kelly.min_position_pct"
                :min="0.01"
                :max="0.3"
                :step="0.01"
                :precision="2"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="凯利系数">
              <el-input-number
                v-model="strategyParams.kelly.kelly_fraction"
                :min="0.1"
                :max="1.0"
                :step="0.05"
                :precision="2"
                style="width: 100%"
              />
            </el-form-item>
          </div>

          <!-- 止损参数 -->
          <div class="param-section">
            <h4>止损策略</h4>
            <el-form-item label="固定止损比例">
              <el-input-number
                v-model="strategyParams.stop_loss.fixed_pct"
                :min="0.01"
                :max="0.2"
                :step="0.005"
                :precision="3"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="ATR倍数">
              <el-input-number
                v-model="strategyParams.stop_loss.atr_multiplier"
                :min="1.0"
                :max="5.0"
                :step="0.1"
                :precision="1"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="ATR周期">
              <el-input-number
                v-model="strategyParams.stop_loss.atr_period"
                :min="5"
                :max="50"
                :step="1"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="支撑位比例">
              <el-input-number
                v-model="strategyParams.stop_loss.support_pct"
                :min="0.005"
                :max="0.1"
                :step="0.005"
                :precision="3"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="移动止损激活比例">
              <el-input-number
                v-model="strategyParams.stop_loss.trailing_activation_pct"
                :min="0.005"
                :max="0.1"
                :step="0.005"
                :precision="3"
                style="width: 100%"
              />
            </el-form-item>
          </div>

          <el-form-item>
            <el-row :gutter="10" style="width: 100%">
              <el-col :span="12">
                <el-button type="success" @click="handleSaveParams" :loading="saving" style="width: 100%">
                  保存方案
                </el-button>
              </el-col>
              <el-col :span="12">
                <el-button @click="handleResetParams" style="width: 100%">
                  重置默认
                </el-button>
              </el-col>
            </el-row>
          </el-form-item>
        </el-form>
      </div>
    </el-collapse-transition>
  </el-card>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import type { BacktestRequest, StrategyParams } from '../../types'
import { getStrategyParams, updateStrategyParams } from '../../services/api'

interface Props {
  loading?: boolean
}

interface Emits {
  (e: 'submit', data: BacktestRequest): void
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const showParams = ref(false)
const saving = ref(false)

const formData = reactive<BacktestRequest>({
  etfCode: '512400',
  period: 'daily',
  initialCapital: 100000,
  startDate: '',
  endDate: ''
})

const strategyParams = reactive<StrategyParams>({
  trend: {
    ma_short_period: 5,
    ma_long_period: 20,
    rsi_oversold: 30,
    rsi_overbought: 70,
    volume_surge_threshold: 1.5
  },
  bottom: {
    bollinger_period: 20,
    bollinger_std: 2.0,
    rsi_bottom_threshold: 20,
    support_lookback: 20,
    volume_shrink_threshold: 0.7
  },
  kelly: {
    win_rate_estimate: 0.55,
    avg_win_avg_loss_ratio: 1.5,
    max_position_pct: 0.3,
    min_position_pct: 0.05,
    kelly_fraction: 0.25
  },
  stop_loss: {
    fixed_pct: 0.05,
    atr_multiplier: 2.0,
    atr_period: 14,
    support_pct: 0.02,
    trailing_activation_pct: 0.02
  }
})

const rules: FormRules = {
  etfCode: [
    { required: true, message: '请输入ETF代码', trigger: 'blur' },
    { pattern: /^\d{6}$/, message: 'ETF代码应为6位数字', trigger: 'blur' }
  ],
  period: [
    { required: true, message: '请选择数据周期', trigger: 'change' }
  ],
  initialCapital: [
    { required: true, message: '请输入初始资金', trigger: 'blur' }
  ]
}

const disabledStartDate = (time: Date) => {
  if (formData.endDate) {
    return time.getTime() > new Date(formData.endDate).getTime()
  }
  return time.getTime() > Date.now()
}

const disabledEndDate = (time: Date) => {
  if (formData.startDate) {
    return time.getTime() < new Date(formData.startDate).getTime()
  }
  return time.getTime() > Date.now()
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate((valid) => {
    if (valid) {
      emit('submit', {
        etf_code: formData.etfCode,
        period: formData.period,
        start_date: formData.startDate || undefined,
        end_date: formData.endDate || undefined,
        initial_capital: formData.initialCapital
      })
    }
  })
}

const handleResetParams = async () => {
  try {
    const defaultParams = await getStrategyParams()
    Object.assign(strategyParams, defaultParams)
  } catch (error) {
    console.error('Failed to reset params:', error)
  }
}

const handleSaveParams = async () => {
  saving.value = true
  try {
    await updateStrategyParams(strategyParams)
    ElMessage.success('策略方案已保存')
  } catch (error) {
    console.error('Failed to save params:', error)
    ElMessage.error('保存失败，请重试')
  } finally {
    saving.value = false
  }
}

// Load default params on mount
handleResetParams()
</script>

<style scoped>
.backtest-form-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: 500;
}

.strategy-params {
  margin-top: 20px;
  padding-top: 10px;
}

.param-section {
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.param-section h4 {
  margin: 0 0 15px 0;
  font-size: 14px;
  font-weight: 500;
  color: #409eff;
}
</style>

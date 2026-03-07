<template>
  <el-card class="input-form-card">
    <template #header>
      <div class="card-header">
        <span>ETF 分析参数</span>
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

      <el-form-item label="总资金" prop="totalCapital">
        <el-input-number
          v-model="formData.totalCapital"
          :min="0"
          :step="1000"
          :precision="2"
          style="width: 100%"
          placeholder="请输入总资金"
        />
      </el-form-item>

      <el-form-item label="持仓金额" prop="holdingAmount">
        <el-input-number
          v-model="formData.holdingAmount"
          :min="0"
          :step="100"
          :precision="2"
          style="width: 100%"
          placeholder="请输入持仓金额"
        />
      </el-form-item>

      <el-form-item label="当前收益率" prop="currentYield">
        <el-input-number
          v-model="formData.currentYield"
          :min="-100"
          :max="100"
          :step="0.1"
          :precision="2"
          style="width: 100%"
          placeholder="请输入当前收益率（%）"
        >
          <template #suffix>%</template>
        </el-input-number>
      </el-form-item>

      <el-form-item label="风险偏好" prop="riskPreference">
        <el-radio-group v-model="formData.riskPreference">
          <el-radio label="conservative">保守</el-radio>
          <el-radio label="neutral">中性</el-radio>
          <el-radio label="aggressive">激进</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item>
        <el-button
          type="primary"
          @click="handleSubmit"
          :loading="loading"
          size="large"
          style="width: 100%"
        >
          {{ loading ? '分析中...' : '开始分析' }}
        </el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import type { RiskPreference } from '../types'

interface Props {
  loading?: boolean
}

interface Emits {
  (e: 'submit', data: {
    etfCode: string
    totalCapital: number
    holdingAmount: number
    currentYield: number
    riskPreference: RiskPreference
  }): void
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const formData = reactive({
  etfCode: '512400',
  totalCapital: 100000,
  holdingAmount: 0,
  currentYield: 0,
  riskPreference: 'neutral' as RiskPreference
})

const rules: FormRules = {
  etfCode: [
    { required: true, message: '请输入ETF代码', trigger: 'blur' },
    { pattern: /^\d{6}$/, message: 'ETF代码应为6位数字', trigger: 'blur' }
  ],
  totalCapital: [
    { required: true, message: '请输入总资金', trigger: 'blur' },
    { type: 'number', min: 0, message: '总资金不能为负数', trigger: 'blur' }
  ],
  holdingAmount: [
    { required: true, message: '请输入持仓金额', trigger: 'blur' },
    { type: 'number', min: 0, message: '持仓金额不能为负数', trigger: 'blur' }
  ],
  currentYield: [
    { required: true, message: '请输入当前收益率', trigger: 'blur' },
    { type: 'number', min: -100, max: 100, message: '收益率应在-100%到100%之间', trigger: 'blur' }
  ],
  riskPreference: [
    { required: true, message: '请选择风险偏好', trigger: 'change' }
  ]
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate((valid) => {
    if (valid) {
      emit('submit', {
        etfCode: formData.etfCode,
        totalCapital: formData.totalCapital,
        holdingAmount: formData.holdingAmount,
        currentYield: formData.currentYield,
        riskPreference: formData.riskPreference
      })
    }
  })
}
</script>

<style scoped>
.input-form-card {
  margin-bottom: 20px;
}

.card-header {
  font-size: 18px;
  font-weight: 500;
}
</style>

<template>
  <el-tag :type="tagType" size="large" effect="dark" class="signal-badge">
    {{ signalText }}
  </el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { SignalType } from '../types'

interface Props {
  signalType: SignalType
  strength?: number
}

const props = withDefaults(defineProps<Props>(), {
  strength: 0
})

const tagType = computed(() => {
  switch (props.signalType) {
    case 'buy':
      return 'success'
    case 'sell':
      return 'danger'
    case 'hold':
      return 'info'
    default:
      return 'info'
  }
})

const signalText = computed(() => {
  switch (props.signalType) {
    case 'buy':
      return `买入 ${props.strength ? `(${(props.strength * 100).toFixed(0)}%)` : ''}`
    case 'sell':
      return `卖出 ${props.strength ? `(${(props.strength * 100).toFixed(0)}%)` : ''}`
    case 'hold':
      return '持有'
    default:
      return '未知'
  }
})
</script>

<style scoped>
.signal-badge {
  font-size: 16px;
  font-weight: 500;
  padding: 8px 16px;
}
</style>

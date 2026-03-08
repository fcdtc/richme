<template>
  <el-card class="trade-list-card" v-if="trades.length > 0">
    <template #header>
      <div class="card-header">
        <span>交易记录</span>
        <el-tag type="info" size="small">共 {{ trades.length }} 笔交易</el-tag>
      </div>
    </template>

    <el-table
      :data="paginatedTrades"
      stripe
      style="width: 100%"
      :default-sort="{ prop: 'entry_date', order: 'descending' }"
    >
      <el-table-column prop="entry_date" label="建仓日期" width="110" sortable>
        <template #default="{ row }">
          {{ formatDate(row.entry_date) }}
        </template>
      </el-table-column>

      <el-table-column prop="exit_date" label="平仓日期" width="110" sortable>
        <template #default="{ row }">
          {{ formatDate(row.exit_date) }}
        </template>
      </el-table-column>

      <el-table-column prop="entry_price" label="建仓价" width="90" align="right">
        <template #default="{ row }">
          {{ row.entry_price.toFixed(3) }}
        </template>
      </el-table-column>

      <el-table-column prop="exit_price" label="平仓价" width="90" align="right">
        <template #default="{ row }">
          {{ row.exit_price.toFixed(3) }}
        </template>
      </el-table-column>

      <el-table-column prop="quantity" label="数量" width="90" align="right">
        <template #default="{ row }">
          {{ row.quantity.toFixed(2) }}
        </template>
      </el-table-column>

      <el-table-column prop="position_value" label="仓位金额" width="100" align="right">
        <template #default="{ row }">
          ¥{{ row.position_value.toFixed(2) }}
        </template>
      </el-table-column>

      <el-table-column prop="holding_days" label="持仓天数" width="90" align="right">
        <template #default="{ row }">
          {{ row.holding_days }}
        </template>
      </el-table-column>

      <el-table-column prop="exit_reason" label="退出原因" width="100">
        <template #default="{ row }">
          <el-tag :type="getExitReasonType(row.exit_reason)" size="small">
            {{ getExitReasonText(row.exit_reason) }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="pnl" label="盈亏" width="120" align="right" sortable>
        <template #default="{ row }">
          <span :class="row.pnl >= 0 ? 'profit' : 'loss'">
            {{ row.pnl >= 0 ? '+' : '' }}¥{{ row.pnl.toFixed(2) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column prop="pnl_pct" label="收益率" width="100" align="right" sortable>
        <template #default="{ row }">
          <span :class="row.pnl >= 0 ? 'profit' : 'loss'">
            {{ row.pnl >= 0 ? '+' : '' }}{{ row.pnl_pct.toFixed(2) }}%
          </span>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :page-sizes="[10, 20, 50, 100]"
      :total="trades.length"
      layout="total, sizes, prev, pager, next, jumper"
      style="margin-top: 20px; justify-content: center"
    />
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { BacktestTrade } from '../../types'

interface Props {
  trades: BacktestTrade[]
}

const props = defineProps<Props>()

const currentPage = ref(1)
const pageSize = ref(20)

const paginatedTrades = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return props.trades.slice(start, end)
})

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

const getExitReasonType = (reason: string) => {
  const map: Record<string, any> = {
    stop_loss: 'danger',
    signal: 'primary',
    take_profit: 'success',
    end_of_test: 'info'
  }
  return map[reason] || 'info'
}

const getExitReasonText = (reason: string) => {
  const map: Record<string, string> = {
    stop_loss: '止损',
    signal: '信号',
    take_profit: '止盈',
    end_of_test: '测试结束'
  }
  return map[reason] || reason
}
</script>

<style scoped>
.trade-list-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: 500;
}

.profit {
  color: #ef5350;  /* 盈利 - 红色 */
  font-weight: 500;
}

.loss {
  color: #26a69a;  /* 亏损 - 绿色 */
  font-weight: 500;
}

:deep(.el-pagination) {
  display: flex;
  justify-content: center;
}
</style>

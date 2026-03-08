/**
 * 颜色配置 - 中国股市惯例（红涨绿跌）
 *
 * 红色：多头、买入、上涨、盈利
 * 绿色：空头、卖出、下跌、亏损
 */

// 核心交易颜色
export const COLORS = {
  // 上涨/多头/买入/盈利 - 红色
  BULLISH: '#f56c6c',      // 多头
  BUY: '#f56c6c',          // 买入
  UP: '#f56c6c',           // 上涨
  PROFIT: '#f56c6c',       // 盈利

  // 下跌/空头/卖出/亏损 - 绿色
  BEARISH: '#67c23a',      // 空头
  SELL: '#67c23a',         // 卖出
  DOWN: '#67c23a',         // 下跌
  LOSS: '#67c23a',         // 亏损

  // 中性颜色
  NEUTRAL: '#909399',      // 中性/持有
  INFO: '#409eff',         // 信息
  WARNING: '#e6a23c',      // 警告

  // K线专用
  CANDLESTICK: {
    YANG: '#f56c6c',       // 阳线（收盘价>=开盘价）
    YIN: '#67c23a',        // 阴线（收盘价<开盘价）
  },

  // 指标线颜色
  INDICATOR: {
    MA5: '#409eff',
    MA10: '#e6a23c',
    MA30: '#909399',
  }
} as const

// Element Plus tag 类型映射（需要自定义样式覆盖）
export const TAG_TYPE = {
  BULLISH: 'danger',   // 多头 - 使用 danger（红色）
  BEARISH: 'success',  // 空头 - 使用 success（绿色）
  BUY: 'danger',       // 买入 - 红色
  SELL: 'success',     // 卖出 - 绿色
  NEUTRAL: 'info',     // 中性
} as const

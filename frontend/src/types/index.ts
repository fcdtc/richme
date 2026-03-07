// ETF分析相关类型定义

export interface ETFData {
  symbol: string
  name: string
  price: number
  volume: number
  date: string
}

export interface CalculationParams {
  capital: number
  leverage: number
  stopLossPercent: number
  takeProfitPercent: number
}

export interface CalculationResult {
  positionSize: number
  stopLossPrice: number
  takeProfitPrice: number
  riskRewardRatio: number
}

export type RiskPreference = 'conservative' | 'neutral' | 'aggressive'
export type SignalType = 'buy' | 'sell' | 'hold'
export type IndicatorSignal = 'bullish' | 'bearish' | 'neutral'

// K线数据
export interface KlineItem {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  ma5?: number
  ma10?: number
  ma30?: number
}

export interface KlineData {
  code: string
  period: string
  count: number
  klines: KlineItem[]
  fetch_time: string
  source: string
}

// 指标值 - 包含信号和解读
export interface IndicatorValue {
  value: number
  signal: IndicatorSignal
  interpretation: string
}

// MACD指标组
export interface MACDIndicators {
  macd: IndicatorValue
  signal: IndicatorValue
  histogram: IndicatorValue
}

// KDJ指标组
export interface KDJIndicators {
  k: IndicatorValue
  d: IndicatorValue
  j: IndicatorValue
}

// 布林带
export interface BollingerBands {
  upper: number
  middle: number
  lower: number
}

// 所有技术指标
export interface Indicators {
  ma5: IndicatorValue
  ma10: IndicatorValue
  ma20: IndicatorValue
  ma60: IndicatorValue
  rsi: IndicatorValue
  macd: MACDIndicators
  kdj: KDJIndicators
  bollinger: BollingerBands
}

// 交易信号
export interface Signal {
  signal_type: SignalType
  strength: number
  confidence: number
}

// 仓位建议
export interface PositionRecommendation {
  action: 'buy' | 'sell' | 'hold'    // 操作类型: buy加仓, sell减仓, hold持有不动
  amount: number                      // 建议交易金额
  percentage: number                  // 目标仓位占总资金比例
  stop_loss_price: number             // 建议止损价
  take_profit_price: number           // 建议止盈价
  risk_amount: number                 // 潜在风险金额
  risk_percentage: number             // 风险占总资金比例
  max_position: number                // 最大允许持仓金额
  current_position: number            // 当前持仓金额
  target_position: number             // 目标持仓金额
  // 量化依据
  signal_score: number                // 综合信号得分 (-1 to 1)
  trend_direction: string             // 趋势方向: up/down/sideways
  trend_strength: number              // 趋势强度 (0-1)
  support_level: number               // 支撑位价格
  resistance_level: number            // 阻力位价格
  reason: string                      // 详细操作理由
}

// 分析项
export interface AnalysisItem {
  indicator: string
  value: number
  signal: IndicatorSignal
  interpretation: string
  weight: number
}

// 数据质量
export interface DataQuality {
  completeness: number
  reliability: number
  recency: number
}

// 分析请求
export interface AnalyzeRequest {
  etf_code: string
  risk_preference: RiskPreference
  use_cache: boolean
  total_capital?: number      // 总资金
  holding_amount?: number     // 持仓金额
}

// 分析响应
export interface AnalyzeResponse {
  etf_code: string
  etf_name: string
  current_price: number
  signal: Signal
  indicators: Indicators
  analysis: AnalysisItem[]
  overall_score: number
  timestamp: string
  data_quality: DataQuality
  klines: KlineData | null          // K线数据
  position: PositionRecommendation   // 仓位建议
}

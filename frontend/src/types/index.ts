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
}

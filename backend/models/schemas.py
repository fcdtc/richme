from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from datetime import datetime


# 风险偏好类型
RiskPreferenceType = Literal["conservative", "neutral", "aggressive"]

# 信号类型
SignalType = Literal["bullish", "bearish", "neutral"]


class AnalysisRequest(BaseModel):
    """Request model for ETF analysis"""
    etf_code: str = Field(..., description="ETF code (e.g., 510300)")
    risk_preference: RiskPreferenceType = Field(default="neutral", description="Risk preference setting")
    use_cache: bool = Field(default=True, description="Whether to use cached data")
    total_capital: Optional[float] = Field(default=100000, description="Total capital")
    holding_amount: Optional[float] = Field(default=0, description="Current holding amount")


class IndicatorValue(BaseModel):
    """Indicator value with signal interpretation"""
    value: float = Field(..., description="Current indicator value")
    signal: SignalType = Field(default="neutral", description="Signal type")
    interpretation: str = Field(default="", description="Interpretation of the indicator")


class MACDIndicators(BaseModel):
    """MACD indicator group"""
    macd: IndicatorValue = Field(..., description="MACD line")
    signal: IndicatorValue = Field(..., description="Signal line")
    histogram: IndicatorValue = Field(..., description="Histogram")


class KDJIndicators(BaseModel):
    """KDJ indicator group"""
    k: IndicatorValue = Field(..., description="K value")
    d: IndicatorValue = Field(..., description="D value")
    j: IndicatorValue = Field(..., description="J value")


class BollingerBands(BaseModel):
    """Bollinger Bands indicator"""
    upper: float = Field(..., description="Upper band")
    middle: float = Field(..., description="Middle band")
    lower: float = Field(..., description="Lower band")


class Indicators(BaseModel):
    """All technical indicators"""
    ma5: IndicatorValue = Field(..., description="5-day MA")
    ma10: IndicatorValue = Field(..., description="10-day MA")
    ma20: IndicatorValue = Field(..., description="20-day MA")
    ma60: IndicatorValue = Field(..., description="60-day MA")
    rsi: IndicatorValue = Field(..., description="RSI indicator")
    macd: MACDIndicators = Field(..., description="MACD indicators")
    kdj: KDJIndicators = Field(..., description="KDJ indicators")
    bollinger: BollingerBands = Field(..., description="Bollinger Bands")


class Signal(BaseModel):
    """Trading signal result"""
    signal_type: Literal["buy", "sell", "hold"] = Field(..., description="Trading signal type")
    strength: float = Field(..., ge=0.0, le=1.0, description="Signal strength from 0 to 1")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level from 0 to 1")


class KlineItem(BaseModel):
    """Single K-line data item"""
    date: str = Field(..., description="Date/time")
    open: float = Field(..., description="Open price")
    high: float = Field(..., description="High price")
    low: float = Field(..., description="Low price")
    close: float = Field(..., description="Close price")
    volume: int = Field(..., description="Volume")
    ma5: Optional[float] = Field(default=0, description="MA5")
    ma10: Optional[float] = Field(default=0, description="MA10")
    ma30: Optional[float] = Field(default=0, description="MA30")


class KlineData(BaseModel):
    """K-line data container"""
    code: str = Field(..., description="ETF code")
    period: str = Field(..., description="Period name")
    count: int = Field(..., description="Number of items")
    klines: List[KlineItem] = Field(default_factory=list, description="K-line items")
    fetch_time: str = Field(default="", description="Fetch timestamp")
    source: str = Field(default="", description="Data source")


class PositionRecommendation(BaseModel):
    """Position recommendation based on risk preference and capital"""
    action: Literal["buy", "sell", "hold"] = Field(..., description="Recommended action")
    amount: float = Field(..., description="Recommended amount in currency")
    shares: int = Field(..., description="Recommended shares (rounded to 100)")
    percentage: float = Field(..., description="Percentage of total capital")
    stop_loss_price: float = Field(..., description="Stop loss price")
    take_profit_price: float = Field(..., description="Take profit price")
    risk_amount: float = Field(..., description="Risk amount if stop loss triggered")
    risk_percentage: float = Field(..., description="Risk percentage of total capital")
    max_position: float = Field(..., description="Maximum position allowed")
    current_position: float = Field(..., description="Current position value")
    target_position: float = Field(..., description="Target position value")
    reason: str = Field(..., description="Reason for recommendation")


class AnalysisItem(BaseModel):
    """Individual analysis item"""
    indicator: str = Field(..., description="Indicator name")
    value: float = Field(..., description="Indicator value")
    signal: SignalType = Field(..., description="Signal type")
    interpretation: str = Field(..., description="Interpretation")
    weight: float = Field(..., ge=0.0, le=1.0, description="Weight in overall analysis")


class DataQuality(BaseModel):
    """Data quality metrics"""
    completeness: float = Field(..., ge=0.0, le=1.0, description="Data completeness")
    reliability: float = Field(..., ge=0.0, le=1.0, description="Data reliability")
    recency: float = Field(..., ge=0.0, le=1.0, description="Data recency")


class AnalysisResponse(BaseModel):
    """Response model for ETF analysis"""
    etf_code: str = Field(..., description="Analyzed ETF code")
    etf_name: str = Field(default="", description="ETF name")
    current_price: float = Field(..., description="Current ETF price")
    signal: Signal = Field(..., description="Trading signal result")
    indicators: Indicators = Field(..., description="Technical indicators")
    analysis: List[AnalysisItem] = Field(default_factory=list, description="Analysis items")
    overall_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Overall score")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Analysis timestamp")
    data_quality: DataQuality = Field(
        default_factory=lambda: DataQuality(completeness=0.9, reliability=0.85, recency=0.95),
        description="Data quality metrics"
    )
    klines: Optional[KlineData] = Field(default=None, description="K-line data")
    position: Optional[PositionRecommendation] = Field(default=None, description="Position recommendation")

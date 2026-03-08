"""
Pydantic models for backtest API requests and responses.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from datetime import datetime


class BacktestRequest(BaseModel):
    """Request model for backtest"""
    etf_code: str = Field(..., description="ETF code (e.g., 510300)")
    period: str = Field(default="daily", description="Data period")
    start_date: Optional[str] = Field(default=None, description="Start date YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="End date YYYY-MM-DD")
    initial_capital: float = Field(default=100000, description="Initial capital")


class BacktestTrade(BaseModel):
    """Individual trade record"""
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    quantity: float
    position_value: float
    pnl: float
    pnl_pct: float
    holding_days: int
    exit_reason: Literal['stop_loss', 'signal', 'take_profit', 'end_of_test']
    stop_loss: Optional[float] = None
    signals: Optional[List[str]] = None


class BacktestMetrics(BaseModel):
    """Backtest performance metrics"""
    initial_capital: float
    final_capital: float
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    avg_win: float
    avg_loss: float
    profit_factor: float


class EquityPoint(BaseModel):
    """Single point in equity curve"""
    date: str
    value: float
    drawdown: float


class BacktestResponse(BaseModel):
    """Response model for backtest"""
    etf_code: str
    period: str
    metrics: BacktestMetrics
    equity_curve: List[EquityPoint]
    trades: List[BacktestTrade]
    strategy_params: Optional[Dict] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# Strategy parameter schemas
class TrendFollowingConfig(BaseModel):
    ma_short_period: int = Field(default=5, ge=1, le=200)
    ma_long_period: int = Field(default=20, ge=1, le=200)
    rsi_oversold: float = Field(default=30.0, ge=0, le=50)
    rsi_overbought: float = Field(default=70.0, ge=50, le=100)
    volume_surge_threshold: float = Field(default=1.5, ge=1.0, le=5.0)


class BottomFishingConfig(BaseModel):
    bollinger_period: int = Field(default=20, ge=5, le=100)
    bollinger_std: float = Field(default=2.0, ge=0.5, le=4.0)
    rsi_bottom_threshold: float = Field(default=20.0, ge=0, le=40)
    support_lookback: int = Field(default=20, ge=5, le=100)
    volume_shrink_threshold: float = Field(default=0.7, ge=0.1, le=1.0)


class KellyConfig(BaseModel):
    win_rate_estimate: float = Field(default=0.55, ge=0.1, le=0.9)
    avg_win_avg_loss_ratio: float = Field(default=1.5, ge=1.0, le=5.0)
    max_position_pct: float = Field(default=0.3, ge=0.05, le=1.0)
    min_position_pct: float = Field(default=0.05, ge=0.01, le=0.3)
    kelly_fraction: float = Field(default=0.25, ge=0.1, le=1.0)


class StopLossConfig(BaseModel):
    fixed_pct: float = Field(default=0.05, ge=0.01, le=0.2)
    atr_multiplier: float = Field(default=2.0, ge=1.0, le=5.0)
    atr_period: int = Field(default=14, ge=5, le=50)
    support_pct: float = Field(default=0.02, ge=0.005, le=0.1)
    trailing_activation_pct: float = Field(default=0.02, ge=0.005, le=0.1)


class StrategyParams(BaseModel):
    """Complete strategy parameters"""
    trend: TrendFollowingConfig
    bottom: BottomFishingConfig
    kelly: KellyConfig
    stop_loss: StopLossConfig

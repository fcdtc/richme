"""Backtest router for ETF strategy testing."""
import pandas as pd
from fastapi import APIRouter, HTTPException
from backend.models.backtest_schemas import (
    BacktestRequest, BacktestResponse, StrategyParams,
    TrendFollowingConfig, BottomFishingConfig, KellyConfig, StopLossConfig
)
from backend.services.backtest import BacktestEngine
from backend.services.strategy_engine import StrategyEngine
from backend.services.fetcher import MultiSourceFetcher

router = APIRouter(prefix="/api", tags=["backtest"])

# Initialize fetcher
fetcher = MultiSourceFetcher()

# Default strategy parameters
DEFAULT_PARAMS = {
    'trend': TrendFollowingConfig().dict(),
    'bottom': BottomFishingConfig().dict(),
    'kelly': KellyConfig().dict(),
    'stop_loss': StopLossConfig().dict()
}

# Store custom params (in production, use database/session)
custom_params = {}


def get_strategy_params() -> dict:
    """Get strategy parameters (custom or default)"""
    if custom_params:
        return custom_params
    return DEFAULT_PARAMS


@router.post("/backtest", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest) -> BacktestResponse:
    """
    Run historical backtest for an ETF.

    Fetches 1 year of historical data by default,
    applies strategy engine to generate trades,
    returns complete performance metrics.

    Args:
        request: Backtest request with ETF code and optional date range

    Returns:
        BacktestResponse with metrics, equity curve, and trade list
    """
    try:
        # Fetch historical data
        kline_data = fetcher.fetch_kline(
            request.etf_code,
            period="daily",
            count=500  # ~2 years of daily data
        )

        if not kline_data or not kline_data.get('klines'):
            raise HTTPException(
                status_code=404,
                detail=f"无法获取 {request.etf_code} 的历史数据"
            )

        # Convert to DataFrame
        df = pd.DataFrame(kline_data['klines'])

        # Filter by date range if provided
        if request.start_date:
            df = df[df['date'] >= request.start_date]
        if request.end_date:
            df = df[df['date'] <= request.end_date]

        if df.empty:
            raise HTTPException(
                status_code=400,
                detail="筛选后的数据为空"
            )

        # Initialize strategy engine with parameters
        params = get_strategy_params()
        strategy_engine = StrategyEngine(params)

        # Run backtest
        backtest_engine = BacktestEngine(
            strategy_engine,
            initial_capital=request.initial_capital
        )
        result = backtest_engine.run(df)

        return BacktestResponse(
            etf_code=request.etf_code,
            period=request.period,
            metrics=result['metrics'],
            equity_curve=result['equity_curve'],
            trades=result['trades'],
            strategy_params=params,
            timestamp=pd.Timestamp.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"回测过程中发生错误: {str(e)}"
        )


@router.get("/strategy/params")
async def get_strategy_params_endpoint() -> StrategyParams:
    """
    Get current strategy parameter defaults.

    Returns:
        Current strategy parameters for all modules
    """
    params = get_strategy_params()
    return StrategyParams(
        trend=TrendFollowingConfig(**params['trend']),
        bottom=BottomFishingConfig(**params['bottom']),
        kelly=KellyConfig(**params['kelly']),
        stop_loss=StopLossConfig(**params['stop_loss'])
    )


@router.post("/strategy/params")
async def update_strategy_params(params: StrategyParams) -> StrategyParams:
    """
    Update strategy parameters.

    Args:
        params: New strategy parameters

    Returns:
        Updated strategy parameters
    """
    global custom_params
    custom_params = {
        'trend': params.trend.dict(),
        'bottom': params.bottom.dict(),
        'kelly': params.kelly.dict(),
        'stop_loss': params.stop_loss.dict()
    }
    return params


@router.get("/strategy/params/reset")
async def reset_strategy_params() -> dict:
    """
    Reset strategy parameters to defaults.

    Returns:
        Default strategy parameters
    """
    global custom_params
    custom_params = {}
    return DEFAULT_PARAMS

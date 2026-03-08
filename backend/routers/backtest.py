"""Backtest router for ETF strategy testing."""
import json
from pathlib import Path
import pandas as pd
from fastapi import APIRouter, HTTPException
from backend.models.backtest_schemas import (
    BacktestRequest, BacktestResponse, StrategyParams,
    TrendFollowingConfig, BottomFishingConfig, KellyConfig, StopLossConfig,
    BacktestKlineData, KlineItem, TradeSignal
)
from backend.services.backtest import BacktestEngine
from backend.services.strategy_engine import StrategyEngine
from backend.services.fetcher import MultiSourceFetcher

router = APIRouter(prefix="/api", tags=["backtest"])

# Initialize fetcher
fetcher = MultiSourceFetcher()

# Persistent storage path
DATA_DIR = Path(__file__).parent.parent / "data"
STRATEGY_PARAMS_FILE = DATA_DIR / "strategy_params.json"

# Default strategy parameters
DEFAULT_PARAMS = {
    'trend': TrendFollowingConfig().dict(),
    'bottom': BottomFishingConfig().dict(),
    'kelly': KellyConfig().dict(),
    'stop_loss': StopLossConfig().dict()
}


def _ensure_data_dir():
    """Ensure data directory exists"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_params_from_file() -> dict | None:
    """Load strategy params from persistent file"""
    if STRATEGY_PARAMS_FILE.exists():
        try:
            with open(STRATEGY_PARAMS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    return None


def _save_params_to_file(params: dict):
    """Save strategy params to persistent file"""
    _ensure_data_dir()
    with open(STRATEGY_PARAMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(params, f, ensure_ascii=False, indent=2)


def get_strategy_params() -> dict:
    """Get strategy parameters (persistent or default)"""
    saved_params = _load_params_from_file()
    if saved_params:
        return saved_params
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

        # Prepare K-line data for chart display
        kline_items = []
        for _, row in df.iterrows():
            kline_items.append(KlineItem(
                date=str(row['date']),
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=float(row['volume']),
                ma5=float(row.get('ma5', 0)) if 'ma5' in row else None,
                ma10=float(row.get('ma10', 0)) if 'ma10' in row else None,
                ma30=float(row.get('ma30', 0)) if 'ma30' in row else None
            ))

        backtest_kline_data = BacktestKlineData(
            code=request.etf_code,
            period=request.period,
            count=len(kline_items),
            klines=kline_items,
            fetch_time=pd.Timestamp.now().isoformat(),
            source='backtest'
        )

        # Extract trade signals for chart display
        signals = []
        for trade in result['trades']:
            signals.append(TradeSignal(
                date=trade['entry_date'],
                type='buy',
                price=trade['entry_price']
            ))
            signals.append(TradeSignal(
                date=trade['exit_date'],
                type='sell',
                price=trade['exit_price']
            ))

        return BacktestResponse(
            etf_code=request.etf_code,
            period=request.period,
            metrics=result['metrics'],
            equity_curve=result['equity_curve'],
            trades=result['trades'],
            klines=backtest_kline_data,
            signals=signals,
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
    Update strategy parameters (persisted to file).

    Args:
        params: New strategy parameters

    Returns:
        Updated strategy parameters
    """
    params_dict = {
        'trend': params.trend.dict(),
        'bottom': params.bottom.dict(),
        'kelly': params.kelly.dict(),
        'stop_loss': params.stop_loss.dict()
    }
    _save_params_to_file(params_dict)
    return params


@router.delete("/strategy/params")
async def reset_strategy_params() -> dict:
    """
    Reset strategy parameters to defaults.

    Returns:
        Default strategy parameters
    """
    if STRATEGY_PARAMS_FILE.exists():
        STRATEGY_PARAMS_FILE.unlink()
    return DEFAULT_PARAMS

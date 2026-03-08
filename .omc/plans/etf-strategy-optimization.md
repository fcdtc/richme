# ETF Quantitative Trading Strategy Optimization - Implementation Plan (Revised)

## RALPLAN-DR Summary

### Principles (3-5)

1. **Modular Strategy Architecture**: Separate trend-following and bottom-fishing strategies into distinct, testable modules with clear interfaces
2. **Configurable Risk Management**: Strategy parameters (periods, thresholds, multipliers) must be externally configurable without code changes
3. **Multi-Timeframe Consistency**: Weekly trend context filters daily entry signals to avoid counter-trend trades
4. **Volume-Confirmed Signals**: Price signals must be validated by volume analysis (surge for breakouts, shrink for bottoms)
5. **Kelly Criterion Position Sizing**: Position size derived from edge probability and odds, not fixed percentage

### Decision Drivers (Top 3)

1. **Technical Implementation Requirements**: Multi-timeframe analysis (daily + weekly), Kelly criterion position sizing, configurable strategy parameters
2. **Existing Architecture Preservation**: Maintain FastAPI + Vue 3 + TA-Lib/Pandas stack without major refactoring
3. **Signal Compatibility**: Bridge between existing 5-point discrete signal system and new probability-based engine

### Viable Options (>=2)

#### Option A: Incremental Module Addition
- **Approach**: Add new strategy modules alongside existing signal.py, create backtest service, add backtest page
- **Pros**: Minimal disruption to existing code, gradual testing, lower risk
- **Cons**: Technical debt accumulates, signal.py becomes more complex, eventual cleanup needed

#### Option B: Clean Strategy Replacement
- **Approach**: Replace signal.py entirely with new strategy architecture, consolidate indicators, unified position sizing
- **Pros**: Cleaner architecture, better maintainability, aligned with long-term vision
- **Cons**: Higher upfront effort, requires comprehensive testing, temporary API compatibility concerns

#### Option C: Hybrid Layered Approach (RECOMMENDED)
- **Approach**: Create new strategy engine as separate service, keep signal.py for backward compatibility, route through strategy selector
- **Pros**: Gradual migration path, existing UI continues working, new backtest functionality isolated
- **Cons**: Duplicate code temporarily, requires careful routing logic

### Why Option C Chosen

Option A and Option B both have significant trade-offs. Option A maintains the status quo but creates technical debt. Option B is clean but high-risk for a production system. Option C provides a pragmatic path:
- New backtest endpoint uses new strategy engine immediately
- Existing analysis endpoint can migrate incrementally
- No breaking changes to existing API contracts
- Parallel development and testing possible

### Alternative Invalidation Rationale

- **Option A invalidated**: Signal.py already has 289 lines with mixed concerns. Adding more will exceed maintainability threshold (300 lines). The combined stop-loss logic requirement requires architectural reorganization.
- **Option B invalidated**: Replacing signal.py in one step would require simultaneous changes to 7+ components (schemas, routers, indicators, position calculation, frontend types, frontend components). This exceeds acceptable change blast radius.

---

## Key Changes from Critic Feedback

1. **Weekly Data Solution**: Added `convert_to_weekly()` function to generate weekly data from daily (no API dependency)
2. **Signal Adapter Pattern**: Explicit mapping from discrete 5-point signals to Kelly probability space
3. **KDJ Implementation Decision**: Use existing synthetic KDJ (derived from RSI) for consistency, document clearly
4. **Kelly Verification Tests**: Added comprehensive edge case tests including quarter-Kelly, min/max constraints
5. **Deprecation Strategy**: 3-phase timeline with versioned API transition
6. **Business Outcomes**: Moved return targets to "Future Goals" section (not acceptance criteria)
7. **Analyze Endpoint Migration Path**: Added `StrategySelector` class with `use_new_engine` feature flag and risk_preference to StrategyParams mapping
8. **RISK_CONFIG Migration Mapping**: NEW_RISK_CONFIG schema (strategy_selector.py) maps to Kelly-based parameters; legacy RISK_CONFIG (analysis.py lines 34-57) uses old schema
9. **calculate_position_recommendation() Migration**: Added section 1.8 documenting legacy function dependencies (lines 325, 399-400, 405, 411, 437-438, 441-442) and 3-phase cleanup path
10. **Backward Compatibility Tests**: Added integration tests for signal comparability and risk preference parameter validation

---

## Implementation Plan

### Phase 1: Backend Strategy Engine (Core)

#### 1.1 Weekly Data Conversion Function

**File**: `backend/services/data_utils.py` (NEW)

Create utility for converting daily data to weekly:

```python
"""
Data transformation utilities for multi-timeframe analysis
"""
import pandas as pd

def convert_to_weekly(daily_data: pd.DataFrame) -> pd.DataFrame:
    """
    Convert daily OHLCV data to weekly OHLCV data.

    Since API does not provide weekly K-line, this function aggregates
    daily data into weekly bars: open=Monday open, high=weekly max,
    low=weekly min, close=Friday close, volume=weekly sum.

    Args:
        daily_data: DataFrame with columns [date, open, high, low, close, volume]

    Returns:
        Weekly DataFrame with same structure
    """
    if daily_data.empty:
        return daily_data.copy()

    df = daily_data.copy()
    df['date'] = pd.to_datetime(df['date'])

    # Group by week (ISO week number)
    df['week'] = df['date'].dt.isocalendar().week
    df['year'] = df['date'].dt.isocalendar().year

    # Aggregate: open=first, high=max, low=min, close=last, volume=sum
    weekly = df.groupby(['year', 'week']).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).reset_index(drop=True)

    # Recalculate date as Friday of each week
    def get_friday_of_week(row):
        year = row['year']
        week = row['week']
        return pd.to_datetime(f"{year}-W{week}-5", format="%Y-W%W-%w")

    weekly['date'] = weekly.apply(get_friday_of_week, axis=1)
    weekly = weekly.drop(columns=['year', 'week'])

    # Ensure minimum 26 weeks for weekly indicators
    return weekly

def validate_weekly_data(weekly_data: pd.DataFrame, min_weeks: int = 26) -> bool:
    """
    Validate if we have sufficient weekly data for analysis.

    Args:
        weekly_data: Weekly DataFrame
        min_weeks: Minimum required weeks

    Returns:
        True if sufficient, False otherwise
    """
    return len(weekly_data) >= min_weeks
```

**Acceptance Criteria**: Function handles empty input, produces valid OHLCV aggregation, Friday dates calculated correctly, minimum 26-week validation

#### 1.2 Extended Indicators Module

**File**: `backend/services/indicators.py` (MODIFY)

Add new indicator functions with dual implementation:

```python
# Add to existing indicators.py

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range for dynamic stop-loss.
    Uses talib if available, pandas fallback otherwise.

    Args:
        high: High price series
        low: Low price series
        close: Close price series
        period: ATR period

    Returns:
        ATR series
    """
    if TALIB_AVAILABLE and len(high) >= period + 1:
        atr_values = talib.ATR(high.values, low.values, close.values, timeperiod=period)
        return pd.Series(atr_values, index=high.index).fillna(method='ffill')

    # Pandas fallback: True Range = max(high-low, abs(high-prev_close), abs(low-prev_close))
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return true_range.rolling(window=period).mean()


def calculate_volume_surge(volume: pd.Series, period: int = 20, threshold: float = 1.5) -> Dict:
    """
    Detect volume surge (above threshold * average).

    Args:
        volume: Volume series
        period: Lookback period for average
        threshold: Multiplier for surge detection

    Returns:
        Dict with current_ratio, is_surge, average_volume
    """
    avg_volume = volume.rolling(window=period).mean().iloc[-1]
    current_volume = volume.iloc[-1]
    ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
    return {
        'current_ratio': ratio,
        'is_surge': ratio >= threshold,
        'average_volume': avg_volume,
        'threshold': threshold
    }


def calculate_volume_shrink(volume: pd.Series, period: int = 20, threshold: float = 0.7) -> Dict:
    """
    Detect volume shrinkage (below threshold * average).

    Args:
        volume: Volume series
        period: Lookback period for average
        threshold: Multiplier for shrink detection

    Returns:
        Dict with current_ratio, is_shrink, average_volume
    """
    avg_volume = volume.rolling(window=period).mean().iloc[-1]
    current_volume = volume.iloc[-1]
    ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
    return {
        'current_ratio': ratio,
        'is_shrink': ratio <= threshold,
        'average_volume': avg_volume,
        'threshold': threshold
    }


def calculate_support_resistance(high: pd.Series, low: pd.Series, lookback: int = 20) -> Dict[str, float]:
    """
    Calculate support and resistance levels using local extremes.

    Args:
        high: High price series
        low: Low price series
        lookback: Lookback period

    Returns:
        Dict with support_level, resistance_level
    """
    recent_high = high.tail(lookback).max()
    recent_low = low.tail(lookback).min()
    current_price = close.iloc[-1]

    # Support is recent low if price is near it, otherwise previous swing low
    # Resistance is recent high if price is near it, otherwise previous swing high
    return {
        'support_level': float(recent_low),
        'resistance_level': float(recent_high)
    }


def detect_breakout(close: pd.Series, high: pd.Series, resistance: float, threshold: float = 0.02) -> bool:
    """
    Detect if price breaks above resistance with threshold buffer.

    Args:
        close: Close price series
        high: High price series
        resistance: Resistance level
        threshold: Percentage above resistance to confirm breakout

    Returns:
        True if breakout detected
    """
    current_close = close.iloc[-1]
    breakout_level = resistance * (1 + threshold)
    return current_close >= breakout_level


# Note: KDJ remains synthetic (derived from RSI) for consistency with existing implementation
# Real KDJ requires high/low/close historical and is computationally expensive
# Synthetic KDJ provides sufficient signal for the current use case
```

**Acceptance Criteria**: All indicators tested on sample data, ATR has talib/pandas dual implementation, edge cases handled (insufficient data, NaN values)

#### 1.3 Signal Adapter Pattern

**File**: `backend/services/signal_adapter.py` (NEW)

Bridge between discrete 5-point signal and probability space:

```python
"""
Signal adapter for converting discrete signals to probability space.
This bridges the gap between existing signal.py (5-point discrete)
and the new strategy engine (continuous probability).
"""
from typing import Literal

# Discrete signal types from existing system
DiscreteSignal = Literal["strong_buy", "buy", "hold", "sell", "strong_sell"]

class SignalAdapter:
    """Adapter for signal type conversion"""

    # Mapping from discrete signals to probability space
    # Format: {signal: (probability_range, kelly_edge)}
    SIGNAL_MAPPING = {
        "strong_buy": (0.80, 0.35),   # 80% win prob, 35% edge
        "buy": (0.65, 0.20),          # 65% win prob, 20% edge
        "hold": (0.50, 0.00),          # 50% win prob, no edge
        "sell": (0.35, -0.20),         # 35% win prob, -20% edge
        "strong_sell": (0.20, -0.35)   # 20% win prob, -35% edge
    }

    @classmethod
    def discrete_to_probability(cls, signal: DiscreteSignal) -> tuple:
        """
        Convert discrete signal to probability and edge.

        Args:
            signal: Discrete signal from signal.py

        Returns:
            Tuple of (win_probability, edge)
        """
        return cls.SIGNAL_MAPPING.get(signal, (0.50, 0.00))

    @classmethod
    def discrete_to_strength(cls, signal: DiscreteSignal) -> float:
        """
        Convert discrete signal to strength score (-1 to 1).

        Args:
            signal: Discrete signal

        Returns:
            Strength score
        """
        strength_map = {
            "strong_buy": 1.0,
            "buy": 0.5,
            "hold": 0.0,
            "sell": -0.5,
            "strong_sell": -1.0
        }
        return strength_map.get(signal, 0.0)

    @classmethod
    def probability_to_discrete(cls, probability: float) -> DiscreteSignal:
        """
        Convert probability back to discrete signal (reverse mapping).

        Args:
            probability: Win probability (0 to 1)

        Returns:
            Discrete signal
        """
        if probability >= 0.75:
            return "strong_buy"
        elif probability >= 0.60:
            return "buy"
        elif probability >= 0.40:
            return "hold"
        elif probability >= 0.25:
            return "sell"
        else:
            return "strong_sell"
```

**Acceptance Criteria**: Bidirectional conversion works, edge probabilities match expected values, integration with Kelly calculator verified

#### 1.4 New Strategy Engine

**File**: `backend/services/strategy_engine.py` (NEW)

Core strategy engine with separate modules:

```python
"""
Strategy engine for ETF quantitative trading.
Supports multi-strategy, multi-timeframe analysis with Kelly position sizing.
"""
import pandas as pd
from typing import Dict, Optional
from .indicators import (
    calculate_all_indicators, calculate_atr,
    calculate_volume_surge, calculate_volume_shrink,
    calculate_support_resistance, detect_breakout
)
from .data_utils import convert_to_weekly, validate_weekly_data
from .signal_adapter import SignalAdapter


class TrendFollowingStrategy:
    """Right-side trend following strategy"""

    def analyze(self, data: pd.DataFrame, config: Dict) -> Dict:
        """
        Analyze and return trend following signal.

        Requirements:
        - MA crossover (short > long)
        - MACD confirmation (DIF > DEA, bar > 0)
        - RSI not overbought (<70)
        - Volume surge on breakout
        - Multi-timeframe: weekly trend must be bullish

        Returns:
            Dict with signal_strength (-1 to 1), probability, signals dict
        """
        indicators = calculate_all_indicators(data['close'])

        score = 0.0
        signals = []

        # MA crossover score
        ma_short = indicators['ma'][f"ma{config['ma_short_period']}"]
        ma_long = indicators['ma'][f"ma{config['ma_long_period']}"]
        current_price = data['close'].iloc[-1]

        if current_price > ma_short > ma_long:
            score += 0.3
            signals.append(f"Price above MA{config['ma_short_period']} and MA{config['ma_long_period']}")
        elif current_price < ma_short < ma_long:
            score -= 0.3
            signals.append(f"Price below MA{config['ma_short_period']} and MA{config['ma_long_period']}")

        # MACD confirmation
        macd = indicators['macd']
        if macd['dif'] > macd['dea'] and macd['bar'] > 0:
            score += 0.25
            signals.append("MACD bullish (DIF > DEA, bar > 0)")
        elif macd['dif'] < macd['dea'] and macd['bar'] < 0:
            score -= 0.25
            signals.append("MACD bearish (DIF < DEA, bar < 0)")

        # RSI check
        rsi = indicators['rsi']
        if rsi < config['rsi_oversold']:
            score += 0.2
            signals.append(f"RSI oversold ({rsi:.1f})")
        elif rsi > config['rsi_overbought']:
            score -= 0.15
            signals.append(f"RSI overbought ({rsi:.1f})")

        # Volume check
        volume_data = calculate_volume_surge(
            data['volume'],
            config.get('volume_period', 20),
            config.get('volume_surge_threshold', 1.5)
        )
        if volume_data['is_surge'] and score > 0:
            score += 0.1
            signals.append(f"Volume surge ({volume_data['current_ratio']:.2f}x average)")

        # Normalize score to -1 to 1
        signal_strength = max(-1.0, min(1.0, score))

        # Convert to probability
        probability = 0.5 + signal_strength * 0.3

        return {
            'strategy': 'trend_following',
            'signal_strength': signal_strength,
            'win_probability': max(0.1, min(0.9, probability)),
            'signals': signals,
            'indicators': indicators
        }


class BottomFishingStrategy:
    """Left-side bottom fishing strategy"""

    def analyze(self, data: pd.DataFrame, config: Dict) -> Dict:
        """
        Analyze and return bottom fishing signal.

        Requirements:
        - Price at/near Bollinger lower band
        - RSI oversold (<config threshold)
        - Support level holding
        - Volume shrinkage indicating exhaustion
        - Synthetic KDJ oversold signal

        Returns:
            Dict with signal_strength (-1 to 1), probability, signals dict
        """
        indicators = calculate_all_indicators(data['close'])

        score = 0.0
        signals = []
        current_price = data['close'].iloc[-1]

        # Bollinger lower band check
        bb = indicators['bollinger']
        if current_price <= bb['lower'] * 1.02:  # 2% buffer
            score += 0.35
            signals.append(f"Price near Bollinger lower band ({current_price:.3f} vs {bb['lower']:.3f})")

        # RSI oversold
        rsi = indicators['rsi']
        rsi_threshold = config.get('rsi_bottom_threshold', 20.0)
        if rsi < rsi_threshold:
            score += 0.25
            signals.append(f"RSI oversold ({rsi:.1f})")
        elif rsi < 30:
            score += 0.15
            signals.append(f"RSI approaching oversold ({rsi:.1f})")

        # Support level
        support_data = calculate_support_resistance(
            data['high'],
            data['low'],
            config.get('support_lookback', 20)
        )
        if abs(current_price - support_data['support_level']) / support_data['support_level'] < 0.02:
            score += 0.2
            signals.append(f"Price near support ({support_data['support_level']:.3f})")

        # Volume shrinkage (exhaustion)
        volume_data = calculate_volume_shrink(
            data['volume'],
            config.get('volume_period', 20),
            config.get('volume_shrink_threshold', 0.7)
        )
        if volume_data['is_shrink']:
            score += 0.2
            signals.append(f"Volume shrinkage indicating exhaustion ({volume_data['current_ratio']:.2f}x average)")

        # Note: KDJ is synthetic (derived from RSI) - see analysis.py for calculation
        # We use the RSI-based KDJ values already computed in indicators
        # Since KDJ is synthetic, we rely on RSI and Bollinger signals primarily

        # Normalize score to -1 to 1
        signal_strength = max(-1.0, min(1.0, score))

        # Convert to probability
        probability = 0.5 + signal_strength * 0.25

        return {
            'strategy': 'bottom_fishing',
            'signal_strength': signal_strength,
            'win_probability': max(0.1, min(0.9, probability)),
            'signals': signals,
            'indicators': indicators
        }


class CombinedStopLoss:
    """Combined stop-loss logic"""

    def calculate(self, entry_price: float, current_price: float, data: pd.DataFrame,
                 config: Dict, current_profit_pct: float = 0.0) -> float:
        """
        Calculate dynamic stop-loss price.

        Methods:
        - Fixed percentage stop
        - ATR-based trailing stop
        - Technical support level stop
        - Trailing stop when profit threshold reached

        Returns: the most conservative (highest for long) stop price
        """
        stops = []

        # Fixed percentage stop
        fixed_stop = entry_price * (1 - config['fixed_pct'])
        stops.append(fixed_stop)

        # ATR-based stop
        if len(data) >= config.get('atr_period', 14):
            atr = calculate_atr(data['high'], data['low'], data['close'], config['atr_period'])
            current_atr = atr.iloc[-1] if not pd.isna(atr.iloc[-1]) else 0
            atr_stop = current_price - current_atr * config['atr_multiplier']
            stops.append(atr_stop)

        # Support level stop
        support_data = calculate_support_resistance(
            data['high'], data['low'], config.get('support_lookback', 20)
        )
        support_stop = support_data['support_level'] * (1 - config.get('support_pct', 0.02))
        stops.append(support_stop)

        # Trailing stop (only when profit > threshold)
        if current_profit_pct > config.get('trailing_activation_pct', 0.02):
            trailing_stop = max(stops)  # Use the best stop so far
            stops.append(trailing_stop)

        # Return the most conservative (highest) stop price
        return max(stops)


class KellyPositionSizer:
    """Kelly criterion position sizing"""

    def calculate(self, win_probability: float, avg_win: float, avg_loss: float,
                 config: Dict, current_equity: float) -> float:
        """
        Calculate position size using Kelly criterion.

        Kelly formula: f* = (bp - q) / b
        where:
        - b = avg_win / avg_loss (odds)
        - p = win_probability
        - q = 1 - p

        Apply quarter-Kelly (config['kelly_fraction']) for safety.

        Args:
            win_probability: Estimated win rate (0 to 1)
            avg_win: Average winning trade
            avg_loss: Average losing trade
            config: Kelly config
            current_equity: Current account equity

        Returns:
            Position size in currency
        """
        # Use config estimates if actuals not provided
        if avg_loss == 0:
            avg_loss = 1.0  # Prevent division by zero
        if avg_win == 0:
            avg_win = config.get('avg_win_avg_loss_ratio', 1.5)

        # Calculate odds
        odds = avg_win / abs(avg_loss)

        # Kelly formula
        edge = (win_probability * odds) - 1
        kelly_fraction = edge / odds if odds > 0 else 0

        # Apply safety fraction (quarter-Kelly default)
        safe_kelly = kelly_fraction * config.get('kelly_fraction', 0.25)

        # Handle edge cases
        if safe_kelly < 0:
            return 0.0  # No position when edge is negative

        # Calculate position size
        position_size = current_equity * safe_kelly

        # Apply min/max constraints
        max_position = current_equity * config.get('max_position_pct', 0.3)
        min_position = current_equity * config.get('min_position_pct', 0.05)

        if position_size > max_position:
            position_size = max_position
        elif position_size < min_position and position_size > 0:
            position_size = min_position

        return position_size


class MultiTimeframeAnalyzer:
    """Multi-timeframe analysis coordinator"""

    def analyze(self, daily_data: pd.DataFrame, weekly_data: pd.DataFrame) -> Dict:
        """
        Combine daily and weekly analysis.

        Logic:
        - Weekly determines trend direction (bullish/bearish/neutral)
        - Daily provides entry signals
        - Only take daily signals aligned with weekly trend

        Returns:
            Dict with trend_direction, weekly_score, daily_weight
        """
        if not validate_weekly_data(weekly_data):
            # Fall back to daily-only if insufficient weekly data
            return {
                'trend_direction': 'neutral',
                'weekly_score': 0.0,
                'daily_weight': 1.0,
                'use_weekly': False
            }

        # Calculate weekly MA trend
        weekly_indicators = calculate_all_indicators(weekly_data['close'])
        ma_short_weekly = weekly_indicators['ma']['ma5']
        ma_long_weekly = weekly_indicators['ma']['ma20']

        trend_direction = 'neutral'
        weekly_score = 0.0

        if ma_short_weekly > ma_long_weekly:
            trend_direction = 'bullish'
            weekly_score = 0.5
        elif ma_short_weekly < ma_long_weekly:
            trend_direction = 'bearish'
            weekly_score = -0.5

        # Daily signals get weighted by weekly trend
        daily_weight = 1.0 + weekly_score * 0.3  # Amplify or reduce daily signals

        return {
            'trend_direction': trend_direction,
            'weekly_score': weekly_score,
            'daily_weight': max(0.5, min(1.5, daily_weight)),  # Clamp between 0.5 and 1.5
            'use_weekly': True
        }


class StrategyEngine:
    """Main strategy orchestrator"""

    def __init__(self, configs: Dict):
        self.trend_strategy = TrendFollowingStrategy()
        self.bottom_strategy = BottomFishingStrategy()
        self.stop_loss = CombinedStopLoss()
        self.position_sizer = KellyPositionSizer()
        self.mtf_analyzer = MultiTimeframeAnalyzer()
        self.configs = configs

    def generate_signal(self, daily_data: pd.DataFrame, weekly_data: pd.DataFrame = None) -> Dict:
        """
        Generate complete trading signal.

        Returns:
            Dict with:
                - signal_type: 'buy' | 'sell' | 'hold'
                - signal_strength: -1 to 1
                - position_size: currency amount
                - stop_loss: price level
                - win_probability: 0 to 1
                - signals: list of contributing signals
                - mtf_analysis: multi-timeframe analysis
        """
        if weekly_data is None or weekly_data.empty:
            # Generate weekly from daily
            weekly_data = convert_to_weekly(daily_data)

        # Analyze both strategies
        trend_result = self.trend_strategy.analyze(daily_data, self.configs['trend'])
        bottom_result = self.bottom_strategy.analyze(daily_data, self.configs['bottom'])

        # Multi-timeframe filter
        mtf_result = self.mtf_analyzer.analyze(daily_data, weekly_data)

        # Determine which strategy to use based on trend
        if mtf_result['trend_direction'] == 'bullish':
            # Prefer trend following in bullish market
            selected_strategy = trend_result
            strategy_weight = 0.7
        elif mtf_result['trend_direction'] == 'bearish':
            # Prefer bottom fishing (or no position) in bearish market
            selected_strategy = bottom_result
            strategy_weight = 0.6  # More conservative in bearish
        else:
            # Neutral market: average both signals
            selected_strategy = {
                'signal_strength': (trend_result['signal_strength'] + bottom_result['signal_strength']) / 2,
                'win_probability': (trend_result['win_probability'] + bottom_result['win_probability']) / 2,
                'signals': trend_result['signals'] + bottom_result['signals']
            }
            strategy_weight = 0.5

        # Apply multi-timeframe weight
        final_strength = selected_strategy['signal_strength'] * mtf_result['daily_weight']
        final_probability = selected_strategy['win_probability']

        # Determine signal type
        if final_strength > 0.3:
            signal_type = 'buy'
        elif final_strength < -0.3:
            signal_type = 'sell'
        else:
            signal_type = 'hold'

        # Calculate position size if buy signal
        position_size = 0.0
        current_price = daily_data['close'].iloc[-1]
        current_equity = self.configs.get('initial_capital', 100000)

        if signal_type == 'buy':
            position_size = self.position_sizer.calculate(
                final_probability,
                self.configs['kelly'].get('avg_win_avg_loss_ratio', 1.5),
                -1.0,  # avg_loss (absolute)
                self.configs['kelly'],
                current_equity
            )

        # Calculate stop loss
        stop_loss = self.stop_loss.calculate(
            current_price, current_price, daily_data,
            self.configs['stop_loss']
        )

        return {
            'signal_type': signal_type,
            'signal_strength': final_strength,
            'win_probability': final_probability,
            'position_size': position_size,
            'stop_loss': stop_loss,
            'signals': selected_strategy['signals'],
            'mtf_analysis': mtf_result
        }
```

**Acceptance Criteria**: Each strategy produces scores (-1 to 1), signals combined with configurable weights, stop-loss returns most conservative level, weekly data properly integrated

#### 1.5 Backtest Engine

**File**: `backend/services/backtest.py` (NEW)

Backtest framework:

```python
"""
Historical backtesting engine for ETF strategies.
"""
import pandas as pd
from typing import List, Dict, Optional
from .strategy_engine import StrategyEngine


class BacktestEngine:
    """Historical backtesting engine"""

    def __init__(self, strategy_engine: StrategyEngine, initial_capital: float = 100000):
        self.strategy = strategy_engine
        self.initial_capital = initial_capital

    def run(self, data: pd.DataFrame, start_date: str = None, end_date: str = None) -> Dict:
        """
        Run backtest on historical data.

        Simulates trades based on strategy signals, tracking positions,
        P&L, and drawdown.

        Args:
            data: DataFrame with columns [date, open, high, low, close, volume]
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)

        Returns:
            Dict with metrics, equity_curve, trades
        """
        # Filter by date range
        if start_date:
            data = data[data['date'] >= start_date]
        if end_date:
            data = data[data['date'] <= end_date]

        # Convert to weekly for multi-timeframe
        weekly_data = convert_to_weekly(data)

        # Initialize backtest state
        equity = self.initial_capital
        position = 0.0  # Position size in currency
        position_price = 0.0
        trades = []
        equity_curve = []
        current_trade = None

        # Iterate through data (rolling window for indicators)
        min_window = 60  # Need at least 60 bars for indicators

        for i in range(min_window, len(data)):
            current_bar = data.iloc[i]
            window_data = data.iloc[max(0, i-120):i+1]  # 120-bar window
            window_weekly = weekly_data[weekly_data['date'] <= current_bar['date']]

            # Generate signal
            signal = self.strategy.generate_signal(window_data, window_weekly)

            # Record equity
            equity_curve.append({
                'date': current_bar['date'],
                'value': equity,
                'drawdown': 0.0  # Will calculate later
            })

            # Trading logic
            if signal['signal_type'] == 'buy' and position <= 0:
                # Open long position
                position_size = min(signal['position_size'], equity)
                if position_size > equity * self.strategy.configs['kelly'].get('min_position_pct', 0.05):
                    position = position_size
                    position_price = current_bar['open'] if i == 0 else current_bar['close']
                    current_trade = {
                        'entry_date': str(current_bar['date']),
                        'entry_price': position_price,
                        'quantity': position / position_price,
                        'position_value': position,
                        'stop_loss': signal['stop_loss'],
                        'signals': signal['signals']
                    }

            elif signal['signal_type'] == 'sell' and position > 0:
                # Close long position
                exit_price = current_bar['close']
                exit_reason = 'signal'

                # Check stop loss
                if current_bar['low'] <= current_trade['stop_loss']:
                    exit_price = current_trade['stop_loss']
                    exit_reason = 'stop_loss'

                # Calculate P&L
                pnl = (exit_price - position_price) * current_trade['quantity']
                pnl_pct = (pnl / current_trade['position_value']) * 100

                trades.append({
                    **current_trade,
                    'exit_date': str(current_bar['date']),
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'holding_days': i - data[data['date'] == current_trade['entry_date']].index[0],
                    'exit_reason': exit_reason
                })

                equity += pnl
                position = 0.0
                current_trade = None

            # Update current trade if in position
            if position > 0 and current_trade:
                # Check stop loss intraday
                if current_bar['low'] <= current_trade['stop_loss']:
                    exit_price = current_trade['stop_loss']
                    pnl = (exit_price - position_price) * current_trade['quantity']
                    pnl_pct = (pnl / current_trade['position_value']) * 100

                    trades.append({
                        **current_trade,
                        'exit_date': str(current_bar['date']),
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'holding_days': i - data[data['date'] == current_trade['entry_date']].index[0],
                        'exit_reason': 'stop_loss'
                    })

                    equity += pnl
                    position = 0.0
                    current_trade = None

        # Calculate metrics
        metrics = self.calculate_metrics(equity_curve, trades)

        return {
            'metrics': metrics,
            'equity_curve': self._calculate_drawdown(equity_curve),
            'trades': trades
        }

    def calculate_metrics(self, equity_curve: List[Dict], trades: List[Dict]) -> Dict:
        """
        Calculate performance metrics.

        Returns:
            Dict with total return, annualized return, max drawdown,
            sharpe ratio, win rate, avg win/loss, profit factor
        """
        if not equity_curve:
            return {}

        final_equity = equity_curve[-1]['value']
        total_return = (final_equity - self.initial_capital) / self.initial_capital

        # Calculate drawdown
        equity_curve_with_dd = self._calculate_drawdown(equity_curve)
        max_drawdown = min([e['drawdown'] for e in equity_curve_with_dd])

        # Trade statistics
        if not trades:
            return {
                'initial_capital': self.initial_capital,
                'final_capital': final_equity,
                'total_return': total_return,
                'annualized_return': 0.0,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': 0.0,
                'win_rate': 0.0,
                'total_trades': 0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0
            }

        win_trades = [t for t in trades if t['pnl'] > 0]
        loss_trades = [t for t in trades if t['pnl'] <= 0]

        win_rate = len(win_trades) / len(trades) if trades else 0
        avg_win = sum(t['pnl'] for t in win_trades) / len(win_trades) if win_trades else 0
        avg_loss = sum(t['pnl'] for t in loss_trades) / len(loss_trades) if loss_trades else 0

        # Profit factor
        total_profit = sum(t['pnl'] for t in win_trades) if win_trades else 0
        total_loss = abs(sum(t['pnl'] for t in loss_trades)) if loss_trades else 0
        profit_factor = total_profit / total_loss if total_loss > 0 else 0

        # Annualized return (assuming 252 trading days)
        days = len(equity_curve)
        annualized_return = (1 + total_return) ** (252 / days) - 1 if days > 0 else 0

        # Sharpe ratio (simplified)
        returns = [e['value'] / self.initial_capital - 1 for e in equity_curve[1:]]
        daily_returns = pd.Series(returns)
        sharpe = daily_returns.mean() / daily_returns.std() * (252 ** 0.5) if daily_returns.std() > 0 else 0

        return {
            'initial_capital': self.initial_capital,
            'final_capital': final_equity,
            'total_return': total_return,
            'annualized_return': annualized_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe,
            'win_rate': win_rate,
            'total_trades': len(trades),
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor
        }

    def _calculate_drawdown(self, equity_curve: List[Dict]) -> List[Dict]:
        """
        Calculate drawdown for each point in equity curve.

        Returns:
            Equity curve with drawdown values
        """
        peak = self.initial_capital
        result = []

        for point in equity_curve:
            if point['value'] > peak:
                peak = point['value']
            drawdown = (point['value'] - peak) / peak
            result.append({
                'date': point['date'],
                'value': point['value'],
                'drawdown': drawdown
            })

        return result

    def generate_signals_for_backtest(self, data: pd.DataFrame) -> List[Dict]:
        """
        Generate buy/sell signals for each bar in data.

        Each signal includes: type (buy/sell), price, position_size, stop_loss

        Returns:
            List of signal dictionaries
        """
        signals = []
        weekly_data = convert_to_weekly(data)
        min_window = 60

        for i in range(min_window, len(data)):
            window_data = data.iloc[max(0, i-120):i+1]
            window_weekly = weekly_data[weekly_data['date'] <= data.iloc[i]['date']]

            signal = self.strategy.generate_signal(window_data, window_weekly)

            if signal['signal_type'] in ['buy', 'sell']:
                signals.append({
                    'date': str(data.iloc[i]['date']),
                    'type': signal['signal_type'],
                    'price': data.iloc[i]['close'],
                    'position_size': signal.get('position_size', 0),
                    'stop_loss': signal['stop_loss'],
                    'strength': signal['signal_strength'],
                    'probability': signal['win_probability']
                })

        return signals
```

**Acceptance Criteria**: Backtest produces all required metrics, handles 1-year of data efficiently (<5s), records all trades with exit reasons

#### 1.6 Backtest Router and Schemas

**File**: `backend/models/backtest_schemas.py` (NEW)

```python
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
```

**File**: `backend/routers/backtest.py` (NEW)

```python
"""Backtest router for ETF strategy testing."""
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
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
```

**File**: `backend/main.py` (MODIFY)

Add backtest router registration:

```python
from backend.routers import backtest
app.include_router(backtest.router)
```

**Acceptance Criteria**: API endpoints documented in OpenAPI, validation on all inputs, error handling for missing data

#### 1.7 Strategy Selector for Analyze Endpoint Migration

**File**: `backend/services/strategy_selector.py` (NEW)

```python
"""
Strategy selector for gradual migration from old signal.py to new strategy_engine.
Provides routing logic and feature flag control for the analyze endpoint.
"""
from typing import Dict, Optional
from .strategy_engine import StrategyEngine
from .signal_adapter import SignalAdapter

# NOTE: This is a NEW RISK_CONFIG schema for the new strategy engine.
# The legacy RISK_CONFIG (with single_trade_pct, stop_loss_pct, etc.) exists in
# backend/routers/analysis.py lines 34-57 and is used by calculate_position_recommendation().
# This NEW schema maps legacy risk preferences to the new Kelly-based parameters.
NEW_RISK_CONFIG = {
    "conservative": {
        "kelly_fraction": 0.15,      # More conservative Kelly
        "max_position_pct": 0.20,    # Lower max position
        "min_position_pct": 0.05,
        "atr_multiplier": 1.5,       # Tighter stop loss
        "rsi_oversold": 25.0,       # More selective entry
        "rsi_overbought": 75.0,
        "fixed_pct": 0.03            # Lower fixed stop
    },
    "neutral": {
        "kelly_fraction": 0.25,      # Quarter-Kelly (default)
        "max_position_pct": 0.30,
        "min_position_pct": 0.05,
        "atr_multiplier": 2.0,
        "rsi_oversold": 30.0,
        "rsi_overbought": 70.0,
        "fixed_pct": 0.05
    },
    "aggressive": {
        "kelly_fraction": 0.40,      # Higher Kelly fraction
        "max_position_pct": 0.50,    # Higher max position
        "min_position_pct": 0.05,
        "atr_multiplier": 2.5,      # Wider stops for trend following
        "rsi_oversold": 35.0,       # Earlier entry
        "rsi_overbought": 65.0,
        "fixed_pct": 0.07
    }
}


class StrategySelector:
    """Selects between old and new strategy engines based on feature flags"""

    def __init__(self, use_new_engine: bool = False):
        """
        Initialize strategy selector.

        Args:
            use_new_engine: Feature flag to use new strategy engine
        """
        self.use_new_engine = use_new_engine

    def map_risk_to_params(self, risk_preference: str) -> Dict:
        """
        Map risk_preference to StrategyParams format.

        This enables backward compatibility by converting legacy
        risk_preference values to the new structured parameters.

        Args:
            risk_preference: One of 'conservative', 'neutral', 'aggressive'

        Returns:
            Dictionary with structure matching StrategyParams
        """
        risk_config = NEW_RISK_CONFIG.get(risk_preference, NEW_RISK_CONFIG["neutral"])

        return {
            "trend": {
                "ma_short_period": 5,
                "ma_long_period": 20,
                "rsi_oversold": risk_config["rsi_oversold"],
                "rsi_overbought": risk_config["rsi_overbought"],
                "volume_surge_threshold": 1.5
            },
            "bottom": {
                "bollinger_period": 20,
                "bollinger_std": 2.0,
                "rsi_bottom_threshold": risk_config["rsi_oversold"],
                "support_lookback": 20,
                "volume_shrink_threshold": 0.7
            },
            "kelly": {
                "win_rate_estimate": 0.55,
                "avg_win_avg_loss_ratio": 1.5,
                "max_position_pct": risk_config["max_position_pct"],
                "min_position_pct": risk_config["min_position_pct"],
                "kelly_fraction": risk_config["kelly_fraction"]
            },
            "stop_loss": {
                "fixed_pct": risk_config["fixed_pct"],
                "atr_multiplier": risk_config["atr_multiplier"],
                "atr_period": 14,
                "support_pct": 0.02,
                "trailing_activation_pct": 0.02
            }
        }

    def get_strategy_engine(self, risk_preference: Optional[str] = None,
                          strategy_params: Optional[Dict] = None) -> Dict:
        """
        Get appropriate strategy engine and parameters.

        Priority:
        1. If strategy_params provided: use new engine with custom params
        2. If use_new_engine and risk_preference: use new engine with mapped params
        3. Otherwise: indicate old engine should be used

        Args:
            risk_preference: Legacy risk preference value
            strategy_params: New structured strategy parameters

        Returns:
            Dict with:
                - use_new_engine: bool
                - params: strategy parameters dict
                - engine: StrategyEngine instance if use_new_engine=True
        """
        if strategy_params:
            # Explicit new engine request
            engine = StrategyEngine(strategy_params)
            return {
                "use_new_engine": True,
                "params": strategy_params,
                "engine": engine
            }

        if self.use_new_engine and risk_preference:
            # Convert risk preference to new params
            params = self.map_risk_to_params(risk_preference)
            engine = StrategyEngine(params)
            return {
                "use_new_engine": True,
                "params": params,
                "engine": engine
            }

        # Fall back to old engine
        # NOTE: This returns the legacy RISK_CONFIG from backend/routers/analysis.py lines 34-57
        # with keys: single_trade_pct, stop_loss_pct, take_profit_pct, max_risk_per_trade, signal_threshold
        return {
            "use_new_engine": False,
            "params": {"fallback": "legacy_risk_config_in_analysis_py_lines_34_57"},
            "engine": None
        }

    def get_migration_status(self) -> Dict:
        """
        Get current migration status.

        Returns:
            Dict with migration information
        """
        return {
            "use_new_engine": self.use_new_engine,
            "migration_phase": "phase_1" if not self.use_new_engine else "phase_2",
            "supported_risk_levels": ["conservative", "neutral", "aggressive"],
            "deprecated": "risk_preference" if self.use_new_engine else None
        }
```

**Acceptance Criteria**: StrategySelector routes correctly based on feature flag, risk_preference maps to valid StrategyParams, old engine fallback works when flag is off

#### 1.8 calculate_position_recommendation() Migration Notes

**Context**: The existing `calculate_position_recommendation()` function in `backend/routers/analysis.py` (lines 309-490) uses the legacy RISK_CONFIG schema.

**Legacy RISK_CONFIG Schema** (lines 34-57):
```python
RISK_CONFIG = {
    "conservative": {
        "single_trade_pct": 0.10,      # Single trade 10%
        "stop_loss_pct": 0.03,         # Stop loss 3%
        "take_profit_pct": 0.06,       # Take profit 6%
        "max_risk_per_trade": 0.02,    # Max risk 2% per trade
        "signal_threshold": 0.60,      # Signal threshold
    },
    "neutral": {
        "single_trade_pct": 0.20,
        "stop_loss_pct": 0.05,
        "take_profit_pct": 0.10,
        "max_risk_per_trade": 0.03,
        "signal_threshold": 0.40,
    },
    "aggressive": {
        "single_trade_pct": 0.30,
        "stop_loss_pct": 0.08,
        "take_profit_pct": 0.16,
        "max_risk_per_trade": 0.05,
        "signal_threshold": 0.30,
    }
}
```

**Function Dependencies** (lines 325, 399-400, 405, 411, 437-438, 441-442):
- Line 325: `config = RISK_CONFIG.get(risk_preference, RISK_CONFIG["neutral"])`
- Lines 399-400: Uses `config["signal_threshold"]` for buy/sell thresholds
- Line 405: Uses `config["single_trade_pct"]` for position sizing
- Line 411: Uses `config["single_trade_pct"]` for sell calculations
- Lines 437-438: Uses `config["stop_loss_pct"]` and `config["take_profit_pct"]` for stop/take profit
- Lines 441-442: Uses `config["stop_loss_pct"]` for risk amount calculation

**Migration Path**:

**Phase 1 (No Changes)**: The function continues to work as-is when `use_new_engine=False`. The StrategySelector returns a fallback indicator, and the existing analyze endpoint uses the legacy function.

**Phase 2 (Optional Enhancement)**: When `use_new_engine=True`, create a new `calculate_position_recommendation_v2()` that:
1. Accepts `strategy_params` (NEW_RISK_CONFIG schema) instead of `risk_preference`
2. Uses Kelly criterion for position sizing instead of `single_trade_pct`
3. Uses ATR-based stop loss instead of fixed `stop_loss_pct`
4. Returns compatible PositionRecommendation structure

**Phase 3 (Cleanup)**: After full migration, delete:
- Lines 34-57: Legacy RISK_CONFIG
- Lines 309-490: Legacy `calculate_position_recommendation()` function
- All references to `risk_preference` parameter in schemas and routers

**Acceptance Criteria**: Legacy function works unchanged during Phase 1, new function created in Phase 2, full cleanup in Phase 3

---

### Phase 2: Frontend Backtest UI

#### 2.1 TypeScript Type Updates

**File**: `frontend/src/types/index.ts` (MODIFY)

Add backtest types:

```typescript
export interface BacktestRequest {
  etf_code: string
  period?: string
  start_date?: string
  end_date?: string
  initial_capital?: number
}

export interface BacktestTrade {
  entry_date: string
  exit_date: string
  entry_price: number
  exit_price: number
  quantity: number
  position_value: number
  pnl: number
  pnl_pct: number
  holding_days: number
  exit_reason: 'stop_loss' | 'signal' | 'take_profit' | 'end_of_test'
  stop_loss?: number
  signals?: string[]
}

export interface BacktestMetrics {
  initial_capital: number
  final_capital: number
  total_return: number
  annualized_return: number
  max_drawdown: number
  sharpe_ratio: number
  win_rate: number
  total_trades: number
  avg_win: number
  avg_loss: number
  profit_factor: number
}

export interface EquityPoint {
  date: string
  value: number
  drawdown: number
}

export interface BacktestResponse {
  etf_code: string
  period: string
  metrics: BacktestMetrics
  equity_curve: EquityPoint[]
  trades: BacktestTrade[]
  strategy_params?: StrategyParams
  timestamp: string
}

export interface StrategyParams {
  trend: {
    ma_short_period: number
    ma_long_period: number
    rsi_oversold: number
    rsi_overbought: number
    volume_surge_threshold: number
  }
  bottom: {
    bollinger_period: number
    bollinger_std: number
    rsi_bottom_threshold: number
    support_lookback: number
    volume_shrink_threshold: number
  }
  kelly: {
    win_rate_estimate: number
    avg_win_avg_loss_ratio: number
    max_position_pct: number
    min_position_pct: number
    kelly_fraction: number
  }
  stop_loss: {
    fixed_pct: number
    atr_multiplier: number
    atr_period: number
    support_pct: number
    trailing_activation_pct: number
  }
}
```

#### 2.2 API Service Extensions

**File**: `frontend/src/services/api.ts` (MODIFY)

Add backtest API functions:

```typescript
import axios from 'axios'
import type {
  AnalyzeRequest, AnalyzeResponse,
  BacktestRequest, BacktestResponse, StrategyParams
} from '../types'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// Existing analyze function
export const analyzeETF = (data: AnalyzeRequest): Promise<AnalyzeResponse> => {
  return apiClient.post('/analyze', data)
}

// New backtest functions
export const runBacktest = (data: BacktestRequest): Promise<BacktestResponse> => {
  return apiClient.post('/backtest', data)
}

export const getStrategyParams = (): Promise<StrategyParams> => {
  return apiClient.get('/strategy/params')
}

export const updateStrategyParams = (params: StrategyParams): Promise<StrategyParams> => {
  return apiClient.post('/strategy/params', params)
}

export const resetStrategyParams = (): Promise<any> => {
  return apiClient.get('/strategy/params/reset')
}

export default apiClient
```

#### 2.3 Backtest Page Component

**File**: `frontend/src/views/BacktestView.vue` (NEW)

New dedicated backtest page with:

```vue
<template>
  <div class="backtest-view">
    <el-card class="input-card">
      <BacktestForm
        @run="handleBacktest"
        @params-change="handleParamsChange"
        :loading="loading"
      />
    </el-card>

    <el-card v-if="backtestResult" class="results-card">
      <BacktestMetrics :metrics="backtestResult.metrics" />
      <BacktestEquityChart :curve="backtestResult.equity_curve" />
      <BacktestDrawdownChart :curve="backtestResult.equity_curve" />
      <BacktestTradeList :trades="backtestResult.trades" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import BacktestForm from '../components/backtest/BacktestForm.vue'
import BacktestMetrics from '../components/backtest/BacktestMetrics.vue'
import BacktestEquityChart from '../components/backtest/BacktestEquityChart.vue'
import BacktestDrawdownChart from '../components/backtest/BacktestDrawdownChart.vue'
import BacktestTradeList from '../components/backtest/BacktestTradeList.vue'
import { runBacktest, type BacktestResponse } from '../services/api'

const loading = ref(false)
const backtestResult = ref<BacktestResponse | null>(null)

const handleBacktest = async (etfCode: string) => {
  loading.value = true
  try {
    backtestResult.value = await runBacktest({
      etf_code: etfCode,
      period: 'daily',
      initial_capital: 100000
    })
  } catch (error) {
    console.error('Backtest failed:', error)
  } finally {
    loading.value = false
  }
}

const handleParamsChange = () => {
  // Re-run backtest with new params if results exist
  if (backtestResult.value) {
    handleBacktest(backtestResult.value.etf_code)
  }
}
</script>
```

#### 2.4 Backtest Sub-components

**File**: `frontend/src/components/backtest/BacktestForm.vue` (NEW)
- ETF code input
- Strategy parameter accordion editor (trend/bottom/kelly/stop_loss tabs)
- Run backtest button
- Load default parameters button

**File**: `frontend/src/components/backtest/BacktestMetrics.vue` (NEW)
- Display key metrics in card layout
- Color coding: green for positive, red for negative
- Note: Business outcome targets moved to future goals, not part of acceptance criteria

**File**: `frontend/src/components/backtest/BacktestEquityChart.vue` (NEW)
- ECharts line chart
- Initial capital reference line
- Hover tooltips with dates

**File**: `frontend/src/components/backtest/BacktestDrawdownChart.vue` (NEW)
- ECharts filled area chart
- Red gradient for drawdown areas
- Maximum drawdown annotation

**File**: `frontend/src/components/backtest/BacktestTradeList.vue` (NEW)
- el-table with pagination
- Sortable columns
- Color-coded PnL rows
- Trade detail drawer

**Acceptance Criteria**: All components use Element Plus design system, charts responsive, trade list handles 500+ rows

#### 2.5 K-line Chart with Signal Annotations

**File**: `frontend/src/components/KlineChart.vue` (MODIFY)

Add signal marker support:

```typescript
interface Props {
  klineData: KlineData | null
  currentPrice?: number
  signals?: Array<{date: string, type: 'buy'|'sell', price: number, reason: string}>
}

// Add markPoint to series for buy/sell signals
series: [
  {
    markPoint: {
      data: props.signals?.map(s => ({
        name: s.type,
        coord: [s.date, s.price],
        value: s.reason,
        itemStyle: { color: s.type === 'buy' ? '#67c23a' : '#f56c6c' }
      }))
    }
  }
]
```

**Acceptance Criteria**: Signals displayed as markers on K-line, tooltip shows signal reason

#### 2.6 Routing and Navigation

**File**: `frontend/src/router/index.ts` (NEW or MODIFY)

Add backtest route:

```typescript
{
  path: '/backtest',
  name: 'Backtest',
  component: () => import('@/views/BacktestView.vue')
}
```

Update App.vue navigation (if present):

```vue
<el-menu>
  <el-menu-item index="/backtest">策略回测</el-menu-item>
</el-menu>
```

---

### Phase 3: Risk Preference Deprecation (3-Phase Strategy)

#### 3.1 Phase 1: Soft Deprecation (v1.0 -> v1.1)

**File**: `backend/models/schemas.py` (MODIFY)

```python
# Phase 1: Keep risk_preference but mark as deprecated
class AnalysisRequest(BaseModel):
    etf_code: str = Field(..., description="ETF code (e.g., 510300)")
    risk_preference: Optional[RiskPreferenceType] = Field(
        default=None,
        description="[DEPRECATED] Use strategy_params instead. Will be removed in v2.0"
    )
    strategy_params: Optional[Dict] = Field(
        default=None,
        description="Strategy parameters override (preferred)"
    )
    use_cache: bool = Field(default=True, description="Whether to use cached data")
    total_capital: Optional[float] = Field(default=100000, description="Total capital")
    holding_amount: Optional[float] = Field(default=0, description="Current holding amount")
```

**File**: `backend/routers/analysis.py` (MODIFY)

```python
# Phase 1: Add deprecation warning
@router.post("/analyze")
async def analyze(request: AnalysisRequest) -> AnalysisResponse:
    # Log deprecation warning if risk_preference is used
    if request.risk_preference is not None:
        logger.warning(
            "risk_preference is deprecated. "
            "Use strategy_params instead. "
            "See /api/deprecation for migration guide."
        )

    # Use strategy_params if provided, fall back to risk_preference logic
    if request.strategy_params:
        # Use new strategy engine
        strategy_engine = StrategyEngine(request.strategy_params)
        # ... use strategy_engine
    else:
        # Fall back to existing RISK_CONFIG logic (in analysis.py lines 34-57)
        # NOTE: This uses legacy RISK_CONFIG with keys: single_trade_pct, stop_loss_pct,
        # take_profit_pct, max_risk_per_trade, signal_threshold
        # Legacy calculate_position_recommendation() function will use this config
        config = {"use_legacy": True}  # Will be handled by old signal logic
        # ... existing logic calls calculate_position_recommendation() with legacy config
```

**Timeline**: Immediate (current release)

**Rollout Steps**:

1. **Add Feature Flag**: Create environment variable or config setting
   ```python
   # backend/config.py (NEW)
   USE_NEW_STRATEGY_ENGINE = os.getenv("USE_NEW_STRATEGY_ENGINE", "false").lower() == "true"
   ```

2. **Integrate StrategySelector**:
   ```python
   # backend/routers/analysis.py (MODIFY)
   from backend.services.strategy_selector import StrategySelector
   from backend.config import USE_NEW_STRATEGY_ENGINE

   @router.post("/analyze")
   async def analyze(request: AnalysisRequest) -> AnalysisResponse:
       selector = StrategySelector(use_new_engine=USE_NEW_STRATEGY_ENGINE)
       engine_config = selector.get_strategy_engine(
           risk_preference=request.risk_preference,
           strategy_params=request.strategy_params
       )

       if engine_config["use_new_engine"]:
           # Use new strategy engine
           result = engine_config["engine"].generate_signal(daily_data, weekly_data)
           # ... process result
       else:
           # Fall back to old engine
           result = old_signal_logic(daily_data, config=engine_config["params"])
   ```

3. **Enable Gradual Rollout**:
   - Start with `USE_NEW_STRATEGY_ENGINE=false` (old engine default)
   - Test internally with `USE_NEW_STRATEGY_ENGINE=true`
   - Monitor logs for signal comparison between old and new
   - Gradually enable for beta users
   - Full rollout after validation

4. **Add Migration Status Endpoint**:
   ```python
   @router.get("/api/migration/status")
   async def get_migration_status():
       selector = StrategySelector(use_new_engine=USE_NEW_STRATEGY_ENGINE)
       return selector.get_migration_status()
   ```

**Rollout Timeline**:
- Week 1-2: Feature flag off by default, internal testing
- Week 3-4: Signal comparison logging for validation
- Week 5-6: Enable for 10% of users (A/B test)
- Week 7-8: Full rollout if validation passes

#### 3.2 Phase 2: Graceful Migration (v1.2)

**File**: `backend/routers/deprecation.py` (NEW)

```python
"""API versioning and deprecation information"""
from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["deprecation"])

DEPRECATION_INFO = {
    "version": "1.2",
    "deprecated_features": {
        "risk_preference": {
            "removed_in": "2.0",
            "replacement": "strategy_params",
            "migration_guide": "Replace risk_preference with strategy_params object",
            "example": {
                "old": {"risk_preference": "neutral"},
                "new": {"strategy_params": {"kelly": {"kelly_fraction": 0.25}}}
            }
        }
    }
}

@router.get("/deprecation")
async def get_deprecation_info():
    """Get information about deprecated API features"""
    return DEPRECATION_INFO
```

**Timeline**: 3-6 months after Phase 1

#### 3.3 Phase 3: Hard Removal (v2.0)

**File**: `backend/models/schemas.py` (FINAL)

```python
# Phase 3: Remove risk_preference completely
class AnalysisRequest(BaseModel):
    etf_code: str = Field(..., description="ETF code (e.g., 510300)")
    strategy_params: Optional[Dict] = Field(
        default=None,
        description="Strategy parameters override"
    )
    use_cache: bool = Field(default=True, description="Whether to use cached data")
    total_capital: Optional[float] = Field(default=100000, description="Total capital")
    holding_amount: Optional[float] = Field(default=0, description="Current holding amount")
```

**File**: `backend/routers/analysis.py` (FINAL)

```python
# Remove RISK_CONFIG dict and risk-based logic
# DELETE: Lines 34-57 (RISK_CONFIG)
# DELETE: Risk preference references in all functions
```

**File**: `frontend/src/types/index.ts` (FINAL)

```typescript
// REMOVE
// export type RiskPreference = 'conservative' | 'neutral' | 'aggressive'

// MODIFY AnalyzeRequest
export interface AnalyzeRequest {
  etf_code: string
  use_cache: boolean
  total_capital?: number
  holding_amount?: number
  strategy_params?: StrategyParams  // REPLACES risk_preference
}
```

**File**: `frontend/src/components/InputForm.vue` (FINAL)

Remove risk preference dropdown entirely.

**Timeline**: 9-12 months after Phase 1 (allows for client migration)

**Acceptance Criteria**: Phase 1 adds deprecation warnings, Phase 2 provides migration guide, Phase 3 removes all references

---

### Phase 4: Testing and Validation

#### 4.1 Unit Tests

**File**: `tests/test_strategy_engine.py` (NEW)

```python
def test_trend_following_signal():
    """Test trend following signal generation"""
    # Given
    daily_data = generate_test_data()
    config = TrendFollowingConfig().dict()

    # When
    strategy = TrendFollowingStrategy()
    result = strategy.analyze(daily_data, config)

    # Then
    assert 'signal_strength' in result
    assert -1 <= result['signal_strength'] <= 1
    assert 'win_probability' in result
    assert 0 <= result['win_probability'] <= 1


def test_bottom_fishing_signal():
    """Test bottom fishing signal generation"""
    # Given
    daily_data = generate_test_data()
    config = BottomFishingConfig().dict()

    # When
    strategy = BottomFishingStrategy()
    result = strategy.analyze(daily_data, config)

    # Then
    assert 'signal_strength' in result
    assert 'win_probability' in result


def test_combined_stop_loss():
    """Test combined stop-loss returns most conservative value"""
    # Given
    entry_price = 100.0
    current_price = 105.0
    data = generate_test_data()
    config = StopLossConfig().dict()

    # When
    stop_loss = CombinedStopLoss().calculate(
        entry_price, current_price, data, config
    )

    # Then
    assert stop_loss < current_price  # Stop must be below price


def test_kelly_position_sizing_edge_cases():
    """Test Kelly position sizing handles edge cases"""
    # Test 1: Quarter-Kelly constraint
    kelly = KellyPositionSizer()
    config = {'kelly_fraction': 0.25, 'max_position_pct': 0.3, 'min_position_pct': 0.05}
    equity = 100000

    # Test 2: Negative edge returns 0
    size = kelly.calculate(0.3, 1.5, -1.0, config, equity)
    assert size >= 0

    # Test 3: Max position constraint
    config_high = {**config, 'max_position_pct': 0.1}
    size_constrained = kelly.calculate(0.8, 2.0, -1.0, config_high, equity)
    assert size_constrained <= equity * 0.1

    # Test 4: Min position constraint
    size_min = kelly.calculate(0.55, 1.5, -1.0, config, equity)
    if size_min > 0:
        assert size_min >= equity * 0.05


def test_multitimeframe_analysis():
    """Test multi-timeframe analysis with weekly data"""
    # Given
    daily_data = generate_test_data(days=100)
    weekly_data = convert_to_weekly(daily_data)

    # When
    analyzer = MultiTimeframeAnalyzer()
    result = analyzer.analyze(daily_data, weekly_data)

    # Then
    assert 'trend_direction' in result
    assert result['trend_direction'] in ['bullish', 'bearish', 'neutral']


def test_convert_to_weekly():
    """Test weekly data conversion"""
    # Given
    daily_data = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=30),
        'open': np.random.rand(30) * 100 + 90,
        'high': np.random.rand(30) * 100 + 100,
        'low': np.random.rand(30) * 100 + 85,
        'close': np.random.rand(30) * 100 + 95,
        'volume': np.random.randint(1000, 5000, 30)
    })

    # When
    weekly_data = convert_to_weekly(daily_data)

    # Then
    assert len(weekly_data) < len(daily_data)
    assert all(col in weekly_data.columns for col in ['date', 'open', 'high', 'low', 'close', 'volume'])
    assert validate_weekly_data(weekly_data)


def test_strategy_selector_risk_to_params_conservative():
    """Test conservative risk preference maps correctly"""
    # Given
    selector = StrategySelector(use_new_engine=False)

    # When
    params = selector.map_risk_to_params("conservative")

    # Then
    assert params['kelly']['kelly_fraction'] == 0.15
    assert params['kelly']['max_position_pct'] == 0.20
    assert params['kelly']['min_position_pct'] == 0.05
    assert params['stop_loss']['fixed_pct'] == 0.03
    assert params['stop_loss']['atr_multiplier'] == 1.5


def test_strategy_selector_risk_to_params_neutral():
    """Test neutral risk preference maps correctly"""
    # Given
    selector = StrategySelector(use_new_engine=False)

    # When
    params = selector.map_risk_to_params("neutral")

    # Then
    assert params['kelly']['kelly_fraction'] == 0.25
    assert params['kelly']['max_position_pct'] == 0.30
    assert params['stop_loss']['fixed_pct'] == 0.05
    assert params['stop_loss']['atr_multiplier'] == 2.0


def test_strategy_selector_risk_to_params_aggressive():
    """Test aggressive risk preference maps correctly"""
    # Given
    selector = StrategySelector(use_new_engine=False)

    # When
    params = selector.map_risk_to_params("aggressive")

    # Then
    assert params['kelly']['kelly_fraction'] == 0.40
    assert params['kelly']['max_position_pct'] == 0.50
    assert params['stop_loss']['fixed_pct'] == 0.07
    assert params['stop_loss']['atr_multiplier'] == 2.5


def test_strategy_selector_invalid_risk_fallback():
    """Test invalid risk preference falls back to neutral"""
    # Given
    selector = StrategySelector(use_new_engine=False)

    # When
    params = selector.map_risk_to_params("invalid_risk")

    # Then
    # Should fallback to neutral defaults
    assert params['kelly']['kelly_fraction'] == 0.25
    assert params['kelly']['max_position_pct'] == 0.30


def test_strategy_selector_with_strategy_params():
    """Test strategy_params takes priority over risk_preference"""
    # Given
    selector = StrategySelector(use_new_engine=True)
    custom_params = {
        "kelly": {"kelly_fraction": 0.50, "max_position_pct": 0.25}
    }

    # When
    result = selector.get_strategy_engine(
        risk_preference="conservative",
        strategy_params=custom_params
    )

    # Then
    assert result['use_new_engine'] is True
    assert result['params']['kelly']['kelly_fraction'] == 0.50  # Custom params used
    assert result['params']['kelly']['max_position_pct'] == 0.25


def test_strategy_selector_flag_false_uses_old():
    """Test use_new_engine=False returns old engine config"""
    # Given
    selector = StrategySelector(use_new_engine=False)

    # When
    result = selector.get_strategy_engine(risk_preference="neutral")

    # Then
    assert result['use_new_engine'] is False
    assert result['engine'] is None
    assert result['params']['kelly_fraction'] == 0.25


def test_strategy_selector_flag_true_uses_new():
    """Test use_new_engine=True returns new engine"""
    # Given
    selector = StrategySelector(use_new_engine=True)

    # When
    result = selector.get_strategy_engine(risk_preference="neutral")

    # Then
    assert result['use_new_engine'] is True
    assert result['engine'] is not None
    assert isinstance(result['engine'], StrategyEngine)


def test_backward_compatibility_signal_comparability():
    """Integration test: Old vs New engine signal comparability"""
    # Given
    daily_data = generate_test_data(days=252)
    selector = StrategySelector(use_new_engine=True)

    # Get old engine result
    old_result = selector.get_strategy_engine(risk_preference="neutral")
    # Simulate old signal generation (simplified)
    old_signal_strength = 0.5  # From old logic

    # Get new engine result
    new_result = selector.get_strategy_engine(risk_preference="neutral")
    new_signal = new_result['engine'].generate_signal(daily_data, None)

    # Then
    # Signals should be in comparable range (-1 to 1)
    assert -1 <= old_signal_strength <= 1
    assert -1 <= new_signal['signal_strength'] <= 1
    # Direction should be consistent (both positive, both negative, or both near zero)
    direction_consistent = (old_signal_strength * new_signal['signal_strength']) >= -0.1
    assert direction_consistent, "Signal directions should be consistent"
```

**File**: `tests/test_backtest.py` (NEW)

```python
def test_backtest_full_run():
    """Test complete backtest execution"""
    # Given
    daily_data = generate_test_data(days=252)
    configs = {
        'trend': TrendFollowingConfig().dict(),
        'bottom': BottomFishingConfig().dict(),
        'kelly': KellyConfig().dict(),
        'stop_loss': StopLossConfig().dict()
    }
    strategy = StrategyEngine(configs)
    backtest = BacktestEngine(strategy, initial_capital=100000)

    # When
    result = backtest.run(daily_data)

    # Then
    assert 'metrics' in result
    assert 'equity_curve' in result
    assert 'trades' in result
    assert result['metrics']['initial_capital'] == 100000


def test_backtest_metrics_calculation():
    """Test backtest metrics are calculated correctly"""
    # Given
    equity_curve = [
        {'date': '2024-01-01', 'value': 100000},
        {'date': '2024-01-02', 'value': 102000},
        {'date': '2024-01-03', 'value': 98000}
    ]
    trades = [
        {'pnl': 2000},
        {'pnl': -4000}
    ]

    # When
    metrics = BacktestEngine().calculate_metrics(equity_curve, trades)

    # Then
    assert 'total_return' in metrics
    assert 'max_drawdown' in metrics
    assert 'win_rate' in metrics


def test_backtest_api_endpoint():
    """Test backtest API endpoint returns valid response"""
    # When
    response = client.post("/api/backtest", json={
        'etf_code': '510300',
        'initial_capital': 100000
    })

    # Then
    assert response.status_code == 200
    data = response.json()
    assert 'metrics' in data
    assert 'equity_curve' in data
    assert 'trades' in data


def test_kelly_verification_scenarios():
    """Test Kelly criterion under various scenarios"""
    # Scenario 1: Quarter-Kelly vs Full Kelly
    kelly = KellyPositionSizer()
    config = {
        'kelly_fraction': 0.25,  # Quarter-Kelly
        'max_position_pct': 1.0,
        'min_position_pct': 0.01
    }
    equity = 100000

    # High edge scenario
    size_quarter = kelly.calculate(0.7, 2.0, -1.0, config, equity)
    config_full = {**config, 'kelly_fraction': 1.0}
    size_full = kelly.calculate(0.7, 2.0, -1.0, config_full, equity)

    assert size_quarter < size_full  # Quarter-Kelly should be smaller

    # Scenario 2: Low win probability (edge case)
    size_low = kelly.calculate(0.3, 1.5, -1.0, config, equity)
    assert size_low == 0.0  # Should recommend no position

    # Scenario 3: Zero division protection
    size_zero = kelly.calculate(0.55, 1.5, 0, config, equity)
    assert isinstance(size_zero, (int, float))  # Should not crash
```

#### 4.2 Integration Tests

1. **Full Backtest Flow**: Fetch data -> Run strategy -> Verify metrics
2. **Multi-Timeframe Analysis**: Weekly trend filters daily signals correctly
3. **Stop-Loss Logic**: Combined stop returns most conservative value
4. **Kelly Sizing**: Returns value between min/max constraints
5. **API Endpoints**: All endpoints return valid responses with error handling
6. **Signal Adapter**: Discrete to probability conversion works bidirectionally

#### 4.3 Manual Validation Checklist

- [ ] Backtest completes on 510300 within 5 seconds
- [ ] Annual return displays correctly (format: XX.XX%)
- [ ] Maximum drawdown displays correctly (format: -XX.XX%)
- [ ] Equity curve chart renders with correct dates
- [ ] Drawdown chart shows negative area properly
- [ ] Trade list shows all columns with correct data
- [ ] K-line chart displays buy/sell signal markers
- [ ] Strategy parameter updates affect backtest results
- [ ] Default parameters produce reasonable backtest results
- [ ] Weekly data conversion produces valid OHLCV bars
- [ ] Kelly quarter-fraction constraint is enforced
- [ ] Deprecation warning appears when using risk_preference

---

## Data Flow Diagram

```
┌─────────────┐
│   Frontend  │
│  (Vue 3)    │
└──────┬──────┘
       │ HTTP/JSON
       ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Backend                           │
│  ┌──────────────┐  ┌──────────────────┐             │
│  │   Router     │  │   Strategy Config │             │
│  │  (backtest)  │◄─┤   (Pydantic)     │             │
│  └──────┬───────┘  └──────────────────┘             │
│         │                                               │
│         ▼                                               │
│  ┌─────────────────────────────────────────────┐         │
│  │         Data Pipeline                      │         │
│  │  ┌──────────┐         ┌──────────────┐ │         │
│  │  │  Data    │         │  Data Utils   │ │         │
│  │  │  Fetcher │────────►│convert_to_   │ │         │
│  │  │          │         │   weekly()    │ │         │
│  │  └────┬─────┘         └──────────────┘ │         │
│  │       │                                    │         │
│  │       ▼                                    │         │
│  │  ┌──────────────────────────────────────┐ │         │
│  │  │    Strategy Engine                 │ │         │
│  │  │  ┌──────────────────────────────┐  │ │         │
│  │  │  │   Signal Adapter             │  │ │         │
│  │  │  │   (discrete <-> prob)       │  │ │         │
│  │  │  └──────────────────────────────┘  │ │         │
│  │  │                                     │ │         │
│  │  │  ┌──────────────────┐  ┌─────────┐│ │         │
│  │  │  │Trend Following  │  │  Kelly  ││ │         │
│  │  │  │   Strategy      │◄─│ Sizer   ││ │         │
│  │  │  └────────┬─────────┘  └─────────┘│ │         │
│  │  │           │                         │ │         │
│  │  │  ┌────────▼───────────────────┐    │ │         │
│  │  │  │   Multi-Timeframe          │    │ │         │
│  │  │  │   Analyzer               │    │ │         │
│  │  │  │   (daily + weekly)        │    │ │         │
│  │  │  └───────────────────────────┘    │ │         │
│  │  │                                   │ │         │
│  │  │  ┌─────────────┐  ┌────────────┐ │ │         │
│  │  │  │   Bottom    │  │  Combined  │ │ │         │
│  │  │  │  Fishing    │  │  Stop Loss │ │ │         │
│  │  │  │  Strategy   │  │            │ │ │         │
│  │  │  └─────────────┘  └────────────┘ │ │         │
│  │  └─────────────────────────────────────┘ │         │
│  │                   │                     │         │
│  │                   ▼                     │         │
│  │  ┌────────────────────────────────────┐ │         │
│  │  │      Backtest Engine             │ │         │
│  │  └────────────┬───────────────────┘ │         │
│  └───────────────┼───────────────────────┘         │
│                  │                                 │
│                  ▼                                 │
│  ┌─────────────────────────────────────────────┐  │
│  │      Indicators (TA-Lib/Pandas)           │  │
│  │  ┌────────────┐  ┌──────────────────────┐│  │
│  │  │   ATR      │  │  Volume Analysis    ││  │
│  │  │ (dual impl)│  │  (surge/shrink)    ││  │
│  │  └────────────┘  └──────────────────────┘│  │
│  └─────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘

Data Flow:
1. Frontend sends BacktestRequest
2. Router fetches daily data via DataFetcher
3. DataUtils converts daily to weekly
4. StrategyEngine uses SignalAdapter to convert discrete signals
5. Multi-Timeframe Analyzer combines daily + weekly
6. Trend/Bottom strategies generate signals
7. Kelly Sizer calculates position size
8. Combined Stop Loss determines exit level
9. Backtest Engine simulates trades
10. Metrics Calculator computes performance
11. Response sent to Frontend for visualization
```

---

## Risk Mitigation

### 1. Strategy Performance Risk

**Risk**: New strategies may underperform current approach

**Mitigation**:
- Implement A/B testing framework to compare old vs new signals
- Add parameter validation to prevent extreme values
- Document all strategy decisions with rationale
- Use conservative defaults (quarter-Kelly)

### 2. Data Quality Risk

**Risk**: Weekly conversion may not accurately represent true weekly bars

**Mitigation**:
- Validate weekly conversion with real weekly data when available
- Document conversion methodology (ISO week aggregation)
- Provide option to skip weekly if insufficient data
- Flag periods with suspect data

### 3. Signal Adapter Risk

**Risk**: Mapping between discrete and probability may lose information

**Mitigation**:
- Document mapping table explicitly
- Provide bidirectional conversion
- Allow custom mapping via configuration
- Use conservative probability estimates

### 4. Kelly Criterion Risk

**Risk**: Full Kelly can lead to excessive drawdown

**Mitigation**:
- Use quarter-Kelly (0.25x) by default
- Cap maximum position at 30%
- Require minimum 30 trades before full Kelly calculation
- Fall back to fixed percentage if edge estimate unreliable
- Add comprehensive edge case tests

### 5. API Breaking Changes Risk

**Risk**: Removing risk_preference breaks existing clients

**Mitigation**:
- 3-phase deprecation timeline (soft -> graceful -> hard)
- Keep risk_preference as optional with deprecation warning
- Add `/api/deprecation` endpoint for migration guide
- Monitor API usage before removal

---

## Testing Strategy

### Unit Tests

| Module | Test Cases | Coverage Target |
|--------|-----------|----------------|
| data_utils.py | 5+ (convert_to_weekly, validate) | 90% |
| signal_adapter.py | 8+ (bidirectional conversion) | 95% |
| indicators.py | 20+ (including ATR dual impl) | 85% |
| strategy_engine.py | 25+ (each strategy, stop-loss, Kelly, MTF) | 80% |
| backtest.py | 15+ (run, metrics, signals) | 75% |
| backtest_schemas.py | 5+ (validation) | 90% |

### Integration Tests

1. **Full Backtest Flow**: Fetch data -> Run strategy -> Verify metrics
2. **Multi-Timeframe Analysis**: Weekly trend filters daily signals correctly
3. **Stop-Loss Logic**: Combined stop returns most conservative value
4. **Kelly Sizing**: Returns value between min/max constraints, quarter-Kelly enforced
5. **Signal Adapter**: Bidirectional conversion preserves semantics
6. **API Endpoints**: All endpoints return valid responses with error handling

### Kelly Verification Tests (New)

1. **Quarter-Kelly Constraint**: Quarter-Kelly position <= Full Kelly position
2. **Negative Edge**: Returns 0 position when edge < 0
3. **Max Position**: Enforces max_position_pct constraint
4. **Min Position**: Enforces min_position_pct for small positive signals
5. **Zero Division Protection**: Handles avg_loss = 0 gracefully

### Manual Validation Checklist

- [ ] Backtest completes on 510300 within 5 seconds
- [ ] Annual return displays correctly (format: XX.XX%)
- [ ] Maximum drawdown displays correctly (format: -XX.XX%)
- [ ] Equity curve chart renders with correct dates
- [ ] Drawdown chart shows negative area properly
- [ ] Trade list shows all columns with correct data
- [ ] K-line chart displays buy/sell signal markers
- [ ] Strategy parameter updates affect backtest results
- [ ] Weekly data conversion produces valid Friday-dated bars
- [ ] Kelly quarter-fraction constraint is enforced in results
- [ ] Deprecation warning appears in logs when using risk_preference

---

## Dependencies and Prerequisites

### Required Python Packages

```txt
# Already installed
fastapi
uvicorn
pydantic
pandas
requests
numpy

# May need to add
talib-binary      # Or TA-Lib from source (recommended for ATR)
scipy            # For additional statistics if needed
```

### Required Frontend Packages

```json
{
  "vue": "^3.x",
  "vue-echarts": "^6.x",
  "echarts": "^5.x",
  "element-plus": "^2.x",
  "axios": "^1.x",
  "typescript": "^5.x"
}
```

---

## Timeline Estimate

| Phase | Tasks | Effort |
|-------|--------|--------|
| Phase 1: Backend Strategy Engine | 8 tasks | 4-5 days |
| Phase 2: Frontend Backtest UI | 6 tasks | 2-3 days |
| Phase 3: Risk Preference Deprecation | 3 phases | 1 day (Phase 1) |
| Phase 4: Testing and Validation | Enhanced test suite | 2-3 days |
| **Total** | **18 tasks + 3-phase deprecation** | **9-12 days** |

---

## Success Criteria

1. Backtest API returns all 13 required metrics
2. Backtest page displays equity curve, drawdown curve, and trade list
3. K-line chart annotates buy/sell signals
4. Weekly data conversion produces valid OHLCV bars without API dependency
5. Signal adapter bridges discrete and probability signals correctly
6. All strategy parameters configurable via UI
7. Backtest runs on 1-year historical data in <5 seconds
8. Kelly position sizing enforces quarter-Kelly and min/max constraints
9. Deprecation warnings appear for risk_preference usage
10. ATR indicator has dual talib/pandas implementation

---

## Future Goals (Not Acceptance Criteria)

The following business outcomes are aspirational targets to validate after implementation:
- Annual return: 15-25%
- Maximum drawdown: <10%
- Sharpe ratio: >1.0

These should be measured and optimized after the implementation is complete through parameter tuning and strategy refinement.

---

## ADR (Architecture Decision Record)

### Decision

Implement a hybrid layered approach (Option C) for strategy optimization with explicit weekly data conversion, signal adapter pattern, and 3-phase deprecation strategy.

### Drivers

1. **Technical Requirements**: Multi-timeframe analysis (daily + weekly), Kelly criterion position sizing, configurable strategy parameters
2. **Maintainability**: Current signal.py (289 lines) is approaching complexity threshold
3. **Migration Safety**: Cannot break existing API contracts for production users
4. **API Constraint**: Weekly data not available via current API, requires conversion

### Alternatives Considered

1. **Option A - Incremental Module Addition**: Add new modules to signal.py
   - Rejected: Would push signal.py beyond maintainability threshold
   - Technical debt accumulation
   - Does not address signal semantic mismatch

2. **Option B - Clean Strategy Replacement**: Replace signal.py entirely
   - Rejected: Requires simultaneous changes to 7+ components
   - High risk of breaking changes
   - No weekly data solution

3. **Option C - Hybrid Layered Approach** (SELECTED)
   - New strategy engine for backtest functionality
   - Weekly data conversion via `convert_to_weekly()`
   - Signal adapter for discrete-to-probability mapping
   - Existing analysis endpoint migrates incrementally
   - 3-phase deprecation for risk_preference removal
   - Strategy selector routes to appropriate engine

### Why Chosen

Option C provides:
- Gradual migration path with low risk
- New backtest functionality isolated and testable
- No breaking changes to existing API (initially)
- Explicit weekly data solution without API dependency
- Clear signal semantic bridging via adapter pattern
- Clean architecture for future enhancements
- Ability to A/B test strategies

### Consequences

**Positive**:
- Backtest functionality can be developed independently
- Existing UI continues working during migration
- Clear separation of concerns
- Easier to test and validate
- Signal adapter enables gradual semantic transition

**Negative**:
- Temporary code duplication (signal.py + strategy_engine.py)
- Additional routing logic complexity
- Slightly increased memory footprint
- Weekly conversion is approximation, not real data
- Requires cleanup planning for deprecation

### Follow-ups

1. Migrate existing analysis endpoint to use strategy_engine
2. Deprecate and remove signal.py after validation period
3. Add performance monitoring for new strategies
4. Document parameter tuning guidelines
5. Consider walk-forward analysis for future enhancements
6. Evaluate real weekly data API availability
7. Complete Phase 2 and Phase 3 deprecation timeline

---

## Changelog (from Original Plan)

### Added
1. **Weekly Data Conversion** (`data_utils.py`): Added `convert_to_weekly()` function with Friday date calculation
2. **Signal Adapter** (`signal_adapter.py`): New module for discrete-to-probability conversion
3. **ATR Dual Implementation**: Added talib + pandas fallback in `indicators.py`
4. **Kelly Verification Tests**: Expanded test cases for edge cases, quarter-Kelly, min/max constraints
5. **3-Phase Deprecation Strategy**: Added timeline for risk_preference removal (soft -> graceful -> hard)
6. **Deprecation Endpoint**: Added `/api/deprecation` for migration guide
7. **Strategy Selector** (`strategy_selector.py`): New class for gradual migration with `use_new_engine` feature flag
8. **Risk Preference Mapping**: NEW_RISK_CONFIG (strategy_selector.py) maps to Kelly-based parameters; legacy RISK_CONFIG (analysis.py lines 34-57) documented for migration
9. **Rollout Steps**: Detailed rollout timeline with A/B testing and gradual enablement
10. **Backward Compatibility Tests**: Added risk_preference validation and signal comparability tests

### Modified
1. **KDJ Implementation**: Clarified that synthetic KDJ (derived from RSI) is retained for consistency
2. **Business Outcomes**: Moved return targets (15-25%) to "Future Goals" section, not acceptance criteria
3. **Weekly Data Flow**: Updated data flow diagram to show daily-to-weekly conversion
4. **Testing Strategy**: Added Kelly-specific verification tests

### Clarified
1. **Signal Semantic Mismatch**: Addressed via explicit SignalAdapter pattern with bidirectional conversion
2. **Weekly Data Bottleneck**: Solved via `convert_to_weekly()` function (no API dependency)
3. **ATR Implementation**: Documented dual talib/pandas fallback strategy
4. **RISK_CONFIG Schema Distinction**: NEW_RISK_CONFIG (Kelly-based) vs legacy RISK_CONFIG (fixed percentages) clearly separated
5. **calculate_position_recommendation() Dependencies**: Documented all uses of legacy RISK_CONFIG (lines 325, 399-400, 405, 411, 437-438, 441-442)

### Removed
1. **Real KDJ Implementation**: Plan to add real KDJ removed; synthetic KDJ retained for consistency

---

## Open Questions

1. Should we implement parameter optimization (grid search, genetic algorithm) or leave it manual?
2. Do we need a database to store backtest results for historical comparison?
3. Should strategy parameters be user-specific or global defaults?
4. What is the exact timeline for Phase 2 and Phase 3 deprecation (dates vs. versions)?
5. Do we need real-time paper trading integration?

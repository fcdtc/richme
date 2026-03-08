"""
Unit tests for strategy engine components.
Tests: data_utils, signal_adapter, strategy_engine, indicators
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.data_utils import convert_to_weekly, validate_weekly_data
from services.signal_adapter import SignalAdapter
from services.indicators import (
    calculate_atr, calculate_volume_surge, calculate_volume_shrink,
    calculate_support_resistance, detect_breakout, calculate_all_indicators
)
from services.strategy_engine import (
    TrendFollowingStrategy, BottomFishingStrategy, CombinedStopLoss,
    KellyPositionSizer, MultiTimeframeAnalyzer, StrategyEngine
)


def generate_test_data(days: int = 120) -> pd.DataFrame:
    """Generate synthetic OHLCV test data."""
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')

    # Generate price data with some trend
    base_price = 3.0
    returns = np.random.normal(0.001, 0.02, days)
    prices = base_price * (1 + returns).cumprod()

    # Generate OHLCV
    data = pd.DataFrame({
        'date': dates,
        'open': prices * (1 + np.random.uniform(-0.01, 0.01, days)),
        'high': prices * (1 + np.random.uniform(0.01, 0.03, days)),
        'low': prices * (1 + np.random.uniform(-0.03, -0.01, days)),
        'close': prices,
        'volume': np.random.uniform(1000000, 5000000, days)
    })

    return data


class TestDataUtils:
    """Tests for data_utils module."""

    def test_convert_to_weekly_basic(self):
        """Test basic weekly conversion."""
        daily_data = generate_test_data(120)
        weekly_data = convert_to_weekly(daily_data)

        # Check structure
        assert 'date' in weekly_data.columns
        assert 'open' in weekly_data.columns
        assert 'high' in weekly_data.columns
        assert 'low' in weekly_data.columns
        assert 'close' in weekly_data.columns
        assert 'volume' in weekly_data.columns

        # Weekly should have fewer rows than daily
        assert len(weekly_data) < len(daily_data)

    def test_convert_to_weekly_empty(self):
        """Test empty input handling."""
        empty_df = pd.DataFrame()
        result = convert_to_weekly(empty_df)
        assert result.empty

    def test_validate_weekly_data(self):
        """Test weekly data validation."""
        # Sufficient data
        weekly_data = generate_test_data(200)
        weekly_data = convert_to_weekly(weekly_data)
        assert validate_weekly_data(weekly_data, min_weeks=26) == True

        # Insufficient data
        small_data = generate_test_data(30)
        small_weekly = convert_to_weekly(small_data)
        assert validate_weekly_data(small_weekly, min_weeks=26) == False


class TestSignalAdapter:
    """Tests for signal_adapter module."""

    def test_discrete_to_probability_strong_buy(self):
        """Test strong_buy signal conversion."""
        prob, edge = SignalAdapter.discrete_to_probability("strong_buy")
        assert prob == 0.80
        assert edge == 0.35

    def test_discrete_to_probability_buy(self):
        """Test buy signal conversion."""
        prob, edge = SignalAdapter.discrete_to_probability("buy")
        assert prob == 0.65
        assert edge == 0.20

    def test_discrete_to_probability_hold(self):
        """Test hold signal conversion."""
        prob, edge = SignalAdapter.discrete_to_probability("hold")
        assert prob == 0.50
        assert edge == 0.00

    def test_discrete_to_probability_sell(self):
        """Test sell signal conversion."""
        prob, edge = SignalAdapter.discrete_to_probability("sell")
        assert prob == 0.35
        assert edge == -0.20

    def test_discrete_to_probability_strong_sell(self):
        """Test strong_sell signal conversion."""
        prob, edge = SignalAdapter.discrete_to_probability("strong_sell")
        assert prob == 0.20
        assert edge == -0.35

    def test_discrete_to_strength(self):
        """Test strength conversion."""
        assert SignalAdapter.discrete_to_strength("strong_buy") == 1.0
        assert SignalAdapter.discrete_to_strength("buy") == 0.5
        assert SignalAdapter.discrete_to_strength("hold") == 0.0
        assert SignalAdapter.discrete_to_strength("sell") == -0.5
        assert SignalAdapter.discrete_to_strength("strong_sell") == -1.0

    def test_probability_to_discrete(self):
        """Test probability to discrete conversion."""
        assert SignalAdapter.probability_to_discrete(0.80) == "strong_buy"
        assert SignalAdapter.probability_to_discrete(0.75) == "strong_buy"
        assert SignalAdapter.probability_to_discrete(0.65) == "buy"
        assert SignalAdapter.probability_to_discrete(0.60) == "buy"
        assert SignalAdapter.probability_to_discrete(0.50) == "hold"
        assert SignalAdapter.probability_to_discrete(0.35) == "sell"
        assert SignalAdapter.probability_to_discrete(0.20) == "strong_sell"

    def test_bidirectional_conversion(self):
        """Test bidirectional conversion consistency."""
        signals = ["strong_buy", "buy", "hold", "sell", "strong_sell"]
        for signal in signals:
            prob, _ = SignalAdapter.discrete_to_probability(signal)
            # Note: due to threshold mapping, exact round-trip may vary
            converted = SignalAdapter.probability_to_discrete(prob)
            # Verify it's consistent within the same category
            if signal == "strong_buy":
                assert converted == "strong_buy"
            elif signal == "strong_sell":
                assert converted == "strong_sell"


class TestIndicators:
    """Tests for extended indicator functions."""

    def test_calculate_atr(self):
        """Test ATR calculation."""
        data = generate_test_data(100)
        atr = calculate_atr(data['high'], data['low'], data['close'], period=14)

        assert isinstance(atr, pd.Series)
        assert len(atr) == len(data)
        # ATR should be positive
        assert atr.iloc[-1] > 0

    def test_calculate_volume_surge(self):
        """Test volume surge detection."""
        # Create data with surge
        data = generate_test_data(100)
        data.loc[data.index[-1], 'volume'] = data['volume'].mean() * 2  # Double volume

        result = calculate_volume_surge(data['volume'], period=20, threshold=1.5)

        assert 'current_ratio' in result
        assert 'is_surge' in result
        assert 'average_volume' in result
        assert result['is_surge'] == True
        assert result['current_ratio'] >= 1.5

    def test_calculate_volume_shrink(self):
        """Test volume shrinkage detection."""
        data = generate_test_data(100)
        data.loc[data.index[-1], 'volume'] = data['volume'].mean() * 0.5  # Half volume

        result = calculate_volume_shrink(data['volume'], period=20, threshold=0.7)

        assert 'current_ratio' in result
        assert 'is_shrink' in result
        assert result['is_shrink'] == True
        assert result['current_ratio'] <= 0.7

    def test_calculate_support_resistance(self):
        """Test support/resistance calculation."""
        data = generate_test_data(100)
        result = calculate_support_resistance(data['high'], data['low'], lookback=20)

        assert 'support_level' in result
        assert 'resistance_level' in result
        assert result['support_level'] < result['resistance_level']

    def test_detect_breakout(self):
        """Test breakout detection."""
        data = generate_test_data(100)
        resistance = data['close'].iloc[-1] * 0.95  # Set resistance below current price

        is_breakout = detect_breakout(data['close'], data['high'], resistance, threshold=0.02)

        # Current price should be above resistance
        assert is_breakout == True


class TestStrategyEngine:
    """Tests for strategy engine components."""

    def get_default_configs(self):
        """Get default strategy configurations."""
        return {
            'trend': {
                'ma_short_period': 5,
                'ma_long_period': 20,
                'rsi_oversold': 30,
                'rsi_overbought': 70,
                'volume_period': 20,
                'volume_surge_threshold': 1.5
            },
            'bottom': {
                'rsi_bottom_threshold': 20.0,
                'support_lookback': 20,
                'volume_period': 20,
                'volume_shrink_threshold': 0.7
            },
            'stop_loss': {
                'fixed_pct': 0.05,
                'atr_period': 14,
                'atr_multiplier': 2.0,
                'support_lookback': 20,
                'support_pct': 0.02,
                'trailing_activation_pct': 0.02
            },
            'kelly': {
                'kelly_fraction': 0.25,
                'avg_win_avg_loss_ratio': 1.5,
                'max_position_pct': 0.3,
                'min_position_pct': 0.05
            },
            'initial_capital': 100000
        }

    def test_trend_following_strategy(self):
        """Test trend following strategy analysis."""
        data = generate_test_data(120)
        strategy = TrendFollowingStrategy()
        configs = self.get_default_configs()

        result = strategy.analyze(data, configs['trend'])

        assert 'signal_strength' in result
        assert 'win_probability' in result
        assert 'signals' in result
        assert -1.0 <= result['signal_strength'] <= 1.0
        assert 0.0 <= result['win_probability'] <= 1.0

    def test_bottom_fishing_strategy(self):
        """Test bottom fishing strategy analysis."""
        data = generate_test_data(120)
        strategy = BottomFishingStrategy()
        configs = self.get_default_configs()

        result = strategy.analyze(data, configs['bottom'])

        assert 'signal_strength' in result
        assert 'win_probability' in result
        assert 'signals' in result
        assert -1.0 <= result['signal_strength'] <= 1.0
        assert 0.0 <= result['win_probability'] <= 1.0

    def test_kelly_position_sizer(self):
        """Test Kelly position sizing."""
        sizer = KellyPositionSizer()
        configs = self.get_default_configs()

        # High win probability should result in larger position
        position_high = sizer.calculate(
            win_probability=0.70,
            avg_win=1.5,
            avg_loss=1.0,
            config=configs['kelly'],
            current_equity=100000
        )

        # Low win probability should result in smaller or zero position
        position_low = sizer.calculate(
            win_probability=0.30,
            avg_win=1.5,
            avg_loss=1.0,
            config=configs['kelly'],
            current_equity=100000
        )

        assert position_high >= 0
        assert position_low >= 0
        assert position_high > position_low

        # Position should be within limits
        max_pos = 100000 * configs['kelly']['max_position_pct']
        assert position_high <= max_pos

    def test_combined_stop_loss(self):
        """Test combined stop loss calculation."""
        data = generate_test_data(120)
        stop_loss = CombinedStopLoss()
        configs = self.get_default_configs()

        current_price = data['close'].iloc[-1]
        stop_price = stop_loss.calculate(
            entry_price=current_price,
            current_price=current_price,
            data=data,
            config=configs['stop_loss']
        )

        # Stop loss should be below entry price for long
        assert stop_price < current_price
        assert stop_price > 0

    def test_multi_timeframe_analyzer(self):
        """Test multi-timeframe analysis."""
        daily_data = generate_test_data(180)
        weekly_data = convert_to_weekly(daily_data)
        analyzer = MultiTimeframeAnalyzer()

        result = analyzer.analyze(daily_data, weekly_data)

        assert 'trend_direction' in result
        assert 'weekly_score' in result
        assert 'daily_weight' in result
        assert result['trend_direction'] in ['bullish', 'bearish', 'neutral']
        assert 0.5 <= result['daily_weight'] <= 1.5

    def test_strategy_engine_generate_signal(self):
        """Test complete signal generation."""
        data = generate_test_data(180)
        engine = StrategyEngine(self.get_default_configs())

        signal = engine.generate_signal(data)

        assert 'signal_type' in signal
        assert 'signal_strength' in signal
        assert 'win_probability' in signal
        assert 'position_size' in signal
        assert 'stop_loss' in signal
        assert 'signals' in signal
        assert 'mtf_analysis' in signal

        assert signal['signal_type'] in ['buy', 'sell', 'hold']
        assert -1.0 <= signal['signal_strength'] <= 1.0
        assert 0.0 <= signal['win_probability'] <= 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

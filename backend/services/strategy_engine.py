"""
Strategy engine for ETF quantitative trading.
Supports multi-strategy, multi-timeframe analysis with Kelly position sizing.
"""
import pandas as pd
from typing import Dict

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

        # Calculate odds (win/loss ratio)
        odds = avg_win / abs(avg_loss)

        # Kelly formula: f* = (bp - q) / b
        # where b = odds, p = win_probability, q = 1 - p
        q = 1 - win_probability
        kelly_pct = (odds * win_probability - q) / odds if odds > 0 else 0

        # Apply safety fraction (quarter-Kelly default)
        safe_kelly = kelly_pct * config.get('kelly_fraction', 0.25)

        # Handle edge cases
        if safe_kelly < 0:
            # Use minimum position if we have a buy signal
            safe_kelly = config.get('min_position_pct', 0.05)

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

    def generate_signal(self, daily_data: pd.DataFrame, weekly_data: pd.DataFrame = None, current_equity: float = None) -> Dict:
        """
        Generate complete trading signal.

        Args:
            daily_data: Daily OHLCV data
            weekly_data: Weekly OHLCV data (optional)
            current_equity: Current account equity for position sizing (defaults to initial_capital)

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

        # Use provided equity or fall back to initial capital
        if current_equity is None:
            current_equity = self.configs.get('initial_capital', 100000)

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

        # Determine signal type (lowered threshold for more trades)
        if final_strength > 0.15:
            signal_type = 'buy'
        elif final_strength < -0.15:
            signal_type = 'sell'
        else:
            signal_type = 'hold'

        # Calculate position size if buy signal
        position_size = 0.0
        current_price = daily_data['close'].iloc[-1]

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

"""Technical indicators calculation module with talib fallback support."""

import pandas as pd
from typing import Dict, Optional, Union

try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False


def calculate_ma(series: pd.Series, periods: list) -> Dict[str, float]:
    """
    Calculate Moving Average (MA) indicators.

    Args:
        series: Price series (close prices)
        periods: List of MA periods (e.g., [5, 10, 30])

    Returns:
        Dictionary of MA values (e.g., {'ma5': 1.23, 'ma10': 1.45, 'ma30': 1.67})
    """
    result = {}
    for period in periods:
        if len(series) >= period:
            result[f'ma{period}'] = series.rolling(window=period).mean().iloc[-1]
        else:
            result[f'ma{period}'] = series.iloc[-1]
    return result


def _macd_pandas(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
    """
    Calculate MACD using pandas (fallback implementation).

    Args:
        series: Price series (close prices)
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line period

    Returns:
        Dictionary with DIF, DEA, and bar values
    """
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    return {
        'dif': macd.iloc[-1],
        'dea': signal_line.iloc[-1],
        'bar': histogram.iloc[-1]
    }


def _macd_talib(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
    """
    Calculate MACD using talib.

    Args:
        series: Price series (close prices)
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line period

    Returns:
        Dictionary with DIF, DEA, and bar values
    """
    macd, signal_line, histogram = talib.MACD(series.values, fastperiod=fast, slowperiod=slow, signalperiod=signal)
    return {
        'dif': float(macd[-1]) if not pd.isna(macd[-1]) else 0.0,
        'dea': float(signal_line[-1]) if not pd.isna(signal_line[-1]) else 0.0,
        'bar': float(histogram[-1]) if not pd.isna(histogram[-1]) else 0.0
    }


def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
    """
    Calculate MACD indicator (DIF, DEA, bar).

    Args:
        series: Price series (close prices)
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line period

    Returns:
        Dictionary with DIF, DEA, and bar values
    """
    if TALIB_AVAILABLE and len(series) >= slow + signal:
        return _macd_talib(series, fast, slow, signal)
    else:
        return _macd_pandas(series, fast, slow, signal)


def _rsi_pandas(series: pd.Series, period: int = 14) -> float:
    """
    Calculate RSI using pandas (fallback implementation).

    Args:
        series: Price series (close prices)
        period: RSI period

    Returns:
        RSI value (0-100)
    """
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    rsi_value = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0
    return float(rsi_value)


def _rsi_talib(series: pd.Series, period: int = 14) -> float:
    """
    Calculate RSI using talib.

    Args:
        series: Price series (close prices)
        period: RSI period

    Returns:
        RSI value (0-100)
    """
    rsi_values = talib.RSI(series.values, timeperiod=period)
    rsi_value = rsi_values[-1] if not pd.isna(rsi_values[-1]) else 50.0
    return float(rsi_value)


def calculate_rsi(series: pd.Series, period: int = 14) -> float:
    """
    Calculate RSI indicator.

    Args:
        series: Price series (close prices)
        period: RSI period

    Returns:
        RSI value (0-100)
    """
    if TALIB_AVAILABLE and len(series) >= period + 1:
        return _rsi_talib(series, period)
    else:
        return _rsi_pandas(series, period)


def _bollinger_pandas(series: pd.Series, period: int = 20, std_dev: float = 2) -> Dict[str, float]:
    """
    Calculate Bollinger Bands using pandas (fallback implementation).

    Args:
        series: Price series (close prices)
        period: Moving average period
        std_dev: Standard deviation multiplier

    Returns:
        Dictionary with upper, middle, and lower band values
    """
    middle = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    return {
        'upper': float(upper.iloc[-1]),
        'middle': float(middle.iloc[-1]),
        'lower': float(lower.iloc[-1])
    }


def _bollinger_talib(series: pd.Series, period: int = 20, std_dev: float = 2) -> Dict[str, float]:
    """
    Calculate Bollinger Bands using talib.

    Args:
        series: Price series (close prices)
        period: Moving average period
        std_dev: Standard deviation multiplier

    Returns:
        Dictionary with upper, middle, and lower band values
    """
    upper, middle, lower = talib.BBANDS(series.values, timeperiod=period, nbdevup=std_dev, nbdevdn=std_dev)
    return {
        'upper': float(upper[-1]) if not pd.isna(upper[-1]) else float(series.iloc[-1]),
        'middle': float(middle[-1]) if not pd.isna(middle[-1]) else float(series.iloc[-1]),
        'lower': float(lower[-1]) if not pd.isna(lower[-1]) else float(series.iloc[-1])
    }


def calculate_bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2) -> Dict[str, float]:
    """
    Calculate Bollinger Bands indicator.

    Args:
        series: Price series (close prices)
        period: Moving average period
        std_dev: Standard deviation multiplier

    Returns:
        Dictionary with upper, middle, and lower band values
    """
    if TALIB_AVAILABLE and len(series) >= period:
        return _bollinger_talib(series, period, std_dev)
    else:
        return _bollinger_pandas(series, period, std_dev)


def calculate_all_indicators(series: pd.Series) -> Dict[str, Union[float, Dict[str, float]]]:
    """
    Calculate all technical indicators for a price series.

    Args:
        series: Price series (close prices)

    Returns:
        Dictionary containing all calculated indicators
    """
    indicators = {}

    # MA indicators
    indicators['ma'] = calculate_ma(series, [5, 10, 20, 60])

    # MACD indicator
    indicators['macd'] = calculate_macd(series)

    # RSI indicator
    indicators['rsi'] = calculate_rsi(series)

    # Bollinger Bands
    indicators['bollinger'] = calculate_bollinger_bands(series)

    return indicators


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


def calculate_volume_surge(volume: pd.Series, period: int = 20, threshold: float = 1.5) -> Dict[str, Union[float, bool]]:
    """
    Detect volume surge (above threshold * average).

    Args:
        volume: Volume series
        period: Lookback period for average
        threshold: Multiplier for surge detection

    Returns:
        Dict with current_ratio, is_surge, average_volume, threshold
    """
    if volume.empty or len(volume) < period:
        return {
            'current_ratio': 1.0,
            'is_surge': False,
            'average_volume': 0.0,
            'threshold': threshold
        }

    avg_volume = volume.rolling(window=period).mean().iloc[-1]
    current_volume = volume.iloc[-1]
    ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
    return {
        'current_ratio': float(ratio),
        'is_surge': ratio >= threshold,
        'average_volume': float(avg_volume),
        'threshold': threshold
    }


def calculate_volume_shrink(volume: pd.Series, period: int = 20, threshold: float = 0.7) -> Dict[str, Union[float, bool]]:
    """
    Detect volume shrinkage (below threshold * average).

    Args:
        volume: Volume series
        period: Lookback period for average
        threshold: Multiplier for shrink detection

    Returns:
        Dict with current_ratio, is_shrink, average_volume, threshold
    """
    if volume.empty or len(volume) < period:
        return {
            'current_ratio': 1.0,
            'is_shrink': False,
            'average_volume': 0.0,
            'threshold': threshold
        }

    avg_volume = volume.rolling(window=period).mean().iloc[-1]
    current_volume = volume.iloc[-1]
    ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
    return {
        'current_ratio': float(ratio),
        'is_shrink': ratio <= threshold,
        'average_volume': float(avg_volume),
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
    if high.empty or low.empty or len(high) < lookback:
        return {
            'support_level': 0.0,
            'resistance_level': 0.0
        }

    recent_high = high.tail(lookback).max()
    recent_low = low.tail(lookback).min()

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
    if close.empty or pd.isna(resistance):
        return False

    current_close = close.iloc[-1]
    breakout_level = resistance * (1 + threshold)
    return current_close >= breakout_level


def get_indicator_library() -> str:
    """
    Get the currently available indicator calculation library.

    Returns:
        'talib' if talib is available, 'pandas' otherwise
    """
    return 'talib' if TALIB_AVAILABLE else 'pandas'

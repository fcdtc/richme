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


def get_indicator_library() -> str:
    """
    Get the currently available indicator calculation library.

    Returns:
        'talib' if talib is available, 'pandas' otherwise
    """
    return 'talib' if TALIB_AVAILABLE else 'pandas'

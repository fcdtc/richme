"""Signal generation module for ETF quantitative trading calculator."""

from typing import Dict, List, Literal
import pandas as pd

from backend.services.indicators import calculate_all_indicators

RiskPreference = Literal["conservative", "neutral", "aggressive"]
Signal = Literal["strong_buy", "buy", "hold", "sell", "strong_sell"]


def generate_signal(
    close_prices: list,
    risk_preference: RiskPreference = "neutral"
) -> dict:
    """
    Generate trading signal based on technical indicators.

    Args:
        close_prices: List of closing prices
        risk_preference: Risk preference level (conservative/neutral/aggressive)

    Returns:
        Dictionary containing:
            - signal: Trading signal (strong_buy/buy/hold/sell/strong_sell)
            - strength: Signal strength (-1 to 1)
            - indicators: All calculated technical indicators
            - analysis: List of analysis strings for each indicator
    """
    if len(close_prices) < 30:
        return {
            "signal": "hold",
            "strength": 0.0,
            "indicators": {},
            "analysis": ["Insufficient data for signal generation (need at least 30 data points)"]
        }

    series = pd.Series(close_prices)
    indicators = calculate_all_indicators(series)
    current_price = series.iloc[-1]

    # Calculate scores for each strategy
    scores = []
    analysis = []

    # MA strategy score
    ma_score, ma_analysis = _score_ma_strategy(indicators['ma'], current_price)
    scores.append(ma_score)
    analysis.extend(ma_analysis)

    # MACD strategy score
    macd_score, macd_analysis = _score_macd_strategy(indicators['macd'])
    scores.append(macd_score)
    analysis.extend(macd_analysis)

    # RSI strategy score
    rsi_score, rsi_analysis = _score_rsi_strategy(indicators['rsi'])
    scores.append(rsi_score)
    analysis.extend(rsi_analysis)

    # Bollinger Bands strategy score
    bb_score, bb_analysis = _score_bollinger_strategy(
        indicators['bollinger'], current_price
    )
    scores.append(bb_score)
    analysis.extend(bb_analysis)

    # Calculate overall strength (average of all strategy scores)
    strength = sum(scores) / len(scores)

    # Get signal based on risk preference thresholds
    signal = _map_strength_to_signal(strength, risk_preference)

    return {
        "signal": signal,
        "strength": round(strength, 2),
        "indicators": indicators,
        "analysis": analysis
    }


def _score_ma_strategy(ma_data: Dict[str, float], current_price: float) -> tuple:
    """
    Score Moving Average strategy.

    Returns:
        tuple: (score from -1 to 1, list of analysis strings)
    """
    ma5 = ma_data.get('ma5', current_price)
    ma10 = ma_data.get('ma10', current_price)
    ma30 = ma_data.get('ma30', current_price)

    analysis = []
    score = 0

    # Short-term MA alignment
    if current_price > ma5 > ma10 > ma30:
        score += 0.3
        analysis.append(f"MA: Price ({current_price:.2f}) above all MAs (MA5={ma5:.2f}, MA10={ma10:.2f}, MA30={ma30:.2f}) - bullish")
    elif current_price < ma5 < ma10 < ma30:
        score -= 0.3
        analysis.append(f"MA: Price ({current_price:.2f}) below all MAs (MA5={ma5:.2f}, MA10={ma10:.2f}, MA30={ma30:.2f}) - bearish")
    else:
        analysis.append(f"MA: Mixed alignment (MA5={ma5:.2f}, MA10={ma10:.2f}, MA30={ma30:.2f}) - neutral")

    # Golden cross / Death cross
    if ma5 > ma30:
        score += 0.2
        analysis.append("MA: Golden cross (MA5 > MA30) - positive")
    elif ma5 < ma30:
        score -= 0.2
        analysis.append("MA: Death cross (MA5 < MA30) - negative")

    return score, analysis


def _score_macd_strategy(macd_data: Dict[str, float]) -> tuple:
    """
    Score MACD strategy.

    Returns:
        tuple: (score from -1 to 1, list of analysis strings)
    """
    dif = macd_data.get('dif', 0)
    dea = macd_data.get('dea', 0)
    bar = macd_data.get('bar', 0)

    analysis = []
    score = 0

    # MACD cross
    if dif > dea:
        score += 0.2
        analysis.append(f"MACD: DIF ({dif:.4f}) above DEA ({dea:.4f}) - bullish")
    elif dif < dea:
        score -= 0.2
        analysis.append(f"MACD: DIF ({dif:.4f}) below DEA ({dea:.4f}) - bearish")
    else:
        analysis.append(f"MACD: DIF ({dif:.4f}) crossing DEA ({dea:.4f}) - neutral")

    # Histogram direction
    if bar > 0:
        score += 0.2
        analysis.append(f"MACD: Histogram positive ({bar:.4f}) - momentum up")
    elif bar < 0:
        score -= 0.2
        analysis.append(f"MACD: Histogram negative ({bar:.4f}) - momentum down")
    else:
        analysis.append(f"MACD: Histogram near zero ({bar:.4f}) - no clear momentum")

    # MACD zero line
    if dif > 0:
        score += 0.1
        analysis.append("MACD: DIF above zero line - bullish trend")
    elif dif < 0:
        score -= 0.1
        analysis.append("MACD: DIF below zero line - bearish trend")

    return score, analysis


def _score_rsi_strategy(rsi: float) -> tuple:
    """
    Score RSI strategy.

    Returns:
        tuple: (score from -1 to 1, list of analysis strings)
    """
    analysis = []
    score = 0

    if rsi < 30:
        score += 0.4
        analysis.append(f"RSI: {rsi:.2f} (oversold territory < 30) - strong buy signal")
    elif rsi < 40:
        score += 0.2
        analysis.append(f"RSI: {rsi:.2f} (near oversold < 40) - buy signal")
    elif rsi > 70:
        score -= 0.4
        analysis.append(f"RSI: {rsi:.2f} (overbought territory > 70) - strong sell signal")
    elif rsi > 60:
        score -= 0.2
        analysis.append(f"RSI: {rsi:.2f} (near overbought > 60) - sell signal")
    else:
        analysis.append(f"RSI: {rsi:.2f} (neutral zone 40-60) - no clear signal")

    return score, analysis


def _score_bollinger_strategy(bb_data: Dict[str, float], current_price: float) -> tuple:
    """
    Score Bollinger Bands strategy.

    Returns:
        tuple: (score from -1 to 1, list of analysis strings)
    """
    upper = bb_data.get('upper', current_price)
    middle = bb_data.get('middle', current_price)
    lower = bb_data.get('lower', current_price)

    analysis = []
    score = 0

    # Calculate position within bands
    if current_price > upper:
        score -= 0.4
        analysis.append(f"Bollinger: Price ({current_price:.2f}) above upper band ({upper:.2f}) - overbought, sell signal")
    elif current_price < lower:
        score += 0.4
        analysis.append(f"Bollinger: Price ({current_price:.2f}) below lower band ({lower:.2f}) - oversold, buy signal")
    elif current_price > middle:
        score += 0.1
        analysis.append(f"Bollinger: Price ({current_price:.2f}) above middle band ({middle:.2f}) - bullish zone")
    elif current_price < middle:
        score -= 0.1
        analysis.append(f"Bollinger: Price ({current_price:.2f}) below middle band ({middle:.2f}) - bearish zone")
    else:
        analysis.append(f"Bollinger: Price near middle band ({middle:.2f}) - neutral")

    # Band width squeeze indication
    band_width = upper - lower
    analysis.append(f"Bollinger: Band width {band_width:.2f} (upper={upper:.2f}, lower={lower:.2f})")

    return score, analysis


def _map_strength_to_signal(strength: float, risk_preference: RiskPreference) -> Signal:
    """
    Map strength score to signal based on risk preference thresholds.

    Args:
        strength: Overall strength score (-1 to 1)
        risk_preference: Risk preference level

    Returns:
        Trading signal
    """
    # Risk preference thresholds
    thresholds = {
        "conservative": (0.7, -0.5),  # (buy_threshold, sell_threshold)
        "neutral": (0.5, -0.5),
        "aggressive": (0.3, -0.7)
    }

    buy_threshold, sell_threshold = thresholds[risk_preference]

    if strength >= buy_threshold + 0.2:
        return "strong_buy"
    elif strength >= buy_threshold:
        return "buy"
    elif strength <= sell_threshold - 0.2:
        return "strong_sell"
    elif strength <= sell_threshold:
        return "sell"
    else:
        return "hold"


def get_risk_preference_info() -> Dict[str, Dict[str, float]]:
    """
    Get information about all risk preference thresholds.

    Returns:
        Dictionary with thresholds for each risk preference
    """
    return {
        "conservative": {
            "buy_threshold": 0.7,
            "strong_buy_threshold": 0.9,
            "sell_threshold": -0.5,
            "strong_sell_threshold": -0.7,
            "description": "Strict thresholds, requires strong evidence for signals"
        },
        "neutral": {
            "buy_threshold": 0.5,
            "strong_buy_threshold": 0.7,
            "sell_threshold": -0.5,
            "strong_sell_threshold": -0.7,
            "description": "Balanced thresholds, moderate sensitivity"
        },
        "aggressive": {
            "buy_threshold": 0.3,
            "strong_buy_threshold": 0.5,
            "sell_threshold": -0.7,
            "strong_sell_threshold": -0.9,
            "description": "Low buy threshold, high sell threshold for quick entries"
        }
    }

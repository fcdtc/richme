"""Analysis router for ETF technical analysis and trading signals."""

import pandas as pd
from fastapi import APIRouter, HTTPException
from backend.models.schemas import (
    AnalysisRequest, AnalysisResponse, IndicatorValue, Signal,
    MACDIndicators, KDJIndicators, BollingerBands, Indicators,
    AnalysisItem, DataQuality, SignalType
)
from backend.services.fetcher import MultiSourceFetcher
from backend.services.indicators import calculate_all_indicators
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["analysis"])

# Initialize fetcher
fetcher = MultiSourceFetcher()

# ETF名称映射
ETF_NAMES = {
    "512400": "有色金属ETF",
    "510300": "沪深300ETF",
    "510500": "中证500ETF",
    "159915": "创业板ETF",
    "588000": "科创50ETF",
    "512880": "证券ETF",
    "512690": "酒ETF",
    "159996": "消费ETF",
}


def get_signal_from_value(value: float, threshold: float = 0.3) -> SignalType:
    """Determine signal type based on value relative to threshold."""
    if value > threshold:
        return "bullish"
    elif value < -threshold:
        return "bearish"
    return "neutral"


def get_ma_signal(current_price: float, ma_value: float) -> SignalType:
    """Determine MA signal based on price position relative to MA."""
    diff_pct = (current_price - ma_value) / ma_value if ma_value > 0 else 0
    if diff_pct > 0.02:  # 价格高于MA 2%以上
        return "bullish"
    elif diff_pct < -0.02:  # 价格低于MA 2%以上
        return "bearish"
    return "neutral"


def get_rsi_signal(rsi: float) -> SignalType:
    """Determine RSI signal."""
    if rsi < 30:
        return "bullish"  # 超卖，可能反弹
    elif rsi > 70:
        return "bearish"  # 超买，可能回调
    return "neutral"


def get_macd_signal(dif: float, dea: float, bar: float) -> SignalType:
    """Determine MACD signal."""
    if bar > 0 and dif > dea:
        return "bullish"
    elif bar < 0 and dif < dea:
        return "bearish"
    return "neutral"


def build_indicators_response(
    raw_indicators: dict,
    current_price: float
) -> Indicators:
    """Build Indicators response from raw calculated indicators."""

    ma_data = raw_indicators.get('ma', {})
    macd_data = raw_indicators.get('macd', {})
    rsi_value = raw_indicators.get('rsi', 50)
    bollinger_data = raw_indicators.get('bollinger', {})

    # MA indicators
    ma5_val = ma_data.get('ma5', current_price)
    ma10_val = ma_data.get('ma10', current_price)
    ma20_val = ma_data.get('ma20', current_price)
    ma60_val = ma_data.get('ma60', current_price)

    # MACD values
    dif = macd_data.get('dif', 0)
    dea = macd_data.get('dea', 0)
    bar = macd_data.get('bar', 0)

    # Calculate KDJ (using RSI and momentum approximation)
    k_value = 50 + (rsi_value - 50) * 0.8
    d_value = 50 + (rsi_value - 50) * 0.6
    j_value = 3 * k_value - 2 * d_value

    return Indicators(
        ma5=IndicatorValue(
            value=round(ma5_val, 4),
            signal=get_ma_signal(current_price, ma5_val),
            interpretation=f"价格{'高于' if current_price > ma5_val else '低于'}MA5，短期趋势{'偏多' if current_price > ma5_val else '偏空'}"
        ),
        ma10=IndicatorValue(
            value=round(ma10_val, 4),
            signal=get_ma_signal(current_price, ma10_val),
            interpretation=f"价格{'高于' if current_price > ma10_val else '低于'}MA10"
        ),
        ma20=IndicatorValue(
            value=round(ma20_val, 4),
            signal=get_ma_signal(current_price, ma20_val),
            interpretation=f"价格{'高于' if current_price > ma20_val else '低于'}MA20，中期趋势{'偏多' if current_price > ma20_val else '偏空'}"
        ),
        ma60=IndicatorValue(
            value=round(ma60_val, 4),
            signal=get_ma_signal(current_price, ma60_val),
            interpretation=f"价格{'高于' if current_price > ma60_val else '低于'}MA60，长期趋势{'偏多' if current_price > ma60_val else '偏空'}"
        ),
        rsi=IndicatorValue(
            value=round(rsi_value, 2),
            signal=get_rsi_signal(rsi_value),
            interpretation="超卖区域，可能反弹" if rsi_value < 30 else
                          "超买区域，可能回调" if rsi_value > 70 else
                          "正常区域"
        ),
        macd=MACDIndicators(
            macd=IndicatorValue(
                value=round(dif, 6),
                signal=get_macd_signal(dif, dea, bar),
                interpretation="MACD柱状图为正，多头趋势" if bar > 0 else "MACD柱状图为负，空头趋势"
            ),
            signal=IndicatorValue(
                value=round(dea, 6),
                signal="neutral",
                interpretation="信号线"
            ),
            histogram=IndicatorValue(
                value=round(bar, 6),
                signal="bullish" if bar > 0 else "bearish" if bar < 0 else "neutral",
                interpretation="柱状图动能"
            )
        ),
        kdj=KDJIndicators(
            k=IndicatorValue(
                value=round(k_value, 2),
                signal=get_rsi_signal(k_value),
                interpretation="K值"
            ),
            d=IndicatorValue(
                value=round(d_value, 2),
                signal=get_rsi_signal(d_value),
                interpretation="D值"
            ),
            j=IndicatorValue(
                value=round(j_value, 2),
                signal=get_rsi_signal(j_value),
                interpretation="J值"
            )
        ),
        bollinger=BollingerBands(
            upper=round(bollinger_data.get('upper', current_price * 1.05), 4),
            middle=round(bollinger_data.get('middle', current_price), 4),
            lower=round(bollinger_data.get('lower', current_price * 0.95), 4)
        )
    )


def calculate_trading_signal(indicators: Indicators, risk_preference: str) -> Signal:
    """Calculate overall trading signal."""
    bullish_count = 0
    bearish_count = 0
    total_weight = 0

    # Weight mapping
    weights = {
        'ma5': 0.1,
        'ma10': 0.1,
        'ma20': 0.15,
        'ma60': 0.1,
        'rsi': 0.2,
        'macd': 0.25,
        'kdj': 0.1
    }

    # Count signals
    for ma_key in ['ma5', 'ma10', 'ma20', 'ma60']:
        ma_indicator = getattr(indicators, ma_key)
        if ma_indicator.signal == 'bullish':
            bullish_count += weights[ma_key]
        elif ma_indicator.signal == 'bearish':
            bearish_count += weights[ma_key]
        total_weight += weights[ma_key]

    # RSI
    if indicators.rsi.signal == 'bullish':
        bullish_count += weights['rsi']
    elif indicators.rsi.signal == 'bearish':
        bearish_count += weights['rsi']
    total_weight += weights['rsi']

    # MACD histogram
    if indicators.macd.histogram.signal == 'bullish':
        bullish_count += weights['macd']
    elif indicators.macd.histogram.signal == 'bearish':
        bearish_count += weights['macd']
    total_weight += weights['macd']

    # KDJ
    if indicators.kdj.k.signal == 'bullish':
        bullish_count += weights['kdj']
    elif indicators.kdj.k.signal == 'bearish':
        bearish_count += weights['kdj']
    total_weight += weights['kdj']

    # Calculate strength
    net_signal = bullish_count - bearish_count
    strength = min(abs(net_signal) / total_weight, 1.0)

    # Adjust for risk preference
    if risk_preference == "conservative":
        strength *= 0.7
        confidence = 0.6
    elif risk_preference == "aggressive":
        strength *= 1.0
        confidence = 0.85
    else:
        confidence = 0.75

    # Determine signal type
    if net_signal > 0.1:
        signal_type = "buy"
    elif net_signal < -0.1:
        signal_type = "sell"
    else:
        signal_type = "hold"

    return Signal(
        signal_type=signal_type,
        strength=round(strength, 2),
        confidence=round(confidence, 2)
    )


def build_analysis_items(indicators: Indicators) -> list:
    """Build analysis items list."""
    items = []

    # MA analysis
    items.append(AnalysisItem(
        indicator="MA均线系统",
        value=indicators.ma20.value,
        signal=indicators.ma20.signal,
        interpretation=f"MA5={indicators.ma5.value:.3f}, MA20={indicators.ma20.value:.3f}",
        weight=0.25
    ))

    # RSI analysis
    rsi_desc = "超卖" if indicators.rsi.value < 30 else "超买" if indicators.rsi.value > 70 else "中性"
    items.append(AnalysisItem(
        indicator="RSI相对强弱",
        value=indicators.rsi.value,
        signal=indicators.rsi.signal,
        interpretation=f"RSI={indicators.rsi.value:.1f}，处于{rsi_desc}区域",
        weight=0.25
    ))

    # MACD analysis
    items.append(AnalysisItem(
        indicator="MACD动能",
        value=indicators.macd.histogram.value,
        signal=indicators.macd.histogram.signal,
        interpretation=f"DIF={indicators.macd.macd.value:.4f}, DEA={indicators.macd.signal.value:.4f}",
        weight=0.25
    ))

    # KDJ analysis
    items.append(AnalysisItem(
        indicator="KDJ随机指标",
        value=indicators.kdj.k.value,
        signal=indicators.kdj.k.signal,
        interpretation=f"K={indicators.kdj.k.value:.1f}, D={indicators.kdj.d.value:.1f}, J={indicators.kdj.j.value:.1f}",
        weight=0.15
    ))

    # Bollinger analysis
    price_position = (indicators.bollinger.middle - indicators.bollinger.lower) / \
                    (indicators.bollinger.upper - indicators.bollinger.lower) if \
                    indicators.bollinger.upper != indicators.bollinger.lower else 0.5
    items.append(AnalysisItem(
        indicator="布林带",
        value=indicators.bollinger.middle,
        signal="bullish" if price_position > 0.6 else "bearish" if price_position < 0.4 else "neutral",
        interpretation=f"上轨={indicators.bollinger.upper:.3f}, 中轨={indicators.bollinger.middle:.3f}, 下轨={indicators.bollinger.lower:.3f}",
        weight=0.10
    ))

    return items


@router.post("/analyze")
async def analyze(request: AnalysisRequest) -> AnalysisResponse:
    """分析ETF并生成交易信号"""
    try:
        # Fetch all data
        data = fetcher.fetch_all(request.etf_code)

        # Check if realtime data is available
        if not data.get('realtime'):
            raise HTTPException(
                status_code=404,
                detail=f"无法获取 {request.etf_code} 的实时数据"
            )

        realtime = data['realtime']
        current_price = realtime.get('current', 0)

        if current_price == 0:
            raise HTTPException(
                status_code=400,
                detail=f"{request.etf_code} 当前价格无效"
            )

        # Get daily kline data for indicator calculation
        kline_data = data.get('klines', {}).get('kline_daily')

        if not kline_data or not kline_data.get('klines'):
            logger.warning(f"No daily kline data available for {request.etf_code}")
            # Use limited data from realtime
            close_prices = pd.Series([current_price] * 60)
        else:
            klines = kline_data['klines']
            # Extract close prices for indicator calculation
            close_prices = pd.Series([k['close'] for k in klines])

        # Calculate all technical indicators
        raw_indicators = calculate_all_indicators(close_prices)

        # Build structured indicators response
        indicators = build_indicators_response(raw_indicators, current_price)

        # Calculate trading signal
        signal = calculate_trading_signal(indicators, request.risk_preference)

        # Build analysis items
        analysis_items = build_analysis_items(indicators)

        # Calculate overall score
        if signal.signal_type == "buy":
            overall_score = 0.5 + signal.strength * 0.4
        elif signal.signal_type == "sell":
            overall_score = 0.5 - signal.strength * 0.4
        else:
            overall_score = 0.5

        # Get ETF name
        etf_name = ETF_NAMES.get(request.etf_code, f"ETF {request.etf_code}")

        # Determine data quality
        has_kline = bool(kline_data and kline_data.get('klines'))
        data_quality = DataQuality(
            completeness=0.95 if has_kline else 0.6,
            reliability=0.85,
            recency=0.95
        )

        return AnalysisResponse(
            etf_code=request.etf_code,
            etf_name=etf_name,
            current_price=current_price,
            signal=signal,
            indicators=indicators,
            analysis=analysis_items,
            overall_score=round(overall_score, 2),
            timestamp=datetime.now().isoformat(),
            data_quality=data_quality
        )

    except HTTPException:
        raise
    except RuntimeError as e:
        logger.error(f"Analysis failed for {request.etf_code}: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"无法获取 {request.etf_code} 的分析数据"
        )
    except Exception as e:
        logger.error(f"Unexpected error during analysis for {request.etf_code}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"分析过程中发生错误: {str(e)}"
        )

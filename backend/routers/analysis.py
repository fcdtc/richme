"""Analysis router for ETF technical analysis and trading signals."""

import pandas as pd
from fastapi import APIRouter, HTTPException
from backend.models.schemas import (
    AnalysisRequest, AnalysisResponse, IndicatorValue, Signal,
    MACDIndicators, KDJIndicators, BollingerBands, Indicators,
    AnalysisItem, DataQuality, SignalType, KlineData, KlineItem,
    PositionRecommendation
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

# 风险偏好配置
RISK_CONFIG = {
    "conservative": {
        "max_position_pct": 0.3,      # 最大仓位30%
        "single_trade_pct": 0.1,      # 单次交易10%
        "stop_loss_pct": 0.03,        # 止损3%
        "take_profit_pct": 0.06,      # 止盈6%
        "max_risk_per_trade": 0.02,   # 单笔最大风险2%
        "signal_threshold": 0.6,      # 信号阈值
    },
    "neutral": {
        "max_position_pct": 0.5,      # 最大仓位50%
        "single_trade_pct": 0.2,      # 单次交易20%
        "stop_loss_pct": 0.05,        # 止损5%
        "take_profit_pct": 0.10,      # 止盈10%
        "max_risk_per_trade": 0.03,   # 单笔最大风险3%
        "signal_threshold": 0.4,      # 信号阈值
    },
    "aggressive": {
        "max_position_pct": 0.8,      # 最大仓位80%
        "single_trade_pct": 0.3,      # 单次交易30%
        "stop_loss_pct": 0.08,        # 止损8%
        "take_profit_pct": 0.16,      # 止盈16%
        "max_risk_per_trade": 0.05,   # 单笔最大风险5%
        "signal_threshold": 0.3,      # 信号阈值
    }
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
    if diff_pct > 0.02:
        return "bullish"
    elif diff_pct < -0.02:
        return "bearish"
    return "neutral"


def get_rsi_signal(rsi: float) -> SignalType:
    """Determine RSI signal."""
    if rsi < 30:
        return "bullish"
    elif rsi > 70:
        return "bearish"
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

    ma5_val = ma_data.get('ma5', current_price)
    ma10_val = ma_data.get('ma10', current_price)
    ma20_val = ma_data.get('ma20', current_price)
    ma60_val = ma_data.get('ma60', current_price)

    dif = macd_data.get('dif', 0)
    dea = macd_data.get('dea', 0)
    bar = macd_data.get('bar', 0)

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

    weights = {
        'ma5': 0.1,
        'ma10': 0.1,
        'ma20': 0.15,
        'ma60': 0.1,
        'rsi': 0.2,
        'macd': 0.25,
        'kdj': 0.1
    }

    for ma_key in ['ma5', 'ma10', 'ma20', 'ma60']:
        ma_indicator = getattr(indicators, ma_key)
        if ma_indicator.signal == 'bullish':
            bullish_count += weights[ma_key]
        elif ma_indicator.signal == 'bearish':
            bearish_count += weights[ma_key]
        total_weight += weights[ma_key]

    if indicators.rsi.signal == 'bullish':
        bullish_count += weights['rsi']
    elif indicators.rsi.signal == 'bearish':
        bearish_count += weights['rsi']
    total_weight += weights['rsi']

    if indicators.macd.histogram.signal == 'bullish':
        bullish_count += weights['macd']
    elif indicators.macd.histogram.signal == 'bearish':
        bearish_count += weights['macd']
    total_weight += weights['macd']

    if indicators.kdj.k.signal == 'bullish':
        bullish_count += weights['kdj']
    elif indicators.kdj.k.signal == 'bearish':
        bearish_count += weights['kdj']
    total_weight += weights['kdj']

    net_signal = bullish_count - bearish_count
    strength = min(abs(net_signal) / total_weight, 1.0)

    if risk_preference == "conservative":
        strength *= 0.7
        confidence = 0.6
    elif risk_preference == "aggressive":
        confidence = 0.85
    else:
        confidence = 0.75

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

    items.append(AnalysisItem(
        indicator="MA均线系统",
        value=indicators.ma20.value,
        signal=indicators.ma20.signal,
        interpretation=f"MA5={indicators.ma5.value:.3f}, MA20={indicators.ma20.value:.3f}",
        weight=0.25
    ))

    rsi_desc = "超卖" if indicators.rsi.value < 30 else "超买" if indicators.rsi.value > 70 else "中性"
    items.append(AnalysisItem(
        indicator="RSI相对强弱",
        value=indicators.rsi.value,
        signal=indicators.rsi.signal,
        interpretation=f"RSI={indicators.rsi.value:.1f}，处于{rsi_desc}区域",
        weight=0.25
    ))

    items.append(AnalysisItem(
        indicator="MACD动能",
        value=indicators.macd.histogram.value,
        signal=indicators.macd.histogram.signal,
        interpretation=f"DIF={indicators.macd.macd.value:.4f}, DEA={indicators.macd.signal.value:.4f}",
        weight=0.25
    ))

    items.append(AnalysisItem(
        indicator="KDJ随机指标",
        value=indicators.kdj.k.value,
        signal=indicators.kdj.k.signal,
        interpretation=f"K={indicators.kdj.k.value:.1f}, D={indicators.kdj.d.value:.1f}, J={indicators.kdj.j.value:.1f}",
        weight=0.15
    ))

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


def calculate_position_recommendation(
    signal: Signal,
    current_price: float,
    total_capital: float,
    holding_amount: float,
    risk_preference: str,
    indicators: Indicators
) -> PositionRecommendation:
    """Calculate position recommendation based on signal, capital, and risk preference.

    基金交易特点：
    - 不需要计算股数，只给出交易金额
    - 策略包括：加仓(buy)、减仓(sell)、持有不动(hold)
    - 持有不动需要量化依据支撑
    """

    config = RISK_CONFIG.get(risk_preference, RISK_CONFIG["neutral"])

    # 当前持仓比例
    current_position_pct = holding_amount / total_capital if total_capital > 0 else 0

    # 最大持仓金额
    max_position = total_capital * config["max_position_pct"]

    # 信号得分 (-1 到 1)
    signal_type = signal.signal_type
    signal_strength = signal.strength

    # 计算综合信号得分
    signal_score = 0.0
    if signal_type == "buy":
        signal_score = signal_strength
    elif signal_type == "sell":
        signal_score = -signal_strength

    # 判断趋势方向和强度
    ma5_val = indicators.ma5.value
    ma10_val = indicators.ma10.value
    ma20_val = indicators.ma20.value
    ma60_val = indicators.ma60.value

    # 趋势判断：基于均线排列
    if ma5_val > ma10_val > ma20_val > ma60_val:
        trend_direction = "up"
        trend_strength = min((ma5_val - ma60_val) / ma60_val, 1.0)
    elif ma5_val < ma10_val < ma20_val < ma60_val:
        trend_direction = "down"
        trend_strength = min((ma60_val - ma5_val) / ma60_val, 1.0)
    else:
        trend_direction = "sideways"
        trend_strength = 0.3  # 震荡趋势默认强度

    # 计算支撑位和阻力位
    support_level = indicators.bollinger.lower
    resistance_level = indicators.bollinger.upper

    # 根据趋势调整支撑阻力
    if trend_direction == "up":
        support_level = max(support_level, ma20_val)
    elif trend_direction == "down":
        resistance_level = min(resistance_level, ma20_val)

    # 初始化
    action = "hold"
    target_pct = current_position_pct
    amount = 0.0

    # 检查当前仓位是否超过限制
    position_over_limit = holding_amount > max_position

    # ========== 核心决策逻辑 ==========

    # 计算综合得分 (结合信号得分和趋势)
    combined_score = signal_score * 0.6
    if trend_direction == "up":
        combined_score += trend_strength * 0.3
    elif trend_direction == "down":
        combined_score -= trend_strength * 0.3

    # 加入RSI修正
    rsi = indicators.rsi.value
    if rsi < 30:
        combined_score += 0.2  # 超卖加分
    elif rsi > 70:
        combined_score -= 0.2  # 超买减分

    # 加入MACD修正
    if indicators.macd.histogram.value > 0:
        combined_score += 0.1
    else:
        combined_score -= 0.1

    # 限制得分范围
    combined_score = max(-1.0, min(1.0, combined_score))

    # 决策阈值（根据风险偏好调整）
    buy_threshold = config["signal_threshold"]
    sell_threshold = -config["signal_threshold"]

    # 特殊情况：仓位超限必须减仓
    if position_over_limit:
        action = "sell"
        target_pct = config["max_position_pct"]
    elif combined_score >= buy_threshold:
        # 买入信号：检查是否有空间
        if current_position_pct < config["max_position_pct"]:
            add_pct = config["single_trade_pct"] * abs(combined_score)
            target_pct = min(current_position_pct + add_pct, config["max_position_pct"])
            action = "buy"
        else:
            action = "hold"
            target_pct = current_position_pct
    elif combined_score <= sell_threshold:
        # 卖出信号
        if holding_amount > 0:
            sell_pct = config["single_trade_pct"] * abs(combined_score)
            target_pct = max(0, current_position_pct - sell_pct)
            action = "sell"
        else:
            action = "hold"
            target_pct = 0
    else:
        # 持有不动：有量化依据支撑
        action = "hold"
        target_pct = current_position_pct

    # 计算目标持仓金额
    target_position = total_capital * target_pct

    # 计算交易金额
    if action == "buy":
        amount = target_position - holding_amount
    elif action == "sell":
        amount = holding_amount - target_position
    else:
        amount = 0

    # 计算止损止盈价格
    stop_loss_price = round(current_price * (1 - config["stop_loss_pct"]), 3)
    take_profit_price = round(current_price * (1 + config["take_profit_pct"]), 3)

    # 计算风险金额
    risk_amount = amount * config["stop_loss_pct"] if action == "buy" else 0
    risk_percentage = risk_amount / total_capital if total_capital > 0 else 0

    # ========== 构建操作理由 ==========
    reasons = []

    # 量化依据说明
    reasons.append(f"综合得分{combined_score:.2f}(阈值±{buy_threshold})")
    reasons.append(f"趋势:{trend_direction}(强度{trend_strength:.1%})")

    if position_over_limit:
        reasons.append(f"仓位{current_position_pct:.1%}超限{config['max_position_pct']:.0%}")

    if action == "buy":
        reasons.append(f"得分突破阈值，建议加仓")
        if rsi < 30:
            reasons.append("RSI超卖")
        if indicators.macd.histogram.value > 0:
            reasons.append("MACD多头")
    elif action == "sell":
        reasons.append(f"得分低于阈值，建议减仓")
        if rsi > 70:
            reasons.append("RSI超买")
        if indicators.macd.histogram.value < 0:
            reasons.append("MACD空头")
    else:
        # 持有不动的量化依据
        reasons.append(f"得分在阈值内，持有不动")
        if trend_direction == "sideways":
            reasons.append("震荡行情观望")
        if 0 < current_position_pct < config["max_position_pct"]:
            reasons.append(f"仓位合理({current_position_pct:.1%})")

    reason = "；".join(reasons)

    return PositionRecommendation(
        action=action,
        amount=round(amount, 2),
        percentage=round(target_pct * 100, 1),
        stop_loss_price=stop_loss_price,
        take_profit_price=take_profit_price,
        risk_amount=round(risk_amount, 2),
        risk_percentage=round(risk_percentage * 100, 2),
        max_position=round(max_position, 2),
        current_position=round(holding_amount, 2),
        target_position=round(target_position, 2),
        signal_score=round(combined_score, 2),
        trend_direction=trend_direction,
        trend_strength=round(trend_strength, 2),
        support_level=round(support_level, 3),
        resistance_level=round(resistance_level, 3),
        reason=reason
    )


def build_kline_data(kline_data: dict) -> KlineData:
    """Build KlineData from raw kline data."""
    klines = []
    for item in kline_data.get('klines', []):
        klines.append(KlineItem(
            date=item.get('date', ''),
            open=item.get('open', 0),
            high=item.get('high', 0),
            low=item.get('low', 0),
            close=item.get('close', 0),
            volume=item.get('volume', 0),
            ma5=item.get('ma5', 0),
            ma10=item.get('ma10', 0),
            ma30=item.get('ma30', 0)
        ))

    return KlineData(
        code=kline_data.get('code', ''),
        period=kline_data.get('period', ''),
        count=len(klines),
        klines=klines,
        fetch_time=kline_data.get('fetch_time', ''),
        source=kline_data.get('source', '')
    )


@router.post("/analyze")
async def analyze(request: AnalysisRequest) -> AnalysisResponse:
    """分析ETF并生成交易信号和仓位建议"""
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
            close_prices = pd.Series([current_price] * 60)
        else:
            klines = kline_data['klines']
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
        etf_name = ETF_NAMES.get(request.etf_code, realtime.get('name', f"ETF {request.etf_code}"))

        # Determine data quality
        has_kline = bool(kline_data and kline_data.get('klines'))
        data_quality = DataQuality(
            completeness=0.95 if has_kline else 0.6,
            reliability=0.85,
            recency=0.95
        )

        # Build K-line data for frontend
        kline_response = build_kline_data(kline_data) if kline_data else None

        # Calculate position recommendation
        total_capital = request.total_capital or 100000
        holding_amount = request.holding_amount or 0
        position = calculate_position_recommendation(
            signal, current_price, total_capital, holding_amount,
            request.risk_preference, indicators
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
            data_quality=data_quality,
            klines=kline_response,
            position=position
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

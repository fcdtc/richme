# RichMe ETF量化交易系统说明书

> 版本：1.0.0
> 更新日期：2026-03-08

---

## 目录

1. [系统概述](#1-系统概述)
2. [技术架构](#2-技术架构)
3. [技术指标详解](#3-技术指标详解)
4. [交易策略系统](#4-交易策略系统)
5. [信号生成机制](#5-信号生成机制)
6. [仓位管理系统](#6-仓位管理系统)
7. [风险管理系统](#7-风险管理系统)
8. [Web端界面指标说明](#8-web端界面指标说明)
9. [回测系统](#9-回测系统)
10. [数据源与数据质量](#10-数据源与数据质量)
11. [API接口说明](#11-api接口说明)

---

## 1. 系统概述

### 1.1 系统定位

RichMe是一个专业的ETF（交易所交易基金）量化交易分析系统，提供以下核心功能：

- **技术分析**：基于多维度技术指标的市场分析
- **信号生成**：自动生成买入/卖出/持有交易信号
- **仓位管理**：基于凯利公式的智能仓位建议
- **风险控制**：多层次的止损止盈机制
- **历史回测**：策略绩效验证与优化

### 1.2 核心特性

| 特性 | 描述 |
|------|------|
| 多策略支持 | 趋势跟踪 + 底部吸筹双策略 |
| 多时间框架 | 日线 + 周线联合分析 |
| 多数据源 | 新浪财经（主）+ 腾讯财经（备） |
| 智能仓位 | 凯利公式 + 安全边际 |
| 动态止损 | 固定比例/ATR/支撑位/追踪止损 |

### 1.3 支持的ETF品种

| 代码 | 名称 |
|------|------|
| 512400 | 有色金属ETF |
| 510300 | 沪深300ETF |
| 510500 | 中证500ETF |
| 159915 | 创业板ETF |
| 588000 | 科创50ETF |
| 512880 | 证券ETF |
| 512690 | 酒ETF |
| 159996 | 消费ETF |

---

## 2. 技术架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      前端层 (Vue 3 + TypeScript)              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────────┐│
│  │输入表单  │ │结果展示  │ │K线图表  │ │仓位建议/回测组件    ││
│  └─────────┘ └─────────┘ └─────────┘ └─────────────────────┘│
└───────────────────────────┬─────────────────────────────────┘
                            │ RESTful API
┌───────────────────────────▼─────────────────────────────────┐
│                      后端层 (FastAPI + Python)                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │  数据路由   │ │  分析路由   │ │      回测路由           ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │  数据获取   │ │  指标计算   │ │      策略引擎           ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                      数据源层                                 │
│  ┌─────────────────────┐ ┌─────────────────────┐            │
│  │   新浪财经 (主)     │ │   腾讯财经 (备)     │            │
│  └─────────────────────┘ └─────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈

#### 后端技术栈
| 组件 | 技术 | 用途 |
|------|------|------|
| Web框架 | FastAPI | 高性能异步API |
| 数据处理 | Pandas/NumPy | 数值计算 |
| 技术指标 | TA-Lib | 专业指标计算（主） |
| 备用计算 | Pandas原生 | 无TA-Lib时的替代方案 |
| 数据验证 | Pydantic | 请求/响应模型验证 |

#### 前端技术栈
| 组件 | 技术 | 用途 |
|------|------|------|
| 框架 | Vue 3 | 响应式UI |
| 语言 | TypeScript | 类型安全 |
| UI库 | Element Plus | 企业级组件 |
| 图表 | ECharts | K线/曲线可视化 |
| 构建 | Vite | 快速开发构建 |

---

## 3. 技术指标详解

### 3.1 移动平均线 (MA - Moving Average)

#### 3.1.1 指标含义
移动平均线是最基础的趋势跟踪指标，通过计算一定时期内的平均价格，平滑价格波动，揭示价格趋势方向。

#### 3.1.2 计算公式

**简单移动平均 (SMA):**
```
MA_n = (P_1 + P_2 + ... + P_n) / n
```

其中：
- `P_i` = 第i日的收盘价
- `n` = 周期天数

**系统支持的周期：**
| 周期 | 名称 | 用途 |
|------|------|------|
| MA5 | 5日均线 | 短期趋势，快速反应 |
| MA10 | 10日均线 | 短中期趋势 |
| MA20 | 20日均线 | 中期趋势，月线参考 |
| MA60 | 60日均线 | 长期趋势，季线参考 |

#### 3.1.3 信号判定逻辑

```python
def get_ma_signal(current_price, ma_value):
    """
    MA信号判定
    """
    diff_pct = (current_price - ma_value) / ma_value

    if diff_pct > 0.02:      # 价格高于MA 2%以上
        return "bullish"      # 多头信号
    elif diff_pct < -0.02:    # 价格低于MA 2%以上
        return "bearish"      # 空头信号
    else:
        return "neutral"      # 中性
```

#### 3.1.4 均线排列信号

| 排列形态 | 条件 | 信号含义 |
|----------|------|----------|
| 多头排列 | 价格 > MA5 > MA10 > MA20 > MA60 | 强势上涨趋势，看多 |
| 空头排列 | 价格 < MA5 < MA10 < MA20 < MA60 | 强势下跌趋势，看空 |
| 金叉 | 短期MA上穿长期MA | 买入信号 |
| 死叉 | 短期MA下穿长期MA | 卖出信号 |

---

### 3.2 MACD指标 (指数平滑异同移动平均线)

#### 3.2.1 指标含义
MACD (Moving Average Convergence Divergence) 是趋势跟踪动量指标，通过两条不同周期的指数移动平均线之差，来判断趋势方向和动量强度。

#### 3.2.2 计算公式

```
DIF = EMA(12) - EMA(26)
DEA = EMA(DIF, 9)
MACD柱 = DIF - DEA
```

**指数移动平均 (EMA) 计算：**
```
EMA_today = α × P_today + (1-α) × EMA_yesterday
α = 2 / (n + 1)
```

#### 3.2.3 参数说明

| 参数 | 默认值 | 含义 |
|------|--------|------|
| 快线周期 | 12 | 快速EMA周期 |
| 慢线周期 | 26 | 慢速EMA周期 |
| 信号线周期 | 9 | DEA计算周期 |

#### 3.2.4 信号判定逻辑

```python
def get_macd_signal(dif, dea, bar):
    """
    MACD信号判定
    """
    # 柱状图和DIF/DEA位置综合判断
    if bar > 0 and dif > dea:
        return "bullish"      # 多头：柱状图为正，DIF在DEA上方
    elif bar < 0 and dif < dea:
        return "bearish"      # 空头：柱状图为负，DIF在DEA下方
    else:
        return "neutral"      # 中性
```

#### 3.2.5 MACD信号解读表

| 形态 | DIF | DEA | 柱状图 | 信号 |
|------|-----|-----|--------|------|
| 金叉 | 上穿DEA | - | 由负转正 | 买入 |
| 死叉 | 下穿DEA | - | 由正转负 | 卖出 |
| 多头趋势 | > 0 | > 0 | > 0 | 强势看多 |
| 空头趋势 | < 0 | < 0 | < 0 | 强势看空 |
| 柱状图放大 | - | - | 绝对值增大 | 动量增强 |
| 柱状图缩小 | - | - | 绝对值减小 | 动量减弱 |

---

### 3.3 RSI指标 (相对强弱指数)

#### 3.3.1 指标含义
RSI (Relative Strength Index) 是衡量价格变动速度和变化幅度的动量振荡指标，用于识别超买超卖状态。

#### 3.3.2 计算公式

```
RS = 平均涨幅 / 平均跌幅
RSI = 100 - (100 / (1 + RS))
```

**详细计算步骤：**
```python
delta = price.diff()                    # 价格变化
gain = delta.where(delta > 0, 0)        # 涨幅
loss = -delta.where(delta < 0, 0)       # 跌幅

avg_gain = gain.rolling(14).mean()      # 14日平均涨幅
avg_loss = loss.rolling(14).mean()      # 14日平均跌幅

rs = avg_gain / avg_loss
rsi = 100 - (100 / (1 + rs))
```

#### 3.3.3 参数说明

| 参数 | 默认值 | 含义 |
|------|--------|------|
| 周期 | 14 | RSI计算周期 |

#### 3.3.4 RSI区间划分与信号

| RSI值 | 区域 | 信号含义 |
|-------|------|----------|
| > 70 | 超买区 | 价格可能回调，卖出信号 |
| 60-70 | 偏强区 | 多头优势，警惕回调 |
| 40-60 | 中性区 | 多空平衡，无明确信号 |
| 30-40 | 偏弱区 | 空头优势，关注反弹 |
| < 30 | 超卖区 | 价格可能反弹，买入信号 |

#### 3.3.5 信号判定逻辑

```python
def get_rsi_signal(rsi):
    if rsi < 30:
        return "bullish"      # 超卖，可能反弹
    elif rsi > 70:
        return "bearish"      # 超买，可能回调
    else:
        return "neutral"      # 中性区域
```

---

### 3.4 布林带 (Bollinger Bands)

#### 3.4.1 指标含义
布林带是由三条轨道线组成的波动性指标，中轨为移动平均线，上下轨基于标准差计算，用于判断价格的相对高低位置和波动范围。

#### 3.4.2 计算公式

```
中轨 = MA(20)
上轨 = 中轨 + 2 × 标准差
下轨 = 中轨 - 2 × 标准差
```

**标准差计算：**
```
标准差 = sqrt(Σ(Price_i - MA)² / n)
```

#### 3.4.3 参数说明

| 参数 | 默认值 | 含义 |
|------|--------|------|
| 周期 | 20 | 移动平均周期 |
| 标准差倍数 | 2 | 上下轨偏离倍数 |

#### 3.4.4 信号判定逻辑

```python
def get_bollinger_signal(current_price, upper, middle, lower):
    if current_price > upper:
        return "bearish"      # 超买，价格过高
    elif current_price < lower:
        return "bullish"      # 超卖，价格过低
    elif current_price > middle:
        return "bullish"      # 偏强区域
    else:
        return "bearish"      # 偏弱区域
```

#### 3.4.5 布林带应用场景

| 场景 | 特征 | 操作建议 |
|------|------|----------|
| 价格触及上轨 | 短期超买 | 考虑减仓 |
| 价格触及下轨 | 短期超卖 | 考虑建仓 |
| 带宽收窄 | 波动率降低 | 关注突破方向 |
| 带宽扩张 | 波动率增大 | 趋势可能加速 |

---

### 3.5 KDJ指标 (随机指标)

#### 3.5.1 指标含义
KDJ是由K、D、J三条线组成的动量指标，用于判断价格在某一时期内的相对位置，识别超买超卖和转折信号。

#### 3.5.2 计算公式

本系统采用**合成KDJ**（基于RSI派生），计算方式如下：

```python
# 基于RSI派生KDJ值
K = 50 + (RSI - 50) × 0.8
D = 50 + (RSI - 50) × 0.6
J = 3 × K - 2 × D
```

> 注：此为简化版本，标准KDJ计算涉及RSV（未成熟随机值），此处采用RSI派生方式实现。

#### 3.5.3 信号判定

| K/D值 | 区域 | 信号 |
|-------|------|------|
| > 80 | 超买区 | 卖出信号 |
| < 20 | 超卖区 | 买入信号 |
| K > D | 金叉 | 买入信号 |
| K < D | 死叉 | 卖出信号 |
| J > 100 | 极度超买 | 强烈卖出 |
| J < 0 | 极度超卖 | 强烈买入 |

---

### 3.6 ATR指标 (平均真实波幅)

#### 3.6.1 指标含义
ATR (Average True Range) 衡量市场波动性，用于动态设置止损位。

#### 3.6.2 计算公式

```
真实波幅(TR) = max(
    当日最高 - 当日最低,
    |当日最高 - 昨日收盘|,
    |当日最低 - 昨日收盘|
)

ATR = TR的n日移动平均（默认n=14）
```

#### 3.6.3 应用场景

用于动态止损计算：
```
止损价 = 当前价格 - ATR × 倍数（默认2倍）
```

---

### 3.7 成交量分析

#### 3.7.1 放量检测 (Volume Surge)

**计算公式：**
```python
平均成交量 = volume.rolling(20).mean()
放量比例 = 当前成交量 / 平均成交量

放量判定: 放量比例 >= 阈值(默认1.5)
```

**信号含义：**
- 放量上涨：买盘积极，趋势可能延续
- 放量下跌：卖盘积极，趋势可能加速下跌

#### 3.7.2 缩量检测 (Volume Shrink)

**计算公式：**
```python
缩量判定: 放量比例 <= 阈值(默认0.7)
```

**信号含义：**
- 缩量下跌：卖盘枯竭，可能见底
- 缩量上涨：买盘谨慎，可能乏力

---

### 3.8 支撑位与阻力位

#### 3.8.1 计算方法

```python
支撑位 = 最近n日(默认20日)最低价
阻力位 = 最近n日(默认20日)最高价
```

#### 3.8.2 应用场景

| 场景 | 操作建议 |
|------|----------|
| 价格接近支撑位 | 关注买入机会 |
| 价格接近阻力位 | 考虑获利了结 |
| 跌破支撑位 | 支撑变阻力，考虑止损 |
| 突破阻力位 | 阻力变支撑，可加仓 |

---

## 4. 交易策略系统

### 4.1 策略概览

系统采用**双策略架构**，根据市场环境自动切换：

```
┌─────────────────────────────────────────────────────────┐
│                   策略选择器                            │
│  ┌─────────────────┐    ┌─────────────────┐            │
│  │  趋势跟踪策略   │    │  底部吸筹策略   │            │
│  │ (右侧交易)      │    │ (左侧交易)      │            │
│  └─────────────────┘    └─────────────────┘            │
│           │                      │                      │
│           ▼                      ▼                      │
│  ┌─────────────────────────────────────────────────────┐│
│  │              多时间框架过滤器                        ││
│  │         (周线趋势过滤日线信号)                       ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

### 4.2 趋势跟踪策略 (Trend Following)

#### 4.2.1 策略理念
右侧交易策略，在趋势确立后跟随趋势，"让利润奔跑"。

#### 4.2.2 买入条件（必须同时满足）

| 条件 | 具体要求 | 权重 |
|------|----------|------|
| 均线排列 | 当前价格 > 短期MA > 长期MA | 30% |
| MACD确认 | DIF > DEA 且 柱状图 > 0 | 25% |
| RSI状态 | RSI未超买(< 70) | 20% |
| 成交量 | 放量确认（可选加分） | 10% |
| 周线趋势 | 周线MA5 > MA20（牛市环境） | 权重调节 |

#### 4.2.3 卖出条件

| 条件 | 具体要求 |
|------|----------|
| 均线死叉 | 当前价格 < 短期MA < 长期MA |
| MACD转空 | DIF < DEA 且 柱状图 < 0 |
| RSI超买 | RSI > 70 |

#### 4.2.4 评分计算

```python
def calculate_trend_signal(data, config):
    score = 0.0

    # 均线排列 (+0.3/-0.3)
    if current_price > ma_short > ma_long:
        score += 0.3
    elif current_price < ma_short < ma_long:
        score -= 0.3

    # MACD确认 (+0.25/-0.25)
    if dif > dea and bar > 0:
        score += 0.25
    elif dif < dea and bar < 0:
        score -= 0.25

    # RSI检查 (+0.2/-0.15)
    if rsi < config['rsi_oversold']:
        score += 0.2
    elif rsi > config['rsi_overbought']:
        score -= 0.15

    # 放量确认 (+0.1)
    if volume_surge and score > 0:
        score += 0.1

    return clamp(score, -1.0, 1.0)
```

### 4.3 底部吸筹策略 (Bottom Fishing)

#### 4.3.1 策略理念
左侧交易策略，在价格超跌时逆向买入，"在别人恐惧时贪婪"。

#### 4.3.2 买入条件

| 条件 | 具体要求 | 权重 |
|------|----------|------|
| 布林下轨 | 价格接近或跌破布林下轨(±2%) | 35% |
| RSI超卖 | RSI < 阈值(默认20) | 25% |
| 支撑位 | 价格接近支撑位(±2%) | 20% |
| 缩量 | 成交量萎缩(≤70%均量) | 20% |

#### 4.3.3 评分计算

```python
def calculate_bottom_signal(data, config):
    score = 0.0

    # 布林下轨 (+0.35)
    if current_price <= bb_lower * 1.02:
        score += 0.35

    # RSI超卖 (+0.25/+0.15)
    if rsi < config['rsi_bottom_threshold']:
        score += 0.25
    elif rsi < 30:
        score += 0.15

    # 支撑位 (+0.20)
    if abs(current_price - support_level) / support_level < 0.02:
        score += 0.20

    # 缩量 (+0.20)
    if volume_shrink:
        score += 0.20

    return clamp(score, -1.0, 1.0)
```

### 4.4 多时间框架分析

#### 4.4.1 分析逻辑

```
周线趋势判断：
- MA5 > MA20 → 牛市 → 倾向趋势跟踪策略
- MA5 < MA20 → 熊市 → 倾向底部吸筹策略
- 否则 → 震荡 → 综合两种策略
```

#### 4.4.2 权重调节机制

| 周线趋势 | 策略偏好 | 日线权重调节 |
|----------|----------|--------------|
| 牛市 | 趋势跟踪(70%) | 日线信号 × 1.3 |
| 熊市 | 底部吸筹(60%) | 日线信号 × 0.7 |
| 震荡 | 综合(50%) | 日线信号 × 1.0 |

---

## 5. 信号生成机制

### 5.1 综合评分体系

#### 5.1.1 指标权重分配

| 指标 | 权重 | 说明 |
|------|------|------|
| MA均线系统 | 45% | MA5(10%) + MA10(10%) + MA20(15%) + MA60(10%) |
| RSI | 20% | 动量判断 |
| MACD | 25% | 趋势确认 |
| KDJ | 10% | 辅助判断 |

#### 5.1.2 信号评分计算

```python
def calculate_signal(indicators, risk_preference):
    bullish_count = 0
    bearish_count = 0

    # MA贡献
    for ma_key in ['ma5', 'ma10', 'ma20', 'ma60']:
        if indicators[ma_key].signal == 'bullish':
            bullish_count += weights[ma_key]
        elif indicators[ma_key].signal == 'bearish':
            bearish_count += weights[ma_key]

    # RSI贡献
    if indicators.rsi.signal == 'bullish':
        bullish_count += 0.2
    elif indicators.rsi.signal == 'bearish':
        bearish_count += 0.2

    # MACD贡献
    if indicators.macd.histogram.signal == 'bullish':
        bullish_count += 0.25
    elif indicators.macd.histogram.signal == 'bearish':
        bearish_count += 0.25

    # 净信号
    net_signal = bullish_count - bearish_count
    strength = min(abs(net_signal), 1.0)

    # 信号类型判定
    if net_signal > 0.1:
        signal_type = "buy"
    elif net_signal < -0.1:
        signal_type = "sell"
    else:
        signal_type = "hold"

    return signal_type, strength
```

### 5.2 风险偏好调节

#### 5.2.1 三种风险偏好

| 偏好类型 | 特点 | 买入阈值 | 卖出阈值 | 适用人群 |
|----------|------|----------|----------|----------|
| 保守型 | 严格阈值，强信号确认 | 0.7 | -0.5 | 风险厌恶型投资者 |
| 中性型 | 平衡阈值，适中敏感 | 0.5 | -0.5 | 一般投资者 |
| 激进型 | 低买入阈值，快速响应 | 0.3 | -0.7 | 风险偏好型投资者 |

#### 5.2.2 信号映射表

```python
def map_strength_to_signal(strength, risk_preference):
    thresholds = {
        "conservative": {"buy": 0.7, "sell": -0.5},
        "neutral": {"buy": 0.5, "sell": -0.5},
        "aggressive": {"buy": 0.3, "sell": -0.7}
    }

    buy_threshold = thresholds[risk_preference]["buy"]
    sell_threshold = thresholds[risk_preference]["sell"]

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
```

### 5.3 信号类型说明

| 信号 | 含义 | 建议操作 |
|------|------|----------|
| strong_buy | 强烈买入 | 积极建仓 |
| buy | 买入 | 适度建仓 |
| hold | 持有 | 维持现状 |
| sell | 卖出 | 适度减仓 |
| strong_sell | 强烈卖出 | 积极清仓 |

---

## 6. 仓位管理系统

### 6.1 凯利公式 (Kelly Criterion)

#### 6.1.1 公式原理

凯利公式用于计算最优仓位比例，在长期中实现资金增长最大化。

**原始公式：**
```
f* = (bp - q) / b
```

其中：
- f* = 最优仓位比例
- b = 盈亏比（平均盈利/平均亏损）
- p = 胜率
- q = 1 - p（败率）

#### 6.1.2 系统实现

```python
def calculate_kelly_position(win_probability, avg_win, avg_loss, config, equity):
    # 计算盈亏比
    odds = avg_win / abs(avg_loss) if avg_loss != 0 else 1.5

    # 凯利公式
    q = 1 - win_probability
    kelly_pct = (odds * win_probability - q) / odds

    # 安全边际：使用分数凯利（默认1/4凯利）
    safe_kelly = kelly_pct * config['kelly_fraction']  # 默认0.25

    # 边界约束
    position_size = equity * safe_kelly
    position_size = clamp(position_size,
                          equity * min_position_pct,
                          equity * max_position_pct)

    return position_size
```

#### 6.1.3 参数配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| kelly_fraction | 0.25 | 分数凯利系数（1/4凯利） |
| max_position_pct | 30% | 单笔最大仓位比例 |
| min_position_pct | 5% | 单笔最小仓位比例 |
| avg_win_avg_loss_ratio | 1.5 | 默认盈亏比估计 |

### 6.2 仓位建议计算

#### 6.2.1 决策流程

```
1. 计算综合得分 = 信号得分 × 0.6 + 趋势调整 × 0.3 + RSI修正 + MACD修正
2. 根据风险偏好获取阈值
3. 判定操作类型：
   - 得分 >= 买入阈值 → 加仓
   - 得分 <= 卖出阈值 → 减仓
   - 其他 → 持有
4. 计算仓位大小（使用凯利公式）
5. 计算止损止盈价格
```

#### 6.2.2 综合得分计算

```python
def calculate_combined_score(signal_score, trend_direction, trend_strength, rsi, macd_histogram):
    combined = signal_score * 0.6

    # 趋势调整
    if trend_direction == "up":
        combined += trend_strength * 0.3
    elif trend_direction == "down":
        combined -= trend_strength * 0.3

    # RSI修正
    if rsi < 30:
        combined += 0.2  # 超卖加分
    elif rsi > 70:
        combined -= 0.2  # 超买减分

    # MACD修正
    if macd_histogram > 0:
        combined += 0.1
    else:
        combined -= 0.1

    return clamp(combined, -1.0, 1.0)
```

---

## 7. 风险管理系统

### 7.1 止损机制

#### 7.1.1 四重止损体系

| 止损类型 | 计算方法 | 触发条件 |
|----------|----------|----------|
| 固定比例止损 | 入场价 × (1 - 固定比例) | 始终生效 |
| ATR止损 | 当前价 - ATR × 倍数 | 波动性调节 |
| 支撑位止损 | 支撑位 × (1 - 缓冲比例) | 技术位保护 |
| 追踪止损 | 盈利达到阈值后启动 | 盈利保护 |

#### 7.1.2 止损计算

```python
def calculate_stop_loss(entry_price, current_price, data, config, current_profit_pct):
    stops = []

    # 1. 固定比例止损
    fixed_stop = entry_price * (1 - config['fixed_pct'])
    stops.append(fixed_stop)

    # 2. ATR止损
    atr = calculate_atr(data, config['atr_period'])
    atr_stop = current_price - atr * config['atr_multiplier']
    stops.append(atr_stop)

    # 3. 支撑位止损
    support_level = calculate_support(data)
    support_stop = support_level * (1 - config['support_pct'])
    stops.append(support_stop)

    # 4. 追踪止损（盈利后激活）
    if current_profit_pct > config['trailing_activation_pct']:
        trailing_stop = max(stops)
        stops.append(trailing_stop)

    # 返回最保守（最高）止损价
    return max(stops)
```

#### 7.1.3 止损参数配置

| 参数 | 保守型 | 中性型 | 激进型 |
|------|--------|--------|--------|
| 固定止损比例 | 3% | 5% | 8% |
| ATR倍数 | 2.0 | 2.0 | 2.0 |
| 支撑位缓冲 | 2% | 2% | 2% |
| 追踪止损激活 | 盈利2% | 盈利2% | 盈利2% |

### 7.2 止盈机制

#### 7.2.1 止盈计算

```python
take_profit_price = current_price * (1 + take_profit_pct)
```

#### 7.2.2 止盈参数

| 风险偏好 | 止盈比例 | 盈亏比 |
|----------|----------|--------|
| 保守型 | 6% | 1:2 |
| 中性型 | 10% | 1:2 |
| 激进型 | 16% | 1:2 |

### 7.3 单笔风险控制

| 风险偏好 | 单笔最大风险 | 单次交易比例 |
|----------|--------------|--------------|
| 保守型 | 2% | 10% |
| 中性型 | 3% | 20% |
| 激进型 | 5% | 30% |

---

## 8. Web端界面指标说明

### 8.1 分析结果卡片 (ResultCard)

#### 8.1.1 显示内容

| 字段 | 含义 | 取值范围 |
|------|------|----------|
| etf_code | ETF代码 | 如 512400 |
| etf_name | ETF名称 | 如 有色金属ETF |
| current_price | 当前价格 | 实时价格 |
| signal.signal_type | 信号类型 | buy/sell/hold |
| signal.strength | 信号强度 | 0-100% |
| signal.confidence | 置信度 | 0-100% |
| overall_score | 综合评分 | 0-100分 |

#### 8.1.2 综合评分颜色

| 分数范围 | 颜色 | 含义 |
|----------|------|------|
| ≥ 70分 | 绿色 | 高分，看多 |
| 40-70分 | 黄色 | 中等，观望 |
| < 40分 | 红色 | 低分，看空 |

#### 8.1.3 数据质量指标

| 指标 | 含义 | 评分标准 |
|------|------|----------|
| completeness | 完整性 | 数据是否完整 |
| reliability | 可靠性 | 数据源可信度 |
| recency | 时效性 | 数据新鲜程度 |

### 8.2 技术指标面板 (IndicatorList)

#### 8.2.1 移动平均线区域

```
┌─────────────────────────────────────────┐
│ 移动平均线 (MA)                          │
├─────────────────────────────────────────┤
│ MA5:  1.234    [多头]                    │
│ MA10: 1.230    [多头]                    │
│ MA20: 1.225    [多头]                    │
│ MA60: 1.210    [多头]                    │
└─────────────────────────────────────────┘
```

**信号标签颜色：**
- 绿色（多头）：bullish
- 红色（空头）：bearish
- 灰色（中性）：neutral

#### 8.2.2 RSI区域

```
┌─────────────────────────────────────────┐
│ 相对强弱指标 (RSI)                        │
├─────────────────────────────────────────┤
│ RSI: 45.32    [中性]                     │
│ 正常区域                                  │
└─────────────────────────────────────────┘
```

**RSI解读文字：**
- < 30：超卖区域，可能反弹
- > 70：超买区域，可能回调
- 其他：正常区域

#### 8.2.3 MACD区域

```
┌─────────────────────────────────────────┐
│ 指数平滑异同移动平均线 (MACD)             │
├─────────────────────────────────────────┤
│ MACD(DIF):   0.001234    [多头]          │
│ Signal(DEA): 0.001000    [中性]          │
│ Histogram:   0.000234    [多头]          │
└─────────────────────────────────────────┘
```

#### 8.2.4 KDJ区域

```
┌─────────────────────────────────────────┐
│ 随机指标 (KDJ)                           │
├─────────────────────────────────────────┤
│ K: 45.23    [中性]                       │
│ D: 42.15    [中性]                       │
│ J: 51.39    [中性]                       │
└─────────────────────────────────────────┘
```

#### 8.2.5 布林带区域

```
┌─────────────────────────────────────────┐
│ 布林带 (Bollinger)                       │
├─────────────────────────────────────────┤
│ 上轨: 1.300                              │
│ 中轨: 1.250                              │
│ 下轨: 1.200                              │
└─────────────────────────────────────────┘
```

#### 8.2.6 综合分析区域

```
┌─────────────────────────────────────────┐
│ 综合分析                                 │
├─────────────────────────────────────────┤
│ MA均线系统    1.225    [多头]  权重: 25% │
│ RSI相对强弱   45.32   [中性]  权重: 25% │
│ MACD动能     0.000234 [多头]  权重: 25% │
│ KDJ随机指标   45.23   [中性]  权重: 15% │
│ 布林带        1.250   [中性]  权重: 10% │
└─────────────────────────────────────────┘
```

### 8.3 仓位建议面板 (PositionRecommendation)

#### 8.3.1 操作建议区域

| 字段 | 含义 | 显示 |
|------|------|------|
| action | 操作类型 | 建议加仓/建议减仓/持有不动 |
| amount | 交易金额 | ¥X,XXX |
| reason | 操作理由 | 详细量化依据说明 |

#### 8.3.2 量化依据区域

| 字段 | 含义 | 取值 |
|------|------|------|
| signal_score | 综合得分 | -1.0 ~ +1.0 |
| trend_direction | 趋势方向 | 上涨/下跌/震荡 |
| trend_strength | 趋势强度 | 0% ~ 100% |

**得分颜色：**
- > 0.3：绿色（多头）
- < -0.3：红色（空头）
- 其他：灰色（中性）

#### 8.3.3 核心数据区域

| 字段 | 含义 |
|------|------|
| percentage | 目标仓位比例 |
| current_position | 当前持仓金额 |
| target_position | 目标持仓金额 |
| max_position | 最大持仓金额 |

#### 8.3.4 价格区域

| 字段 | 含义 | 颜色 |
|------|------|------|
| support_level | 支撑位 | 蓝色 |
| stop_loss_price | 止损价 | 红色 |
| take_profit_price | 止盈价 | 绿色 |

#### 8.3.5 仓位进度条

| 进度范围 | 颜色 | 含义 |
|----------|------|------|
| 0-30% | 绿色 | 低仓位 |
| 30-60% | 蓝色 | 中等仓位 |
| 60-80% | 黄色 | 较高仓位 |
| 80-100% | 红色 | 高仓位 |

### 8.4 信号徽章 (SignalBadge)

| 信号类型 | 显示文字 | 颜色 |
|----------|----------|------|
| buy | 买入 | 绿色 |
| sell | 卖出 | 红色 |
| hold | 持有 | 灰色 |

---

## 9. 回测系统

### 9.1 回测流程

```
┌─────────────────────────────────────────────────────────────┐
│                      回测引擎流程                            │
├─────────────────────────────────────────────────────────────┤
│  1. 加载历史数据                                             │
│     ↓                                                       │
│  2. 数据预处理（日期排序、周线转换）                          │
│     ↓                                                       │
│  3. 滑动窗口遍历（120日窗口）                                 │
│     ↓                                                       │
│  4. 生成交易信号                                             │
│     ↓                                                       │
│  5. 执行交易逻辑                                             │
│     ↓                                                       │
│  6. 记录权益曲线                                             │
│     ↓                                                       │
│  7. 计算绩效指标                                             │
└─────────────────────────────────────────────────────────────┘
```

### 9.2 交易逻辑

```python
for each_bar in historical_data:
    # 生成信号
    signal = strategy.generate_signal(window_data, weekly_data, equity)

    # 开仓逻辑
    if signal.type == 'buy' and position == 0:
        position_size = min(signal.position_size, equity)
        if position_size > min_position:
            open_position(position_size, current_price)

    # 平仓逻辑
    if signal.type == 'sell' and position > 0:
        close_position(current_price)

    # 止损检查
    if current_price <= stop_loss:
        close_position(stop_loss)
```

### 9.3 绩效指标

| 指标 | 计算方法 | 含义 |
|------|----------|------|
| total_return | (期末权益 - 期初权益) / 期初权益 | 总收益率 |
| annualized_return | (1 + total_return)^(252/days) - 1 | 年化收益率 |
| max_drawdown | max(峰值 - 当前值) / 峰值 | 最大回撤 |
| sharpe_ratio | (日均收益 / 日收益标准差) × √252 | 夏普比率 |
| win_rate | 盈利交易数 / 总交易数 | 胜率 |
| profit_factor | 总盈利 / 总亏损 | 盈亏比 |
| avg_win | 盈利交易平均盈利 | 平均盈利 |
| avg_loss | 亏损交易平均亏损 | 平均亏损 |

### 9.4 回测响应字段

```typescript
interface BacktestResponse {
  etf_code: string           // ETF代码
  period: string             // 数据周期
  metrics: BacktestMetrics   // 绩效指标
  equity_curve: EquityPoint[] // 权益曲线
  trades: BacktestTrade[]    // 交易记录
  klines: KlineData          // K线数据
  signals: TradeSignal[]     // 交易信号点
  strategy_params: StrategyParams  // 策略参数
  timestamp: string          // 时间戳
}
```

---

## 10. 数据源与数据质量

### 10.1 数据源架构

```
┌─────────────────────────────────────────┐
│         MultiSourceFetcher              │
├─────────────────────────────────────────┤
│  ┌─────────────┐   ┌─────────────┐      │
│  │ SinaDataSrc │ → │ TencentData │      │
│  │  (主数据源)  │   │  (备用源)    │      │
│  └─────────────┘   └─────────────┘      │
│         ↓ 自动故障切换 ↓                 │
│  ┌─────────────────────────────────┐    │
│  │         统一数据格式              │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

### 10.2 支持的数据周期

| 周期 | 代码 | 说明 |
|------|------|------|
| 1分钟 | 1min | 超短线 |
| 5分钟 | 5min | 短线 |
| 15分钟 | 15min | 短线 |
| 30分钟 | 30min | 日内 |
| 60分钟 | 60min | 日内 |
| 日线 | daily | 中短线 |

### 10.3 实时行情数据结构

```python
{
    "code": "512400",
    "name": "有色金属ETF",
    "open": 1.234,
    "prev_close": 1.230,
    "current": 1.235,
    "high": 1.240,
    "low": 1.220,
    "volume": 12345678,
    "amount": 15234567.89,
    "change": 0.005,
    "change_pct": 0.41,
    "bid1": [1.234, 1000],  # [价格, 数量]
    "bid2": [1.233, 2000],
    # ... bid3-5, ask1-5
    "fetch_time": "2026-03-08T10:30:00",
    "source": "sina"
}
```

### 10.4 K线数据结构

```python
{
    "code": "512400",
    "period": "日K",
    "count": 100,
    "klines": [
        {
            "date": "2026-03-08",
            "open": 1.230,
            "high": 1.240,
            "low": 1.220,
            "close": 1.235,
            "volume": 12345678,
            "ma5": 1.228,
            "ma10": 1.225,
            "ma30": 1.220
        },
        # ... more klines
    ],
    "fetch_time": "2026-03-08T10:30:00",
    "source": "sina"
}
```

---

## 11. API接口说明

### 11.1 分析接口

**POST `/api/analyze`**

请求体：
```json
{
    "etf_code": "512400",
    "risk_preference": "neutral",
    "use_cache": true,
    "total_capital": 100000,
    "holding_amount": 50000
}
```

响应体：
```json
{
    "etf_code": "512400",
    "etf_name": "有色金属ETF",
    "current_price": 1.235,
    "signal": {
        "signal_type": "buy",
        "strength": 0.65,
        "confidence": 0.75
    },
    "indicators": {
        "ma5": {"value": 1.228, "signal": "bullish", "interpretation": "..."},
        "rsi": {"value": 45.32, "signal": "neutral", "interpretation": "..."},
        // ...
    },
    "position": {
        "action": "buy",
        "amount": 15000,
        "percentage": 65,
        "stop_loss_price": 1.173,
        "take_profit_price": 1.359,
        // ...
    },
    "overall_score": 0.65,
    "timestamp": "2026-03-08T10:30:00"
}
```

### 11.2 回测接口

**POST `/api/backtest`**

请求体：
```json
{
    "etf_code": "512400",
    "period": "daily",
    "start_date": "2025-01-01",
    "end_date": "2026-03-08",
    "initial_capital": 100000
}
```

响应体：
```json
{
    "etf_code": "512400",
    "metrics": {
        "initial_capital": 100000,
        "final_capital": 125000,
        "total_return": 0.25,
        "annualized_return": 0.18,
        "max_drawdown": -0.12,
        "sharpe_ratio": 1.5,
        "win_rate": 0.65,
        "total_trades": 20
    },
    "equity_curve": [...],
    "trades": [...],
    "signals": [...]
}
```

### 11.3 实时数据接口

**GET `/data/realtime/{code}`**

响应体：
```json
{
    "code": "512400",
    "name": "有色金属ETF",
    "current": 1.235,
    "change": 0.005,
    "change_pct": 0.41,
    // ...
}
```

### 11.4 K线数据接口

**GET `/data/kline/{code}?period=daily&count=100`**

响应体：
```json
{
    "code": "512400",
    "period": "日K",
    "count": 100,
    "klines": [...]
}
```

---

## 附录

### A. 默认参数配置汇总

| 类别 | 参数 | 默认值 |
|------|------|--------|
| **MA** | 周期 | 5, 10, 20, 60 |
| **MACD** | 快线/慢线/信号线 | 12/26/9 |
| **RSI** | 周期 | 14 |
| **Bollinger** | 周期/标准差 | 20/2 |
| **ATR** | 周期 | 14 |
| **Volume** | 均量周期 | 20 |
| **放量阈值** | 比例 | 1.5 |
| **缩量阈值** | 比例 | 0.7 |
| **支撑阻力** | 回看周期 | 20 |
| **Kelly** | 分数系数 | 0.25 |
| **止损** | 固定比例/ATR倍数 | 5%/2.0 |

### B. 风险偏好参数对比表

| 参数 | 保守型 | 中性型 | 激进型 |
|------|--------|--------|--------|
| 单次交易比例 | 10% | 20% | 30% |
| 止损比例 | 3% | 5% | 8% |
| 止盈比例 | 6% | 10% | 16% |
| 单笔最大风险 | 2% | 3% | 5% |
| 买入信号阈值 | 0.7 | 0.5 | 0.3 |
| 卖出信号阈值 | -0.5 | -0.5 | -0.7 |

### C. 市场识别规则

| 代码前缀 | 市场 | 交易所 |
|----------|------|--------|
| 51, 52, 58, 50, 56 | sh | 上海证券交易所 |
| 15, 16, 18, 17, 19 | sz | 深圳证券交易所 |

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2026-03-08 | 初始版本 |

---

**免责声明**：本系统仅供学习和研究使用，不构成任何投资建议。投资有风险，入市需谨慎。

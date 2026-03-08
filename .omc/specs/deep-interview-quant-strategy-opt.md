# Deep Interview Spec: ETF 量化交易策略优化

## Metadata
- Interview ID: quant-opt-001
- Rounds: 11
- Final Ambiguity Score: 12%
- Type: brownfield (现有代码库优化)
- Generated: 2026-03-08
- Threshold: 20%
- Status: PASSED

## Clarity Breakdown
| 维度 | 得分 | 权重 | 加权 |
|------|------|------|------|
| 目标清晰度 | 0.90 | 35% | 0.315 |
| 约束清晰度 | 0.85 | 25% | 0.213 |
| 成功标准 | 0.90 | 25% | 0.225 |
| 上下文清晰度 | 0.85 | 15% | 0.128 |
| **总清晰度** | | | **0.88** |
| **模糊度** | | | **12%** |

## Goal
优化现有 ETF 量化交易系统，实现：
1. **提升收益率**：目标年化 15-25%（理想目标，非硬约束）
2. **降低回撤风险**：目标最大回撤 <10%（理想目标，非硬约束）
3. **保留现有框架**：基于 FastAPI + Vue 3 现有代码，替换策略逻辑 + 新增回测验证页面

## Constraints
- **交易周期**：波段交易 + 趋势跟踪，不做日内短线
- **交易标的**：单一 ETF，不限定具体类型
- **数据来源**：通过现有 API（新浪/腾讯）获取历史数据
- **技术约束**：保留现有 FastAPI 后端 + Vue 3 前端框架
- **简化要求**：删除现有三档风险偏好设定

## Non-Goals
- 不引入机器学习模型（第一阶段）
- 不扩展多 ETF 组合功能
- 不新增数据源（使用现有新浪/腾讯接口）
- 不做日内高频交易

## Acceptance Criteria
- [ ] 实现右侧顺势交易策略模块（MA金叉 + MACD确认 + RSI回升 + 突破放量 + 多周期确认）
- [ ] 实现左侧底部辅助策略模块（布林带+RSI + 支撑位放量止跌 + KDJ超卖金叉 + 缩量止跌）
- [ ] 实现组合止损逻辑（固定比例 + ATR动态 + 技术位）
- [ ] 实现 Kelly 仓位管理算法
- [ ] 实现多周期分析（周线趋势 + 日线入场）
- [ ] 实现量价关系分析（放量/缩量识别，阈值可配置）
- [ ] 实现回测框架（1年历史数据验证）
- [ ] 实现回测页面：关键绩效指标展示
- [ ] 实现回测页面：收益曲线图 + 回撤曲线图
- [ ] 实现回测页面：交易记录列表
- [ ] 实现回测页面：K线图信号标注
- [ ] 删除原有三档风险偏好设定
- [ ] 策略参数用户可配置

## Assumptions Exposed & Resolved
| 假设 | 挑战 | 决议 |
|------|------|------|
| 目标收益和回撤是硬约束 | 逆思模式挑战：15-25%收益 + <10%回撤过于激进 | 明确为理想目标，可根据回测结果调整 |
| 需要完整优化所有策略 | 简化模式挑战：范围是否过大 | 明确保留框架，只替换策略 + 新增回测页面 |
| 需要保留风险偏好档位 | 简化模式挑战：是否增加复杂度 | 删除三档设定，简化系统 |
| 需要网格搜索优化参数 | 用户明确规则化参数优先 | 采用规则化参数 + 用户可配置 + 回测验证 |

## Technical Context

### 现有架构
```
backend/
├── main.py                 # FastAPI 入口
├── models/schemas.py       # Pydantic 数据模型
├── services/
│   ├── fetcher.py         # 数据获取（新浪/腾讯）
│   ├── indicators.py       # 技术指标计算
│   └── signal.py          # 信号生成
└── routers/
    ├── data.py           # 行情数据接口
    └── analysis.py       # 分析接口

frontend/
├── src/
│   ├── views/            # Vue 页面组件
│   ├── components/       # 通用组件
│   └── api/              # API 调用封装
└── package.json
```

### 技术栈
- Backend: FastAPI + Pandas + TA-Lib
- Frontend: Vue 3 + Element Plus + ECharts
- Data: 新浪财经 API（主）、腾讯财经 API（备）

### 需要新增/修改的模块
1. `services/strategy.py` - 新策略逻辑
2. `services/backtest.py` - 回测引擎
3. `services/position.py` - Kelly 仓位管理
4. `services/multi_timeframe.py` - 多周期分析
5. `routers/backtest.py` - 回测 API 接口
6. 前端新增回测页面组件

## Ontology (Key Entities)

### 信号 (Signal)
| 字段 | 类型 | 说明 |
|------|------|------|
| type | enum | 'right_side' \| 'left_side' |
| direction | enum | 'buy' \| 'sell' |
| strength | float | 信号强度 (0-1) |
| indicators | dict | 触发信号的指标值 |
| timestamp | datetime | 信号时间 |
| timeframe | str | 周期 (weekly/daily) |

### 交易记录 (Trade)
| 字段 | 类型 | 说明 |
|------|------|------|
| entry_date | date | 入场日期 |
| exit_date | date | 出场日期 |
| entry_price | float | 入场价格 |
| exit_price | float | 出场价格 |
| position_size | float | 仓位比例 |
| pnl | float | 盈亏金额 |
| pnl_pct | float | 盈亏百分比 |
| entry_signal | Signal | 入场信号 |
| exit_reason | str | 出场原因 |

### 回测结果 (BacktestResult)
| 字段 | 类型 | 说明 |
|------|------|------|
| total_return | float | 总收益率 |
| annual_return | float | 年化收益率 |
| max_drawdown | float | 最大回撤 |
| sharpe_ratio | float | 夏普比率 |
| win_rate | float | 胜率 |
| profit_factor | float | 盈亏比 |
| trades | List[Trade] | 交易记录列表 |
| equity_curve | List[dict] | 资金曲线 |

### 策略配置 (StrategyConfig)
| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| stop_loss_pct | float | 0.08 | 止损比例 |
| take_profit_pct | float | 0.15 | 止盈比例 |
| volume_threshold | float | 1.5 | 放量倍数阈值 |
| kelly_fraction | float | 0.25 | Kelly 系数 |
| ma_short | int | 5 | 短期均线周期 |
| ma_long | int | 20 | 长期均线周期 |
| rsi_oversold | int | 30 | RSI 超卖阈值 |
| rsi_overbought | int | 70 | RSI 超买阈值 |

## Strategy Logic

### 右侧顺势交易 (Right-Side Trend Following)
```
入场条件（需同时满足）：
1. 周线趋势确认
   - 周线 MA5 > MA20（上升趋势）
   - 或周线价格在 MA20 之上

2. 日线入场信号（满足其一）：
   a) 均线金叉：MA5 上穿 MA20
   b) MACD 确认：DIF > DEA 且柱状图扩大
   c) RSI 回升：RSI 从超卖区(<30)回升至 >40
   d) 突破新高+放量：价格突破 20 日新高，成交量 > volume_threshold × 均量

3. 多周期确认：
   - 大周期回踩支撑位
   - 小周期出现止跌信号
```

### 左侧底部辅助 (Left-Side Bottom Fishing)
```
入场条件（满足组合其一）：
1. 布林带+RSI 组合：
   - 价格触及或跌破布林带下轨
   - RSI < 30（超卖）

2. 支撑位+放量止跌：
   - 价格触及支撑位（前低/MA60）
   - 成交量放大且价格止跌

3. KDJ 超卖金叉：
   - J < 20
   - K 线上穿 D 线

4. 缩量止跌信号：
   - 连续下跌后成交量显著萎缩
   - 价格出现止跌形态
```

### 组合止损逻辑
```
止损价格 = max(
    入场价 × (1 - stop_loss_pct),           // 固定比例止损
    入场价 - 2 × ATR(14),                   // ATR 动态止损
    支撑位价格                               // 技术位止损
)
```

### Kelly 仓位管理
```
仓位比例 = min(
    Kelly_fraction × (胜率 - (1-胜率)/盈亏比),  // Kelly 公式
    最大仓位上限 0.95
)

注：简化实现，可使用固定 Kelly_fraction 参数
```

## Interview Transcript
<details>
<summary>完整问答记录 (11 轮)</summary>

### Round 1
**Q:** 你说「优化量化交易策略」，具体想优化哪个方面？
**A:** 提升收益率, 降低回撤风险
**Ambiguity:** 75% (Goal: 0.4, Constraints: 0.2, Criteria: 0.2, Context: 0.5)

### Round 2
**Q:** 要提升收益率、降低回撤，你希望从哪个切入点开始？
**A:** 综合优化 (推荐)
**Ambiguity:** 65%

### Round 3
**Q:** 你的交易周期是什么？你的系统主要交易哪些标的？
**A:** 波段交易和趋势跟踪，不做日内短线；单一 ETF
**Ambiguity:** 55%

### Round 4
**Q:** 年化 15-25% + 回撤 <10% 是一个较激进的组合。如果回测显示这个目标难以同时达成，你会优先保证哪个？
**A:** 理想目标非硬约束
**Ambiguity:** 45%

### Round 5
**Q:** 回测需要历史数据。你的历史 K 线数据从哪里来？你目前有这些策略的历史表现基线吗？
**A:** 通过现有 API 获取；无基线
**Ambiguity:** 40%

### Round 6
**Q:** 为避免范围过大，你希望第一阶段的交付范围是什么？
**A:** 已经有前后端基本框架了，只需要替换现有的策略，另外多一个策略回测验证的页面，用来调整策略
**Notes:** 我希望先跟我确定策略的方案细节，再写代码实现
**Ambiguity:** 35%

### Round 7
**Q:** 关于策略方案，你希望采用什么方向？参数优化你希望采用什么方式？
**A:** 优化现有指标策略，需要结合量价关系，以右侧顺势交易为主，搭配左侧底细动作辅助；基于规则化参数，同时有些配置可以由用户更改，通过回测来验证收益率
**Ambiguity:** 28%

### Round 8
**Q:** 右侧顺势交易的入场信号，你希望使用哪些组合？左侧底部辅助的入场信号，你希望使用哪些组合？止损逻辑你希望怎么设计？
**A:** 右侧: 均线金叉, MACD 动量确认, RSI 回升确认, 突破新高+放量, 诸如大周期回踩，小周期站稳; 左侧: 布林带+RSI 组合, 支撑位+放量止跌, KDJ 超卖金叉, 缩量止跌信号; 止损: 组合止损逻辑
**Ambiguity:** 22%

### Round 9
**Q:** 止盈/退出逻辑你希望怎么设计？仓位管理策略你希望采用什么方式？你提到「大周期回踩，小周期站稳」，周期组合是怎么设计的？
**A:** 止盈: 固定比例止盈; 仓位: 风险平价 (Kelly); 周期: 周线+日线
**Ambiguity:** 18%

### Round 10
**Q:** 回测默认使用多长时间的历史数据？现有系统有三档风险偏好，它们如何影响策略？「放量」的量化定义是什么？
**A:** 回测1年历史；删除三档风险偏好的设定；可配置阈值
**Ambiguity:** 15%

### Round 11
**Q:** 回测页面需要展示哪些信息？
**A:** 关键绩效指标, 收益曲线图, 交易记录列表, 信号标注图表
**Ambiguity:** 12%

</details>

## Next Steps
选择执行模式后，将进入详细实现规划：
1. 设计策略模块接口
2. 实现回测引擎
3. 实现前端回测页面
4. 集成测试与验证

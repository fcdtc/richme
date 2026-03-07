# ETF量化交易计算器 - 实现计划

## Plan Summary

**Plan ID:** etf-quant-calculator-002
**Created:** 2026-03-07
**Revised:** 2026-03-07 (根据 Critic 和 Architect 反馈修订)
**Scope:** Brownfield - 基于现有 `fetch_etf_data.py` 扩展
**Estimated Complexity:** MEDIUM

---

## 1. RALPLAN-DR Summary

### Principles (3-5)

1. **渐进式构建** - 复用现有数据获取模块，增量添加分析和Web层
2. **策略可配置** - 指标参数和风险偏好调整逻辑易于调整
3. **数据驱动** - 基于多数据源（新浪+腾讯）实时数据，确保分析时效性
4. **用户友好** - Web界面简洁直观，分析过程透明可追溯
5. **防御性设计** - 数据源、依赖库均有回退方案

### Decision Drivers (Top 3)

1. **快速可用** - 用户需要尽快获得可用的交易计算工具
2. **技术指标准确性** - MACD、RSI、布林带等指标计算必须正确
3. **本地运行** - 无需云部署，降低使用门槛

### Viable Options

#### Option A: Vue.js 3 + FastAPI (推荐)

**优点:**
- Vue 3 组合式 API 适合复杂的表单和状态管理
- Element Plus/Naive UI 提供丰富的金融组件
- FastAPI + Uvicorn 本地启动简单
- Python 生态适合数值计算
- 前后端分离便于独立测试和部署

**缺点:**
- 需要学习 Vue.js（如果用户不熟悉）
- 前后端需要分别开发
- 对于简单工具可能存在过度工程化风险

**技术栈:**
- 后端: Python 3.12 + FastAPI + Uvicorn
- 前端: Vue 3 + TypeScript + Vite + Element Plus
- 数据计算: pandas + numpy

#### Option B: Streamlit + FastAPI

**优点:**
- 纯 Python 开发，无需前端技能
- 开发速度极快，适合快速原型
- 内置数据可视化组件

**缺点:**
- UI 定制能力有限
- 复杂交互实现困难
- 状态管理较弱
- 性能不如原生前端

**技术栈:**
- 后端: Python 3.12 + FastAPI + Uvicorn
- 前端: Streamlit
- 数据计算: pandas + numpy

#### Option C: React + FastAPI

**优点:**
- React 生态更成熟，组件库丰富（Ant Design）
- 社区活跃，问题容易找到解决方案
- TypeScript 支持完善

**缺点:**
- 配置相对复杂
- JSX 语法对某些开发者不直观

**技术栈:**
- 后端: Python 3.12 + FastAPI + Uvicorn
- 前端: React + TypeScript + Vite + Ant Design
- 数据计算: pandas + numpy

**选择 Option A 的理由:**
- Vue 3 的响应式系统更适合数据驱动的量化应用
- Element Plus 的表格和图表组件开箱即用
- 学习曲线更平缓，上手更快
- 前后端分离便于未来扩展（如添加认证、历史记录）

**其他选项的无效化理由:**
- Option B (Streamlit) 被排除：工具需要展示多个指标、K线图、信号徽章等复杂布局，Streamlit 的定制能力不足以支持良好的用户体验
- Option C (React) 被排除：与 Vue 相比，React 的学习曲线更陡峭，对于此项目的需求 Vue 已足够

---

## 2. 文件结构

```
richme/
├── fetch_etf_data.py           # 已存在：数据获取脚本
├── data/                       # 已存在：数据存储
├── config/
│   ├── __init__.py
│   └── settings.py             # 配置管理系统
├── backend/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── requirements.txt        # 后端依赖
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic 数据模型
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── analysis.py         # 分析接口
│   │   └── data.py             # 数据接口
│   └── services/
│       ├── __init__.py
│       ├── fetcher.py          # 数据源抽象层（新浪+腾讯）
│       ├── indicators.py       # 技术指标计算（含布林带）
│       └── signal.py           # 信号生成逻辑
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── components/
│   │   │   ├── InputForm.vue   # 输入表单
│   │   │   ├── ResultCard.vue  # 结果展示
│   │   │   ├── IndicatorList.vue # 指标列表
│   │   │   └── SignalBadge.vue # 信号徽章
│   │   ├── services/
│   │   │   └── api.ts          # API 调用
│   │   ├── types/
│   │   │   └── index.ts        # TypeScript 类型
│   │   └── assets/
│   └── package-lock.json
├── tests/
│   ├── unit/
│   │   ├── test_indicators.py
│   │   ├── test_signal.py
│   │   └── test_fetcher.py
│   └── integration/
│       └── test_api.py
└── README.md                   # 更新后的使用说明
```

---

## 3. 实现步骤

### Step 1: 后端基础架构搭建

**任务描述:**
- 创建 FastAPI 应用骨架
- 实现配置管理系统（基于 Pydantic Settings）
- 封装现有 `fetch_etf_data.py` 为服务模块
- 定义 Pydantic 数据模型
- 实现前后端类型同步机制

**涉及文件:**
- `backend/main.py` (新建)
- `backend/requirements.txt` (新建)
- `config/settings.py` (新建)
- `backend/models/schemas.py` (新建)
- `backend/services/fetcher.py` (新建)
- `backend/__init__.py` (新建)
- `backend/models/__init__.py` (新建)
- `backend/services/__init__.py` (新建)
- `frontend/src/types/index.ts` (新建)
- `scripts/generate_types.py` (新建 - 类型同步脚本)

**依赖关系:**
- 无（独立步骤）

**验收标准:**
- `uvicorn backend.main:app --reload` 能启动服务
- 访问 `http://localhost:8000/docs` 看到 Swagger 文档
- `/data/realtime/{code}` 接口返回实时行情数据
- 配置管理系统支持环境变量和配置文件
- 运行 `python scripts/generate_types.py` 可生成 TypeScript 类型文件

**类型同步方案:**
```python
# scripts/generate_types.py
# 从 Pydantic 模型自动生成 TypeScript 类型定义
from backend.models.schemas import *
# 生成 frontend/src/types/index.ts
```

---

### Step 2: 技术指标计算模块

**任务描述:**
- 实现均线交叉策略（MA5/MA10/MA30）
- 实现 MACD 指标计算
- 实现 RSI 指标计算
- 实现布林带计算（合并到 indicators.py）
- 实现 talib 依赖的优雅降级

**涉及文件:**
- `backend/services/indicators.py` (新建)
- `backend/requirements.txt` (更新)
- `tests/unit/test_indicators.py` (新建)

**依赖关系:**
- 依赖 Step 1 的数据模型

**talib 依赖风险缓解策略:**

1. **优先使用 talib:**
```python
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
```

2. **pandas/numpy 实现回退方案:**

```python
# MACD 回退实现
def calculate_macd(series: pd.Series, fast=12, slow=26, signal=9) -> dict:
    if TALIB_AVAILABLE:
        return _macd_talib(series, fast, slow, signal)
    return _macd_pandas(series, fast, slow, signal)

def _macd_pandas(series: pd.Series, fast, slow, signal) -> dict:
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

# RSI 回退实现
def calculate_rsi(series: pd.Series, period=14) -> float:
    if TALIB_AVAILABLE:
        return _rsi_talib(series, period)
    return _rsi_pandas(series, period)

def _rsi_pandas(series: pd.Series, period) -> float:
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0

# 布林带回退实现
def calculate_bollinger(series: pd.Series, period=20, std_dev=2) -> dict:
    if TALIB_AVAILABLE:
        return _bollinger_talib(series, period, std_dev)
    return _bollinger_pandas(series, period, std_dev)

def _bollinger_pandas(series: pd.Series, period, std_dev) -> dict:
    middle = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    return {
        'upper': upper.iloc[-1],
        'middle': middle.iloc[-1],
        'lower': lower.iloc[-1]
    }
```

3. **在 requirements.txt 中添加 talib 为可选依赖:**
```
TA-Lib>=0.4.28  # 可选，安装失败时回退到 pandas 实现
```

**验收标准:**
- MACD: DIF、DEA、柱状图值正确
- RSI: 14 日 RSI 值在 0-100 之间
- 布林带: 上轨、中轨、下轨值合理
- 无 talib 时程序能正常运行并使用 pandas 实现
- 所有指标函数有单元测试，测试覆盖率 > 80%

---

### Step 3: 数据源抽象层

**任务描述:**
- 实现数据源抽象接口
- 集成新浪财经数据源
- 集成腾讯财经数据源作为备用
- 实现自动故障切换机制

**涉及文件:**
- `backend/services/fetcher.py` (更新)
- `config/settings.py` (更新)

**依赖关系:**
- 依赖 Step 1 的配置管理系统

**数据源抽象设计:**

```python
from abc import ABC, abstractmethod
from typing import Optional
import requests

class DataSource(ABC):
    """数据源抽象基类"""

    @abstractmethod
    def fetch_realtime(self, code: str) -> Optional[dict]:
        """获取实时行情"""
        pass

    @abstractmethod
    def fetch_kline(self, code: str, period: str = 'daily', count: int = 100) -> Optional[list]:
        """获取K线数据"""
        pass

class SinaDataSource(DataSource):
    """新浪财经数据源"""

    def fetch_realtime(self, code: str) -> Optional[dict]:
        url = f"http://hq.sinajs.cn/list={code}"
        try:
            resp = requests.get(url, timeout=5)
            # 解析逻辑...
        except Exception as e:
            logger.warning(f"新浪数据源获取失败: {e}")
            return None

    def fetch_kline(self, code: str, period: str = 'daily', count: int = 100) -> Optional[list]:
        # 实现逻辑...
        pass

class TencentDataSource(DataSource):
    """腾讯财经数据源（备用）"""

    def fetch_realtime(self, code: str) -> Optional[dict]:
        url = f"http://qt.gtimg.cn/q={code}"
        try:
            resp = requests.get(url, timeout=5)
            # 解析逻辑...
        except Exception as e:
            logger.warning(f"腾讯数据源获取失败: {e}")
            return None

    def fetch_kline(self, code: str, period: str = 'daily', count: int = 100) -> Optional[list]:
        # 实现逻辑...
        pass

class MultiSourceFetcher:
    """多数据源聚合器，支持自动故障切换"""

    def __init__(self, sources: list[DataSource]):
        self.sources = sources

    def fetch_realtime(self, code: str) -> dict:
        for i, source in enumerate(self.sources):
            result = source.fetch_realtime(code)
            if result is not None:
                if i > 0:
                    logger.info(f"使用备用数据源 {source.__class__.__name__}")
                return result
        raise RuntimeError("所有数据源均不可用")

    def fetch_kline(self, code: str, period: str = 'daily', count: int = 100) -> list:
        for i, source in enumerate(self.sources):
            result = source.fetch_kline(code, period, count)
            if result is not None:
                if i > 0:
                    logger.info(f"使用备用数据源 {source.__class__.__name__}")
                return result
        raise RuntimeError("所有数据源均不可用")
```

**验收标准:**
- 新浪数据源正常时使用新浪
- 新浪数据源失败时自动切换到腾讯
- 切换过程有日志记录
- 所有数据源均失败时抛出明确异常

---

### Step 4: 信号生成逻辑

**任务描述:**
- 实现基于指标组合的信号生成
- 实现风险偏好权重调整
- 定义 5 种信号级别（强烈买入/买入/持有/卖出/强烈卖出）

**涉及文件:**
- `backend/services/signal.py` (新建)

**依赖关系:**
- 依赖 Step 2 的指标模块

**验收标准:**
- 各策略独立评分正确
- 风险偏好影响信号阈值
- 生成包含详细分析过程的 JSON
- 信号生成逻辑有单元测试覆盖

---

### Step 5: 分析 API 接口

**任务描述:**
- 创建 `/api/analyze` 接口
- 整合数据获取、指标计算、信号生成
- 返回完整的分析结果

**涉及文件:**
- `backend/routers/analysis.py` (新建)
- `backend/routers/data.py` (新建)
- `backend/main.py` (更新)

**依赖关系:**
- 依赖 Step 1, 2, 3, 4

**验收标准:**
- POST 请求接收用户输入参数
- 返回包含交易建议、指标值、分析过程的完整响应
- 接口响应时间 < 3 秒
- API 有集成测试覆盖

---

### Step 6: 前端项目初始化

**任务描述:**
- 创建 Vue 3 + Vite 项目
- 配置 TypeScript 和 Element Plus
- 创建基础组件结构
- 同步后端类型定义

**涉及文件:**
- `frontend/package.json` (新建)
- `frontend/vite.config.ts` (新建)
- `frontend/tsconfig.json` (新建)
- `frontend/index.html` (新建)
- `frontend/src/main.ts` (新建)
- `frontend/src/App.vue` (新建)
- `frontend/src/services/api.ts` (新建)
- `frontend/src/types/index.ts` (新建)
- `frontend/src/components/*.vue` (新建)

**依赖关系:**
- 无（独立步骤，可与后端并行）

**验收标准:**
- `npm run dev` 能启动前端
- 访问 `http://localhost:5173` 显示基础页面
- TypeScript 类型检查通过（`npm run type-check`）
- 前端类型定义与后端 Pydantic 模型一致

---

### Step 7: 前端功能实现

**任务描述:**
- 实现输入表单（ETF代码、资金、持仓、收益率、风险偏好）
- 实现结果展示卡片（交易建议、指标分析）
- 实现图表可视化（K线图、指标图）

**涉及文件:**
- `frontend/src/components/InputForm.vue`
- `frontend/src/components/ResultCard.vue`
- `frontend/src/components/IndicatorList.vue`
- `frontend/src/components/SignalBadge.vue`
- `frontend/src/App.vue` (更新)
- `frontend/package.json` (更新，添加 echarts)

**依赖关系:**
- 依赖 Step 5 的后端 API
- 依赖 Step 1 生成的类型定义

**验收标准:**
- 表单输入验证正确
- 调用 API 显示分析结果
- 交易信号用颜色区分（绿=买入，红=卖出，灰=持有）
- 显示各指标当前值和解读
- K线图和指标图正确渲染

---

### Step 8: 测试与优化

**任务描述:**
- 编写后端单元测试
- 编写 API 集成测试
- 前端交互测试
- 性能优化

**涉及文件:**
- `tests/unit/test_indicators.py` (新建)
- `tests/unit/test_signal.py` (新建)
- `tests/unit/test_fetcher.py` (新建)
- `tests/integration/test_api.py` (新建)
- `frontend/src/__tests__/` (新建)

**依赖关系:**
- 依赖 Step 2, 3, 4, 5, 7

**验收标准:**
- 所有单元测试通过
- API 集成测试通过
- 前端无控制台错误
- 单元测试覆盖率 > 80%
- API 响应时间 < 3 秒

---

## 4. 测试计划

### 单元测试

| 模块 | 测试内容 | 工具 | 具体测试用例 |
|------|----------|------|-------------|
| indicators.py | MA/MACD/RSI/布林带计算正确性 | pytest | - MACD计算：验证与talib结果一致<br>- MACD降级：验证pandas实现与talib差异<1%<br>- RSI计算：验证14日RSI范围0-100<br>- 布林带：验证上下轨与中轨关系<br>- 边界情况：空序列、单元素序列 |
| signal.py | 各策略评分逻辑 | pytest | - MA交叉：金叉验证买入信号<br>- MA交叉：死叉验证卖出信号<br>- MACD：DIF上穿DEA验证<br>- RSI：超买(>70)卖出信号<br>- RSI：超卖(<30)买入信号<br>- 风险偏好：保守/激进阈值差异 |
| fetcher.py | 数据解析正确性 | pytest | - 新浪数据源：正常响应解析<br>- 新浪数据源：超时处理<br>- 腾讯数据源：正常响应解析<br>- 故障切换：主源失败时切换备用 |
| config/settings.py | 配置加载 | pytest | - 环境变量加载<br>- 配置文件加载<br>- 默认值回退 |

### 集成测试

| 接口 | 测试场景 | 预期结果 |
|------|----------|----------|
| POST /api/analyze | 正常输入（512400，100000，20000，5.5，中性） | 返回完整分析结果，状态码200 |
| POST /api/analyze | 无效ETF代码 | 返回错误信息，状态码400 |
| POST /api/analyze | 极端参数值（资金0，风险偏好极端） | 正常处理，状态码200 |
| GET /data/realtime/512400 | 正常ETF代码 | 返回实时行情数据 |
| GET /data/realtime/999999 | 不存在ETF代码 | 返回404或错误提示 |
| 数据源切换测试 | 模拟新浪失败，腾讯正常 | 自动切换到腾讯并返回数据 |
| 数据源全失败测试 | 模拟所有数据源失败 | 返回503错误，明确提示 |

### 端到端测试

1. 启动后端和前端服务
2. 用户输入：ETF代码=512400，总资金=100000，持仓=20000，收益率=5.5，风险偏好=中性
3. 点击"分析"
4. 验证：显示交易建议 + 指标详情 + 分析过程 + K线图

### 手动测试用例

| 场景 | 输入 | 预期输出 |
|------|------|----------|
| 多头趋势 | 上升趋势ETF | 买入信号 |
| 空头趋势 | 下跌趋势ETF | 卖出信号 |
| 震荡市 | 横盘震荡ETF | 持有信号 |
| 保守偏好 | 风险较大ETF | 卖出/持有 |
| 激进偏好 | 波动较大ETF | 可能买入 |
| 数据源切换 | 新浪接口限流 | 自动使用腾讯数据源 |
| talib缺失 | 无talib环境 | 使用pandas实现，功能正常 |

---

## 5. 风险点与解决方案

### 技术风险

| 风险 | 影响 | 具体解决方案 |
|------|------|--------------|
| 新浪接口限流 | 无法获取实时数据 | 1. 实现腾讯财经备用数据源<br>2. 添加本地缓存（Redis/文件）<br>3. 缓存有效期5分钟 |
| 新浪接口停止服务 | 完全无法获取数据 | 1. 腾讯作为主要备用<br>2. 支持手动导入CSV数据<br>3. 考虑接入东方财富等第三源 |
| 指标计算错误 | 交易信号不准确 | 1. 优先使用talib保证准确性<br>2. pandas实现时进行交叉验证<br>3. 单元测试覆盖率>80%<br>4. 与公开数据对比验证 |
| MACD/RSI 计算复杂 | 开发时间延长 | 1. 优先实现核心指标（MA、MACD、RSI）<br>2. 布林带合并到indicators模块<br>3. 其他指标（KDJ、CCI）后续迭代 |
| 前后端数据不一致 | 显示错误 | 1. 自动生成TypeScript类型<br>2. 后端Pydantic严格校验<br>3. 添加运行时类型检查 |
| talib安装困难 | 指标计算模块无法开发 | 1. 提供详细的talib安装文档<br>2. Windows用户提供预编译wheel<br>3. 提供pandas降级实现<br>4. 在启动时检测并提示用户 |
| pandas版本兼容 | 环境配置失败 | 1. requirements.txt锁定版本<br>2. 提供虚拟环境配置脚本<br>3. Docker容器化部署选项 |

### 业务风险

| 风险 | 影响 | 具体解决方案 |
|------|------|--------------|
| 信号不准确 | 用户损失 | 1. 页面顶部显眼免责声明<br>2. 标注"仅供参考，不构成投资建议"<br>3. 建议用户结合多源信息判断 |
| 风险偏好量化困难 | 信号不匹配 | 1. 提供可调参数表（保守/中性/激进）<br>2. 显示当前参数值供用户查看<br>3. 收集反馈后持续优化 |
| 用户过度依赖 | 实际损失 | 1. 明确说明计算器性质<br>2. 不承诺收益<br>3. 建议风险控制仓位管理 |

### 依赖风险

| 风险 | 影响 | 具体解决方案 |
|------|------|--------------|
| talib安装困难 | 指标计算模块无法开发 | 1. 实现完整的pandas降级方案<br>2. 提供安装失败时的fallback<br>3. 文档说明两种模式的差异 |
| Element Plus组件不满足需求 | 开发时间增加 | 1. 评估组件库差异，选择最合适的<br>2. 需要时使用原生HTML/CSS定制<br>3. 考虑Naive UI作为备选 |
| pandas版本兼容 | 环境配置失败 | 1. requirements.txt锁定pandas==2.1.3<br>2. numpy==1.26.2<br>3. 提供requirements-dev.txt用于开发 |

### 架构风险

| 风险 | 影响 | 具体解决方案 |
|------|------|--------------|
| 前后端类型不同步 | 运行时错误 | 1. 自动生成TypeScript类型脚本<br>2. CI/CD中添加类型一致性检查<br>3. API响应添加schema验证 |
| Vue.js过度工程化 | 维护成本高 | 1. 保持组件简洁，避免过度抽象<br>2. 优先使用Element Plus现成组件<br>3. 未来考虑迁移到Streamlit如果需求简单化 |

---

## 6. ADR (Architecture Decision Record)

### Decision

采用 **Vue.js 3 + FastAPI** 技术栈实现 ETF量化交易计算器

### Drivers

1. 用户需要快速可用的本地运行工具
2. Python 生态适合数值计算和金融分析
3. 前端需要良好的数据展示和交互体验
4. 工具需要展示多个指标、K线图、信号徽章等复杂布局

### Alternatives Considered

#### 1. Streamlit + FastAPI

**优点:**
- 纯 Python 开发，无需前端技能
- 开发速度极快，适合快速原型
- 内置数据可视化组件

**缺点:**
- UI 定制能力有限，难以实现复杂布局
- 复杂交互实现困难（如动态表单、状态联动）
- 状态管理较弱
- 性能不如原生前端

**成本-效益分析:**

| 维度 | Streamlit | Vue.js + FastAPI |
|------|-----------|------------------|
| 初期开发时间 | 1-2周 | 2-3周 |
| 学习曲线 | 平缓（仅Python） | 需学习Vue/TS |
| UI定制能力 | 低 | 高 |
| 复杂交互支持 | 弱 | 强 |
| 性能 | 中等 | 高 |
| 维护成本 | 低（纯Python） | 中等（前后端） |
| 未来扩展性 | 有限 | 良好 |
| **适合当前需求?** | **否** | **是** |

**结论:** Streamlit 虽然开发速度快，但无法满足当前项目对复杂布局和良好交互体验的需求。因此不采用。

#### 2. React + FastAPI

**优点:**
- React 生态更成熟，社区资源丰富
- Ant Design 等组件库功能完善
- TypeScript 支持成熟

**缺点:**
- 配置相对复杂（Babel、Webpack等）
- JSX 语法对某些开发者不直观
- 学习曲线较陡峭

**成本-效益分析:**

| 维度 | React | Vue.js |
|------|-------|--------|
| 初期开发时间 | 3-4周 | 2-3周 |
| 学习曲线 | 陡峭 | 平缓 |
| 生态成熟度 | 非常成熟 | 成熟 |
| 组件库 | Ant Design等 | Element Plus等 |
| 响应式系统 | 需额外工具 | 内置 |
| 开发效率 | 中等 | 高 |
| **适合当前需求?** | **备选** | **是** |

**结论:** React 功能强大但学习曲线较陡，对于当前项目的需求，Vue.js 已足够且效率更高。因此作为备选方案。

#### 3. Vue.js 3 + FastAPI (选择)

**优点:**
- Vue 3 组合式 API 代码组织更清晰
- 响应式系统内置，适合数据驱动应用
- Element Plus 提供丰富的金融组件
- 学习曲线相对平缓
- 前后端分离便于独立开发和测试
- 良好的 TypeScript 支持

**缺点:**
- 需要前后端分别开发
- 生态规模略小于 React

**结论:** 采用

### Why Chosen

1. **技术匹配度高:** Vue 3 的响应式系统非常适合量化应用的数据流管理
2. **组件丰富:** Element Plus 提供的表格、图表、表单组件可以直接使用
3. **开发效率:** 相比 React，Vue 的学习曲线更平缓，上手更快
4. **满足需求:** 能够实现项目需要的复杂布局和良好交互体验
5. **可扩展性:** 前后端分离便于未来添加用户认证、历史记录等功能

### Consequences

- **开发周期:** 约 2-3 周完成 MVP
- **维护成本:** 中等，需要前后端技能
- **扩展性:** 良好，模块化设计便于添加新指标和策略
- **用户体验:** 良好，界面美观，交互流畅

### Follow-ups

1. MVP完成后评估是否需要简化架构（如果实际使用发现功能简单）
2. 评估是否需要添加用户登录和历史记录功能
3. 考虑添加更多技术指标（KDJ、CCI 等）
4. 评估移动端适配需求

---

## 7. 成功标准

- [ ] 后端 API 正常响应 `/api/analyze` 请求
- [ ] 前端表单能接收用户输入
- [ ] 能获取实时行情和K线数据（支持数据源自动切换）
- [ ] 正确计算 MA、MACD、RSI、布林带指标
- [ ] 无 talib 时使用 pandas 实现正常工作
- [ ] 基于策略组合生成交易信号
- [ ] 显示详细的指标分析过程
- [ ] 风险偏好能影响信号阈值
- [ ] Web界面美观，数据可视化清晰
- [ ] 本地启动后可通过浏览器访问
- [ ] 响应时间 < 3 秒
- [ ] 前后端类型定义自动同步
- [ ] 单元测试覆盖率 > 80%
- [ ] API 集成测试通过
- [ ] 所有配置项可通过配置文件或环境变量调整

---

## 8. 开发顺序建议

**优先级 P0（核心功能）:**
1. Step 1: 后端基础架构（含配置管理、类型同步）
2. Step 3: 数据源抽象层（新浪+腾讯）
3. Step 2: 技术指标计算（含talib降级）
4. Step 4: 信号生成逻辑
5. Step 5: 分析 API 接口
6. Step 6: 前端项目初始化
7. Step 7: 前端功能实现

**优先级 P1（质量保证）:**
8. Step 8: 测试与优化
9. 图表可视化增强
10. 性能优化

**优先级 P2（扩展）:**
11. 更多技术指标支持
12. 历史分析记录
13. 移动端适配
14. 多ETF对比分析

---

## 附录

### 需安装的后端依赖

```
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
pandas==2.1.3
numpy==1.26.2
TA-Lib>=0.4.28  # 可选，安装失败时回退到 pandas 实现
requests==2.31.0
pytest==7.4.3
pytest-cov==4.1.0
```

### 需安装的前端依赖

```
vue@^3.3.0
typescript@^5.3.0
vite@^5.0.0
element-plus@^2.4.0
axios@^1.6.0
echarts@^5.4.0
@types/node@^20.0.0
```

### 启动命令

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

# 类型同步（更新后端模型后运行）
python ../scripts/generate_types.py

# 前端
cd frontend
npm install
npm run dev

# 类型检查
npm run type-check
```

### 配置文件示例 (config/settings.py)

```python
from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    # 数据源配置
    primary_data_source: str = "sina"  # sina | tencent
    enable_data_cache: bool = True
    cache_ttl_seconds: int = 300

    # 指标配置
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    rsi_period: int = 14
    bollinger_period: int = 20
    bollinger_std: int = 2

    # 风险偏好阈值
    conservative_buy_threshold: float = 0.7
    conservative_sell_threshold: float = -0.7
    aggressive_buy_threshold: float = 0.5
    aggressive_sell_threshold: float = -0.5

    # API 配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    class Config:
        env_file = ".env"

settings = Settings()
```

---
name: jw-investment-data
description: "投资数据获取层 v3.10：综合财务画像(18源)+资金流向+5年多维财务+公司概况+7引擎行情+技术指标+宏观全景。触发：'查行情'、'看财报'、'获取财务数据'、'A股数据'、'宏观数据'、'帮我拉取XX数据'、'技术指标'、'资金流向'。全链路覆盖公司分析88%+量化数据。"
---

# jw-investment-data v3.10.0

投资数据获取层——宏观全景、A股行情/财务/K线/技术指标，多源交叉验证，本地缓存。

## 依赖

```
pip install akshare adata efinance baostock yfinance pandas matplotlib --break-system-packages -i https://pypi.tuna.tsinghua.edu.cn/simple
```

⚠️ 系统无 pip（PEP 668）时加 `--break-system-packages`。超时换清华镜像。完整依赖列表：akshare, adata, baostock, efinance, yfinance, pandas, matplotlib, numpy, requests。

## 快速上手

```bash
cd ~/.hermes/skills/rancbos-skills/jw-investment-data/scripts

# 统一入口（推荐）
./jw-data macro all                # 宏观全景
./jw-data macro cpi                # CPI
./jw-data macro money              # M2+LPR+利率
./jw-data quote 600519             # A股实时行情
./jw-data kline 600519 120         # K线
./jw-data indicators 600519        # 技术指标
./jw-data chart 600519             # K线图PNG
./jw-data health                   # 全源健康检查

# 或者直接用脚本
python fetch_macro.py --category all --format markdown
python fetch_market_data.py --category quote --symbol 600519
python fetch_market_data.py --category financial --symbol 600519                # 5年多维财务
python fetch_market_data.py --category profile --symbol 600519                  # 公司概况
python fetch_market_data.py --category comprehensive --symbol 600519            # 综合财务画像（⭐推荐）
python fetch_market_data.py --category capital_flow --symbol 600519             # 资金流向
```

## 脚本清单

| 脚本 | 用途 | 输出 |
|:---|:---|:---|
| **jw-data** | 统一入口（推荐） | 路由到各脚本 |
| **fetch_macro.py** | 宏观数据采集 | JSON/Markdown |
| **fetch_market_data.py** | A股/期货/港股/外汇报价+K线+财报 | 标准信封 |
| **technical_indicators.py** | MA/MACD/RSI/KDJ/布林带 | JSON/Markdown |
| **draw_kline.py** | K线图+指标叠加 | PNG |
| **health_check.py** | 全源健康检查 | JSON/Markdown |
| **format_macro.py** | 宏观 Markdown 渲染 | — |
| **format_market.py** | 行情 Markdown 渲染 | — |
| **circuit_breaker.py** | 熔断器（内部模块） | — |
| **market_clock.py** | 交易时钟（内部模块） | — |
| **output_contract.py** | 标准信封（内部模块） | — |

## 宏观数据 (fetch_macro.py)

### 支持指标

| `--category` | 覆盖指标 | 数据源 |
|:---|:---|:---|
| `all` | 全部 | 所有源 |
| `growth` | GDP + PMI | 东方财富 |
| `inflation` | CPI + PPI | 东方财富 |
| `money` | M0/M1/M2 + LPR + 利率 + 准备金 | Baostock + 中国货币网 |
| `cpi` / `ppi` / `pmi` / `gdp` | 单一指标 | 东方财富 |
| `invest` | 固定资产投资（累计/同比） | 东方财富 |
| `industrial` | 工业增加值（当月/累计同比） | 东方财富 |
| `fiscal` | 财政收入（累计/同比） | 东方财富 |
| `real_activity` | 固投+工业+财政（批量） | 东方财富 |
| `lpr` | LPR 1Y/5Y | 中国货币网 |
| `rates` | 存/贷款利率 | Baostock |
| `reserve` | 准备金率 | Baostock |
| `calendar` | 经济日历提醒 | Jin10 MCP (Agent侧实时) |

### 交叉验证

- **M2**: Baostock vs 东方财富 `RPT_ECONOMY_MONEY`，差异≤3% → ✅ 通过；>3% → ⚠️ 标注
- **CPI/PMI/GDP/PPI**: 东方财富脚本获取 + Agent 侧用 `mcp_jin10_list_calendar()` 获取预期值/前值交叉验证
- **固投/工业增加值/财政收入**: 东方财富脚本获取（单源）
- **社融/外汇储备**: Agent 侧用 `mcp_jin10_search_flash("社融")` 获取快讯，与 web search 数据交叉验证
- 验证结果写入 `_verifications` 段，Markdown 输出含完整交叉验证表

### 输出格式

```
JSON (默认):  {ok: true, source: "...", data: {...}, ts: ..., meta: {latency_ms, version, errors}}
Markdown:    人读全景报告（9段）→ 增长/通胀/货币/利率/准备金/日历/全球/美国/验证
```

### 缓存

- 目录: `~/.hermes/cache/jw-investment-data/macro/`
- TTL: CPI 35天 / PMI 5天 / GDP 90天 / M2 35天 / LPR 25天 / worldbank 365天
- `--force` 跳过缓存强制刷新

## A股行情 (fetch_market_data.py)

### 数据源状态 (7引擎)

| 引擎 | 数据 | 认证 | 状态 | 备注 |
|:---|:---|:--:|:--:|:---|
| 腾讯 HTTP | A/H股实时行情 | ❌ | ✅ | curl直连 |
| Baostock | A股K线/财务 | ❌ | ✅ | EOD |
| 新浪 HTTPS | A/H股+五档盘口 | ❌ | ✅ | |
| AkShare 1.18 | A股实时行情 | ❌ | ✅ | 腾讯源 |
| 百度股市通 | A股独立源+盘口 | ❌ | ✅ | ~0.15s |
| Tushare | A股T+1/估值 | ❌ | ✅ | 独立数据库 |
| 雪球 | A股独立源 | ❌ | ✅ | cookie→API |
| yfinance | 港/美股 | ❌ | ⚠️ | 需代理 |
| efinance | 东方财富 | ❌ | ❌ | 封IP |

### 用法

```bash
python fetch_market_data.py --category quote --symbol 600519                    # 实时行情（7引擎交叉验证）
python fetch_market_data.py --category kline --symbol 600519 --start 20260101   # K线
python fetch_market_data.py --category financial --symbol 600519                # 5年多维财务（profit+balance+cashflow+dupont+growth+dividend）
python fetch_market_data.py --category profile --symbol 600519                  # 公司概况（基本信息+行业+最近4季摘要）
python fetch_market_data.py --category futures --symbol RB0 --market SHFE       # 期货
python fetch_market_data.py --category forex --symbol XAUUSD                    # 外汇
python fetch_market_data.py --category fund --symbol 000001                     # 基金
python fetch_market_data.py --schema                                            # 自描述
```

### financial 类别输出结构（v3.6 增强）

`--category financial` 返回5年×6维财务数据，顶层 `summary` 含最新一期关键指标：

```json
{
  "summary": {
    "latest_period": "2026-03-31",
    "revenue": 60629000000,
    "net_profit": 2815000000,
    "roe": 0.0625,
    "gross_margin": 0.1969,
    "current_ratio": 0.49,
    "liability_to_asset": 0.7494,
    "cfo_to_np": 1.70
  },
  "profit": [{...}],      // 17季利润表（ROE/毛利率/净利率/净利润/EPS/营收）
  "balance": [{...}],     // 17季资产负债表（流动比/速动比/负债率/权益乘数）
  "cashflow": [{...}],    // 17季现金流（CFO/营收比/CFO/净利比/利息覆盖倍数）
  "growth": [{...}],      // 17季成长能力（YoY净资产/总资产/净利润/EPS）
  "dupont": [{...}],      // 17季杜邦分析（ROE分解7因子）
  "dividend_raw": [[...]] // 5年分红记录
}
```

**覆盖 jw-company-analysis Step 2（财务健康度）的数据**：
- 盈利质量：profit（ROE/毛利率/净利率/净利润） + cashflow（CFO/净利比）
- 资产负债表：balance（流动比/速动比/负债率/权益乘数）
- 现金流质量：cashflow（CFO/营收比/CFO/净利比）
- 财务趋势：profit+growth+dupont（5年趋势）
- 分红：dividend_raw

### profile 类别输出结构（v3.6 新增）

`--category profile` 返回公司概况 + 最近4季财务摘要：

```json
{
  "basic": {"code": "sz.002493", "name": "荣盛石化", "ipo_date": "2010-11-02", "status": "1"},
  "industry": {"industry_code": "C26化学原料和化学制品制造业"},
  "recent_quarters": [
    {"period": "2026Q1", "roe": 0.0625, "gross_margin": 0.1969, "net_profit": 5011761160, "eps_ttm": 0.3078},
    {"period": "2025Q4", "roe": 0.0194, "gross_margin": 0.1221, "net_profit": 3248859294, "eps_ttm": 0.0849}
  ]
}
```

### comprehensive 类别输出结构（v3.9 增强 ⭐推荐）

`--category comprehensive` 一次调用返回公司分析所需的大部分量化数据（18个数据源）：

```json
{
  "adata_finance": { "summary": {...}, "rows": [...] },  // 43列×20期财务
  "forecast": { "rows": [...] },       // 业绩预告
  "express": { "rows": [...] },        // 业绩快报
  "operation": { "rows": [...] },      // 营运能力
  "shares": { "rows": [...] },         // 股本结构变动
  "concept": { "rows": [...] },        // 概念板块（东方财富）
  "plate": { "rows": [...] },          // 行业/板块/概念归属
  "north_flow": { "rows": [...] },     // 北向资金30日
  "stock_lifting": { "rows": [...] },  // 当月解禁股
  "popularity": { "rows": [...] },     // 人气榜TOP100
  "index_membership": { "membership": [...] },  // 指数成分
  "concept_ths": { "rows": [...] },    // 同花顺概念（v3.9新增）
  "hot_concept": { "rows": [...] },    // 同花顺热门概念TOP20（v3.9新增）
  "hot_rank": { "rows": [...] },       // 同花顺热门股TOP100（v3.9新增）
  "market_five": { "rows": [...] },    // 五档盘口（v3.9新增）
  "north_flow_current": { "summary": {...} },  // 北向资金实时（v3.9新增）
  "daily_movers": { "rows": [...] },   // 每日异动股（v3.9新增）
  "rates": { "loan": {...}, "deposit": {...} }  // 贷款/存款利率（v3.9新增，可能为空）
}
```

**覆盖 jw-company-analysis 各Step的数据**：
- Step 0（基础数据）：profile + shares（股本结构）+ plate（板块归属）+ index_membership（指数成分）
- Step 1（企业质量）：forecast（业绩预告）+ concept（概念板块）+ plate（行业归属）
- Step 2（财务健康）：adata_finance（43列）+ operation（营运能力）→ **覆盖85%+**
- Step 3（产业链）：concept + plate（概念/行业/板块归属）→ **覆盖35%+**
- Step 5（逆向检查）：stock_lifting（解禁风险）+ north_flow（北向资金情绪）→ **覆盖15%**
- Step 6（技术面）：capital_flow（资金流向）+ popularity（市场热度）
- Step 8（数据复验）：adata_finance 交叉验证 baostock financial

### capital_flow 类别（v3.7 新增）

`--category capital_flow` 返回最近30天资金流向（主力/大单/中单/小单/超大单）。

⚠️ 依赖 adata 东方财富接口，连接不稳定时可能失败。

### adata 能力全景（v3.8 实测确认）

**已接入 comprehensive 的11源**：

| # | 数据源 | adata/baostock函数 | 状态 |
|---|--------|-------------------|------|
| 1 | 43列财务核心 | `adata.stock.finance.get_core_index` | ✅ |
| 2 | 业绩预告 | `baostock.query_forecast_report` | ✅ |
| 3 | 业绩快报 | `baostock.query_performance_express_report` | ✅ |
| 4 | 营运能力 | `baostock.query_operation_data` | ✅ |
| 5 | 股本变动 | `adata.stock.info.get_stock_shares` | ✅ |
| 6 | 概念板块(东财) | `adata.stock.info.get_concept_east` | ✅ |
| 7 | 板块归属 | `adata.stock.info.get_plate_east` | ✅ |
| 8 | 北向资金 | `adata.sentiment.north.north_flow` | ✅ |
| 9 | 解禁数据 | `adata.sentiment.stock_lifting_last_month` | ✅ |
| 10 | 人气榜 | `adata.sentiment.hot.pop_rank_100_east` | ✅ |
| 11 | 指数成分 | `adata.stock.info.index_constituent` | ✅ |

**已测试可用但未接入**（未来扩展候选）：

| 函数 | 返回什么 | 测试结果 |
|------|---------|---------|
| `info.get_concept_ths` | 同花顺概念（比东财多，如"减速器""比亚迪概念"） | ✅ 9行 |
| `sentiment.hot.hot_concept_20_ths` | 同花顺热门概念TOP20（含热度值+连续上榜天数） | ✅ 20行 |
| `sentiment.hot.hot_rank_100_ths` | 同花顺热门股TOP100（含热度值/概念标签） | ✅ 100行 |
| `market.get_market_five` | 五档盘口（买卖5档×价格+数量） | ✅ |
| `sentiment.north.north_flow_current` | 当日实时北向资金 | ✅ |
| `sentiment.hot.list_a_list_daily` | 每日异动股列表（龙虎榜） | ✅ 91行 |
| `baostock.query_loan_rate_data` | 贷款利率历史 | ✅ |
| `baostock.query_deposit_rate_data` | 存款利率历史 | ✅ |
| `baostock.query_zz500_stocks` | 中证500成分股 | ✅ |

**不可用（已验证）**：

| 函数 | 问题 |
|------|------|
| `market.get_dividend` | 重定向超过30次（adata bug） |
| `info.get_dynamic_core_index` | 返回None |
| `info.get_industry_sw` | 返回空DataFrame |
| `info.get_concept_baidu` | 返回空DataFrame |
| `sentiment.hot.get_a_list_info` | 返回空（龙虎榜个股查询） |
| `sentiment.securities_margin` | 返回空（融资融券，数据源不可用） |

### 熔断器

- 每引擎独立追踪: 3次连续失败 → OPEN（熔断），10分钟后自动 HALF_OPEN 探测
- `--force` 重置所有熔断器
- 配置: `config/engines.yaml` → `breaker` 段

## 全局设施

### 配置: config/engines.yaml

```yaml
breaker:                    # 熔断器
  failure_threshold: 3
  recovery_timeout: 600    # 秒
cache:                      # 缓存策略
  intraday_ttl: 5          # 分钟 (盘中)
  eod_ttl: 1440            # 分钟 (盘后)
  macro_ttl:               # 宏观指标TTL (见脚本内置)
```

### 熔断器状态

```bash
python circuit_breaker.py    # 查看所有引擎状态
```

### 交易时钟

```bash
python market_clock.py       # 当前北京时间的市场状态 + 推荐缓存TTL
```

## 踩坑记录

### 0. 诊断优先：脚本失败时不要直接降级到 web search

**错误模式**：脚本报错 → 立即放弃 → 用 web search 取数 → 拿到过时数据（券商研报股价可能是1-2个月前的）

**正确流程**：
1. **看错误类型**：`No module named 'X'` → 安装依赖；`❌ 缺少股票代码` → 参数解析bug；`Timeout` → 网络/熔断器问题
2. **快速验证**：`python3 <script> --help` 能跑说明脚本本身没问题，是调用方式或依赖的问题
3. **读源码定位**：`head -70 <script>` 看参数解析逻辑；`grep 'import' <script>` 看依赖
4. **修复并验证**：修完立即跑一次确认
5. **仅在确认无法修复时**才降级到 web search

**数据时效性风险**：web search 获取的券商研报数据（股价、市值）可能是1-2个月前的。例如盐湖股份分析中，web search 返回 36.23元（4月1日研报），实际 API 返回 29.45元（6月5日），差异 18.7%。**关键数据（股价、市值、PE）必须用 API 验证。**

### 1. financial 类别数据极有限（✅ 已在 v3.6 修复）

**症状**（历史问题）：`--category financial` 返回原始数组，无字段名，只有单期利润数据

**修复**（v3.6）：`_baostock_financial()` 已升级为5年×6维查询（profit+balance+cashflow+dupont+growth+dividend），返回结构化JSON含summary摘要。新增 `--category profile` 获取公司概况+最近4季摘要。

**对公司分析的影响**：jw-company-analysis 的 Step 2（财务健康度）现在可直接用 `--category financial` 获取大部分数据，web search 仅需补充股东结构/管理层/近期事件等定性信息。

### 2. 脚本编码报错

**症状**：`python fetch_market_data.py` 报 `SyntaxError: Non-ASCII character '\xe7'`

**原因**：脚本 docstring 包含中文，但缺少编码声明头

**修复**：使用 `python3` 运行（Python 3 默认 UTF-8），或在脚本首行添加 `# -*- coding: utf-8 -*-`

```bash
# 正确
python3 fetch_market_data.py --category quote --symbol 600519

# 错误（python 指向 Python 2 时会报错）
python fetch_market_data.py --category quote --symbol 600519
```

### 3. 指数数据获取

**症状**：`--symbol 000001` 返回平安银行，不是上证指数

**原因**：所有引擎只支持个股代码，不支持指数代码（sh000001 等）

**解决方案**：获取指数行情用 web search，不要用 fetch_market_data.py

详见 `references/index-data-pitfall.md`

### 4. 脚本超时与熔断器累积

**症状**：`fetch_market_data.py` 调用30-60秒无响应，最终超时

**原因**：脚本串行调用8个引擎，每个超时5-10秒，总最坏耗时80秒。无总超时控制。熔断器需3次失败才触发，首次调用会尝试所有引擎。

**快速修复**：
```bash
# 方案1：外部超时包裹（推荐）
timeout 25 python fetch_market_data.py --category quote --symbol 600519 --force

# 方案2：重置熔断器
python fetch_market_data.py --category quote --symbol 600519 --force

# 方案3：检查熔断器状态
python circuit_breaker.py
```

**关键原则**：遇到超时不要重试，直接降级到 web search。详见 `references/timeout-and-circuit-breaker.md`。

### 5. jw-data 参数解析 bug（v3.5 原始版本）

**症状**：`jw-data quote 600519` 报 `❌ 缺少股票代码`，即使参数格式正确

**根因**：`jw-data` bash 脚本将 `SYMBOL` 绑定到 `ARGS[2]`（第三个非选项参数），但 `quote`/`kline`/`indicators` 命令不使用 `SUB`，股票代码在 `ARGS[1]`。而 `macro` 命令需要 `SUB`（如 `macro all`），所以它用 `ARGS[1]` 取子命令是正确的。

**修复**：将 `SYMBOL="${ARGS[2]:-}"` 改为 `SYMBOL="${ARGS[1]:-}"`（已在脚本中修复）

**诊断方法**（通用）：
1. 先看报错信息，判断是参数缺失还是依赖缺失
2. 用 `--help` 验证脚本基本功能
3. 读脚本源码（`head`/`grep`）定位参数解析逻辑
4. 测试修复后立即验证：`jw-data quote 600519`

### 6. 依赖包缺失

**症状**：`No module named 'baostock'` / `'akshare'` / `'yfinance'`

**修复**（系统无 pip/pip3 时用 venv）：
```bash
# 方案1：系统有 pip（推荐）
pip install akshare baostock yfinance -i https://mirrors.aliyun.com/pypi/simple/

# 方案2：系统无 pip（如 PEP 668 环境），创建 venv
uv venv ~/.hermes/skills/rancbos-skills/jw-investment-data/.venv
uv pip install baostock akshare yfinance --python ~/.hermes/skills/rancbos-skills/jw-investment-data/.venv/bin/python -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装后用 venv python 调用脚本
~/.hermes/skills/rancbos-skills/jw-investment-data/.venv/bin/python technical_indicators.py --symbol 600519 --format markdown
```

⚠️ 如果 `pip install` 超时，换用清华镜像 `-i https://pypi.tuna.tsinghua.edu.cn/simple`。

### 7. py_mini_racer DeprecationWarning 破坏 JSON 管道

**症状**：`python3 fetch_market_data.py ... 2>&1 | python3 -c "import json; ..."` 报 `JSONDecodeError`

**原因**：`py_mini_racer` 导入时输出 `DeprecationWarning: pkg_resources is deprecated` 到 stdout，混入 JSON 输出

**修复**：管道模式必须重定向 stderr：
```bash
# 正确
python3 fetch_market_data.py --category comprehensive --symbol 601689 --market A --format json 2>/dev/null | python3 -c "..."
# 错误
python3 fetch_market_data.py ... 2>&1 | python3 -c "..."
```

### 8. adata 东方财富接口连接不稳定

**症状**：`capital_flow` / `concept_constituent_east` 等 adata 函数报 `RemoteDisconnected` 或 `ConnectionError`

**原因**：adata 底层调用东方财富 API，服务器偶尔拒绝连接

**修复**：不阻塞分析，comprehensive 中单个 adata 函数失败时返回 None，其他数据照常获取。capital_flow 作为独立类别可能整体失败，属正常现象。

### 9. ETF/指数代码不支持 baostock K线

**症状**：`technical_indicators.py --symbol 510050` 返回 `无K线数据`

**原因**：baostock 只支持 A股个股代码（如 600519），不支持 ETF（510050、159915）和指数（sh000001）

**解决方案**：ETF/指数的技术分析通过 web search 获取，或用对应个股替代（如用贵州茅台600519代表上证权重股）

## Anti-Patterns（强制阅读）

- ❌ 脚本报错直接降级web search → 先诊断（看错误类型→--help→读源码→修复），仅确认无法修复时才降级
- ❌ 管道模式用 `2>&1` → 必须 `2>/dev/null`（py_mini_racer DeprecationWarning 会破坏JSON）
- ❌ 用指数代码(000001)查个股 → 000001=平安银行，不是上证指数。指数数据用web search
- ❌ comprehensive 返回空就放弃 → fallback 到 financial + web search
- ❌ 不检查脚本权限就调用 → 首次使用先 `chmod +x scripts/*.py`
- ❌ web search 获取的股价/市值直接采用 → 可能是1-2个月前的研报数据，必须用API验证关键价格

## 参考文档

| 文档 | 内容 |
|:---|:---|
| `references/data-source-matrix.md` | 完整数据源矩阵（免费/付费/代理需求） |
| `references/eastmoney-macro-api.md` | 东方财富宏观API端点+缓存策略 |
| `references/eastmoney-new-endpoints.md` | 东方财富新增端点(v3.5): 固投/工业/财政+Jin10交叉验证 |
| `references/baostock-interface-guide.md` | Baostock接口文档 |
| `references/macro-data-sources.md` | 宏观数据源调研全记录 |
| `references/engine-availability-and-pitfalls.md` | 各引擎可用性+踩坑记录 |
| `references/web-search-valuation-pattern.md` | **板块估值web search模式**：漏斗式3轮搜索、关键数据字段、已验证数据源 |
| `references/timeout-and-circuit-breaker.md` | 超时机制、熔断器状态、已知bug修复 |
| `references/yfinance-interface-guide.md` | yfinance 港美股接口 |
| `references/improvement-roadmap.md` | 后续改善路线图 |
| `references/adata-api-surface.md` | adata 2.9.5 API 能力地图（已验证函数+连通性+待接入清单） |
| `references/adata-capability-map.md` | adata/baostock 全部函数能力全景（已接入/可用未接入/不可用） |
| `references/architecture-conventions.md` | 架构约定（v3.5+ 所有脚本开发遵守） |
| `references/adata-integration-guide.md` | **adata 2.9.5 集成指南**：5个已验证函数+43列字段说明+与baostock互补关系 |
| `references/_archive/` | 已归档的历史文档（10个） |


## 版本记录

详见 `references/version-history.md`（完整版本历史）。

**v3.10.0 变更摘要**（2026-06-06）：
- S1：SKILL.md 从 583 行精简至 ~460 行
- S2：踩坑记录3组重复条目去重（-68行）
- S3：更新日志下沉到 references/version-history.md
- S4：新增 Anti-Patterns 集中章节
- S5：description 增加自然语言触发变体
- S6：参考文档表去重

# jw-investment-data v3.5.0

> 投资数据获取层——宏观全景、A股行情/财务/K线/技术指标，多源交叉验证，本地缓存。

## 目录

- [概述](#概述)
- [架构与运行逻辑](#架构与运行逻辑)
- [安装与依赖](#安装与依赖)
- [快速上手](#快速上手)
- [脚本参考](#脚本参考)
- [宏观数据](#宏观数据)
- [A股行情](#a股行情)
- [技术指标 & 图表](#技术指标--图表)
- [全局设施](#全局设施)
- [数据源矩阵](#数据源矩阵)
- [配置参考](#配置参考)
- [版本历史](#版本历史)

---

## 概述

**jw-investment-data** 是一个面向中国投资的本地数据获取层，提供四大能力：

| 能力 | 覆盖范围 | 引擎数 |
|:---|:---|:---:|
| **宏观全景** | GDP/CPI/PPI/PMI/M0-M2/LPR/存贷利率/准备金率/世界银行背景数据 | 5 |
| **A股行情** | 实时报价、K线、财务数据，A/H/期货/外汇/基金 | 8 |
| **技术指标** | MA/MACD/RSI/KDJ/布林带 | — |
| **K线图表** | K线 + 5个指标叠加 | — |

### 核心理念

- **免费优先** — 所有引擎均为免费公开数据源，无付费 API
- **多源交叉验证** — 相同指标从不同源获取，差异≤3% 自动认定一致
- **本地缓存** — 盘中 5 分钟、盘后 24 小时、宏观按发布周期缓存，`--force` 随时刷新
- **熔断降级** — 引擎连续失败 3 次自动熔断，10 分钟后半开探测恢复
- **数据 + 展示分离** — 所有脚本默认输出 JSON（机器读），`--format markdown` 输出可读报告

---

## 架构与运行逻辑

### 数据流

```
用户
 ├─ jw-data (统一入口)
 │    ├─ macro ──→ fetch_macro.py ──→ Baostock / 东方财富 / 中国货币网 / 世界银行 / Jin10 MCP
 │    ├─ quote ──→ fetch_market_data.py ──→ 腾讯 / 新浪 / 百度 / 雪球 / Tushare / AkShare / yfinance
 │    ├─ kline ──→ fetch_market_data.py ──→ 同上（K线模式）
 │    ├─ indicators ──→ technical_indicators.py
 │    ├─ chart ──→ draw_kline.py
 │    └─ health ──→ health_check.py
 │
 ├─ 直接调用脚本（跳过 jw-data）
 │    ├─ python fetch_macro.py --category cpi --format markdown
 │    ├─ python fetch_market_data.py --category quote --symbol 600519
 │    └─ python circuit_breaker.py  # 查看熔断器状态
 │
 └─ 内部模块（不独立调用）
      ├─ format_macro.py    — 宏观数据 Markdown 渲染
      ├─ format_market.py   — 行情数据 Markdown 渲染
      ├─ circuit_breaker.py — 熔断器（也可独立查看状态）
      ├─ market_clock.py    — 交易时钟
      └─ output_contract.py — 标准信封 {ok, data, meta}
```

### 关键设计

1. **标准信封**：所有数据输出格式统一为 `{"ok": true/false, "source": "...", "data": {...}, "error": null, "ts": ...}`
2. **熔断器**：每引擎独立追踪失败计数，3 次连续失败 → OPEN 状态，10 分钟自动 HALF_OPEN
3. **缓存**：行情盘中 5 分钟、盘后 24 小时；宏观按指标发布周期（CPI 35 天 / PMI 5 天 / GDP 90 天等）
4. **代理支持**：yfinance 等需要外网的引擎通过 `HTTP_PROXY` 环境变量使用代理
5. **自描述**：所有用户可调用的脚本均支持 `--schema`（输出 JSON Schema）和 `--version`

---

## 安装与依赖

### 系统依赖

Python 3.9+。推荐虚拟环境。

### Python 依赖

```bash
pip install akshare efinance baostock yfinance pandas matplotlib
# 可选: akshare-proxy（代理支持）
```

> **注意**：如果使用阿里云镜像：
> ```bash
> pip install akshare efinance baostock yfinance pandas matplotlib -i https://mirrors.aliyun.com/pypi/simple/
> ```

### 目录结构

```
~/.hermes/skills/jw-investment-data/
├── SKILL.md                 # Hermes Agent 技能文件
├── README.md                # 本文档
├── config/
│   └── engines.yaml         # 数据引擎配置（优先级/超时/熔断器/缓存）
├── scripts/
│   ├── jw-data              # 统一入口（bash 脚本）
│   ├── fetch_macro.py       # 宏观数据采集 v3.4.1
│   ├── fetch_market_data.py # A股/期货/港美股/外汇报价+K线+财务 v3.5.0
│   ├── technical_indicators.py  # 技术指标 v3.5.0
│   ├── draw_kline.py        # K线图 v3.5.0
│   ├── health_check.py      # 全源健康检查 v1.0.0
│   ├── format_macro.py      # 宏观 Markdown 渲染
│   ├── format_market.py     # 行情 Markdown 渲染
│   ├── circuit_breaker.py   # 熔断器（可独立查看状态）
│   ├── market_clock.py      # 交易时钟
│   └── output_contract.py   # 标准信封
├── references/              # 参考文档
│   ├── data-source-matrix.md
│   ├── eastmoney-macro-api.md
│   ├── baostock-interface-guide.md
│   ├── macro-data-sources.md
│   ├── engine-availability-and-pitfalls.md
│   ├── yfinance-interface-guide.md
│   ├── improvement-roadmap.md
│   ├── architecture-conventions.md
│   └── _archive/            # 已归档的历史文档（10个）
```

---

## 快速上手

```bash
cd ~/.hermes/skills/jw-investment-data/scripts

# ── 统一入口（推荐） ──
./jw-data macro all           # 宏观全景——GDP/CPI/PPI/PMI/M2/LPR
./jw-data macro cpi           # CPI 单独
./jw-data macro money         # M2 + LPR + 利率
./jw-data quote 600519        # 贵州茅台实时行情
./jw-data kline 600519 120    # 120 日 K 线
./jw-data indicators 600519   # 技术指标
./jw-data chart 600519        # K线图（PNG 输出）
./jw-data health              # 全源健康检查

# ── 直接调用脚本 ──
python fetch_macro.py --category all --format markdown   # 宏观全景，人读格式
python fetch_market_data.py --category quote --symbol 600519 --format markdown
```

---

## 脚本参考

所有脚本位于 `scripts/` 目录。用户可调用的脚本全部支持 `--schema` 和 `--version`。

| 脚本 | 类型 | 用途 | 输出格式 |
|:---|:---|:---|:---|
| `jw-data` | **入口** | 统一路由命令 | 路由到各脚本 |
| `fetch_macro.py` | **用户** | 宏观数据采集（GDP/CPI/PPI/PMI/M2/LPR/利率/准备金/世界银行） | JSON / Markdown |
| `fetch_market_data.py` | **用户** | A股/期货/港股/美港股/外汇报价+K线+财务 | JSON / Markdown |
| `technical_indicators.py` | **用户** | MA/MACD/RSI/KDJ/布林带计算 | JSON / Markdown |
| `draw_kline.py` | **用户** | K线图 + 指标叠加 | PNG |
| `health_check.py` | **用户** | 并行扫描全部数据源可用性 | JSON / Markdown |
| `circuit_breaker.py` | **工具** | 查看/管理熔断器状态 | 文本 |
| `format_macro.py` | **内部** | 宏观 Markdown 渲染 | — |
| `format_market.py` | **内部** | 行情 Markdown 渲染 | — |
| `market_clock.py` | **内部** | 当前市场状态 + 推荐缓存 TTL | — |
| `output_contract.py` | **内部** | 标准信封 `{ok, data, meta}` | — |

```bash
# 查看版本和自描述
python fetch_macro.py --version          # → fetch_macro v3.4.1
python fetch_macro.py --schema           # → JSON schema（支持所有参数）
python fetch_market_data.py --version    # → fetch_market_data v3.5.0
```

---

## 宏观数据

### 支持指标

| `--category` | 覆盖指标 | 数据源 |
|:---|:---|:---|
| `all` | 全部 | 所有源 |
| `growth` | GDP + PMI | 东方财富 |
| `inflation` | CPI + PPI | 东方财富 |
| `money` | M0/M1/M2 + LPR + 存贷利率 + 准备金率 | Baostock + 中国货币网 |
| `cpi` | 居民消费价格指数 | 东方财富 |
| `ppi` | 工业生产者出厂价格指数 | 东方财富 |
| `pmi` | 制造业采购经理指数 | 东方财富 |
| `gdp` | 国内生产总值 | 东方财富 |
| `lpr` | LPR 1年期/5年期 | 中国货币网 |
| `rates` | 存款/贷款利率 | Baostock |
| `reserve` | 存款准备金率 | Baostock |
| `calendar` | 经济日历提醒 | Jin10 MCP（Agent 侧实时） |

### 交叉验证

- **M2**：Baostock vs 东方财富 `RPT_ECONOMY_MONEY`，差异 ≤ 3% → ✅ 通过；> 3% → ⚠️ 标注（已知东方财富此端点有时不返回数据，已验证捕获）
- **CPI/PMI/GDP/PPI**：单源（东方财富），输出标注"待第二源确认"
- 验证结果写入 JSON `meta.verification` 段，Markdown 含完整交叉验证表

### 输出格式

```json
{
  "ok": true,
  "source": "eastmoney",
  "data": {
    "cpi": {
      "cpi_yoy": 1.2,
      "cpi_mom": 0.1,
      "period": "2026-04"
    },
    ...
  },
  "meta": {
    "latency_ms": 423,
    "version": "3.4.1",
    "errors": [],
    "verification": {}
  },
  "ts": "2026-05-27T10:00:00.000Z"
}
```

Markdown 输出为人读全景报告（9 段）：增长 / 通胀 / 货币 / 利率 / 准备金 / 日历 / 全球 / 美国 / 验证。

### 缓存

- 目录：`~/.hermes/cache/jw-investment-data/macro/`
- TTL：CPI 35 天 / PMI 5 天 / GDP 90 天 / M2 35 天 / LPR 25 天 / worldbank 365 天
- 缓存 TTL 配置化：修改 `config/engines.yaml` → `macro.cache` 段即可，无需改源码

---

## A股行情

### 数据源

| 引擎 | 数据 | 认证 | 状态 | 备注 |
|:---|:---|:--:|:--:|:---|
| 腾讯 HTTP | A/H 股实时行情 | ❌ | ✅ | 最快，curl 直连 |
| Baostock | A 股 K 线 / 财务 | ❌ | ✅ | EOD 数据 |
| 新浪 HTTPS | A/H 股 + 五档盘口 | ❌ | ✅ | 需要 Referer 头 |
| AkShare | A 股实时行情（腾讯源） | ❌ | ✅ | 翻页兜底 |
| 百度股市通 | A 股独立源 + 盘口 | ❌ | ✅ | ~0.15s 响应 |
| Tushare | A 股 T+1 / 估值 | ❌ | ✅ | 独立数据库 |
| 雪球 | A 股独立源 | ❌ | ✅ | cookie → API |
| yfinance | 港 / 美股 | ❌ | ⚠️ | 需 HTTP 代理 |
| efinance | 东方财富 | ❌ | ❌ | 本服 IP 被封 |

### 支持品种

```bash
--category
  quote      A 股实时行情（默认）  → --symbol 600519
  kline      K 线数据             → --symbol 600519 --start 20260101
  financial  财务数据              → --symbol 600519
  macro      A 股宏观              → --symbol 600519
  forex      外汇                  → --symbol XAUUSD
  futures    期货                  → --symbol RB0 --market SHFE
  fund       基金                  → --symbol 000001
```

### 熔断器

每引擎独立追踪失败计数：

```bash
python circuit_breaker.py          # 查看所有引擎当前状态
```

- 3 次连续失败 → OPEN（熔断），不再调用该引擎
- 10 分钟自动 HALF_OPEN → 允许一次探测请求
- `--force` 重置所有熔断器
- 配置：`config/engines.yaml` → `breaker` 段

---

## 技术指标 & 图表

### 技术指标

```bash
python technical_indicators.py --symbol 600519 --format markdown
```

支持指标：MA（5/10/20/60 日均线）、MACD、RSI、KDJ、布林带（20,2）。

### K线图

```bash
python draw_kline.py --symbol 600519 --ma_days "5,10,20,60"    # 输出 PNG
# 或通过 jw-data
./jw-data chart 600519
```

输出带交易量的 K 线图，叠加 MA / MACD / RSI / KDJ / BOLL 等指标。

---

## 全局设施

### 交易时钟

```bash
python market_clock.py
```

返回当前北京时间市场状态（盘中 / 午休 / 盘后 / 休市日），并自动推荐缓存 TTL（盘中 5 分钟，盘后 24 小时）。

### 健康检查

```bash
./jw-data health
# 或
python health_check.py --format markdown
```

并行扫描全部引擎，10 秒超时，90% 源在 1.5 秒内返回结果。退出码：

| 退出码 | 含义 |
|:---:|:---|
| 0 | 全部正常 |
| 1 | 部分失败（有降级但可用） |
| 2 | 全部失败 |

### 自描述

每个用户可调用的脚本可以查询自身 schema 和版本：

```bash
python fetch_macro.py --schema        # 输出 JSON Schema
python fetch_macro.py --version       # fetch_macro v3.4.1
python fetch_market_data.py --schema  # 输出所有参数和结构
```

---

## 数据源矩阵

| 源 | 数据类型 | 免费 | 需注册 | 需代理 | 速度 | 可靠性 |
|:---|:---|:--:|:--:|:--:|:--:|:--:|
| 腾讯 HTTP | A/H 行情 | ✅ | ❌ | ❌ | ⚡ | ✅ |
| 新浪 HTTPS | A/H 行情 + 盘口 | ✅ | ❌ | ❌ | ⚡ | ✅ |
| 百度股市通 | A 股独立源 + 盘口 | ✅ | ❌ | ❌ | ⚡ | ✅ |
| 雪球 | A 股独立源 | ✅ | ❌ | ❌ | ⚡ | ✅ |
| Tushare | A 股 K 线 + 财务 | ✅ | ❌ | ❌ | ⚡ | ✅ |
| AkShare | A 股行情翻页兜底 | ✅ | ❌ | ❌ | ⚡ | ✅ |
| Baostock | A 股 K 线 / 财务 EOD | ✅ | ❌ | ❌ | ⚡ | ✅ |
| 东方财富 | 宏观 CPI/PPI/PMI/GDP | ✅ | ❌ | ❌ | ⚡ | ✅ |
| 中国货币网 | LPR 1Y/5Y | ✅ | ❌ | ❌ | ⚡ | ✅ |
| 世界银行 | 中美 GDP/CPI 年度数据 | ✅ | ❌ | ❌ | ⚡ | ✅ |
| yfinance | 港 / 美股 | ✅ | ❌ | ✅ | ⚡ | ✅（有代理） |
| Jin10 MCP | 经济日历 / 快讯 | ✅ | ❌ | ❌ | ⚡ | ✅ |
| efinance | 东方财富 A 股行情 | ✅ | ❌ | ❌ | — | ❌（IP 被封） |

---

## 配置参考

主要配置在 `config/engines.yaml` 中管理：

### 熔断器

```yaml
breaker:
  failure_threshold: 3       # 连续失败 N 次 → 熔断
  recovery_timeout: 600      # 熔断 600 秒（10 分钟）→ 半开探测
  half_open_probes: 1        # 半开时允许 1 次探测
```

### 缓存

```yaml
cache:
  enabled: true
  ttl_minutes_trading: 5     # 盘中缓存 5 分钟
  ttl_minutes_closed: 1440   # 盘后缓存 24 小时
  directory: "~/.hermes/cache/jw-investment-data/"
```

### 宏观 TTL

```yaml
macro:
  cache:
    m2_ttl_days: 35          # M2，次月 15 日发布
    cpi_ttl_days: 35         # CPI，次月 10 日发布
    ppi_ttl_days: 35         # PPI，次月 10 日发布
    pmi_ttl_days: 5          # PMI，次月 1 日发布
    gdp_ttl_days: 90         # GDP，下季度发布
    lpr_ttl_days: 25         # LPR，每月 20 日发布
    rrr_ttl_days: 90         # 准备金率，不定期调整
    rate_ttl_days: 90        # 存贷利率，不定期调整
    calendar_ttl_days: 1     # 经济日历
    worldbank_ttl_days: 365  # 世界银行年度数据
```

### 校验参数

```yaml
verification:
  threshold_high: 0.02       # ≤ 2% → high confidence
  threshold_medium: 0.05     # ≤ 5% → medium confidence
  min_sources_high: 3        # 至少 3 源才给 high confidence
```

---

## 版本历史

**v3.5.0** — 全面像素级优化
- ⚙️ TTL 配置化：`config/engines.yaml` → `macro.cache` 段，改缓存策略不再需要改源码
- 📐 版本统一：`draw_kline.py` / `technical_indicators.py` 改用 `__version__`
- 📄 双 Formatter：`format_macro.py` + `format_market.py`，数据采集和展示完全分离
- 🏷️ `circuit_breaker` 加 `--schema`：所有用户可调用模块均已自描述
- 🔍 所有脚本加 `--version` 标志：`python fetch_macro.py --version`
- 🏥 健康检查：`health_check.py` — 9 源并行扫描，1.5s 出结果
- 🚪 统一入口：`jw-data` — 一个命令，`jw-data macro cpi` = `python fetch_macro.py --category cpi`
- 🔪 死代码清理：删 `fetch_stock/fetch_financial/data_validator`，7→7（替换为更高质）
- 📚 文档精简：17 references → 7 活 + 10 归档，移除虚设 JQData 章节
- 🔍 交叉验证：M2 双源对比实时接线，日历去硬编码改 MCP 动态提示
- ❌ 错误聚合：API 失败不再静默吞，JSON 和 Markdown 均可见
- ✅ frontmatter 合规：通过 skill-creator `quick_validate`

**v3.4.1**
- 🔪 砍掉死代码：`fetch_stock.py`、`fetch_financial.py`、`data_validator.py`
- 脚本从 10 个精简到 7 个

**v3.4.0** (2026-05-27)
- SKILL.md 重写：Usage 段前置，changelog 压缩
- 脚本合并：mydata 脚本全部移入 `scripts/`，旧目录清理
- 版本统一：全栈 `__version__`
- 交叉验证接线：M2 部署 Baostock vs 东方财富双源对比
- 日历去硬编码 → MCP 动态提示
- 错误聚合：`main()` 收集所有 API 失败 → `meta.errors`

**v3.3.0** — 宏观全系：+LPR + 世界银行 + Jin10 美国快讯

**v3.2.0** — 东方财富 API 接入：CPI/PMI/GDP/PPI

**v3.1.0** — 宏观数据模块上线：Baostock 货币/利率/准备金 + 缓存

**v3.0.0** — 熔断降级 + 交易时钟 + 标准信封 + `--force`

---
name: jw-investment-data
description: "投资数据获取层 v3.5：TTL配置化 + 统一版本号 + schema全覆盖 + 双formatter独立。全链路：宏观+行情+K线+技术指标。"
---

# jw-investment-data v3.5.0

投资数据获取层——宏观全景、A股行情/财务/K线/技术指标，多源交叉验证，本地缓存。

## 依赖

```
pip install akshare efinance baostock yfinance pandas matplotlib
# 可选: akshare-proxy（代理支持）
```

## 快速上手

```bash
cd ~/.hermes/skills/jw-investment-data/scripts

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
| `lpr` | LPR 1Y/5Y | 中国货币网 |
| `rates` | 存/贷款利率 | Baostock |
| `reserve` | 准备金率 | Baostock |
| `calendar` | 经济日历提醒 | Jin10 MCP (Agent侧实时) |

### 交叉验证

- **M2**: Baostock vs 东方财富 `RPT_ECONOMY_MONEY`，差异≤3% → ✅ 通过；>3% → ⚠️ 标注
- **CPI/PMI/GDP/PPI**: 单源(东方财富)，标注"待第二源确认"
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
python fetch_market_data.py --category quote --symbol 600519                    # 实时行情
python fetch_market_data.py --category kline --symbol 600519 --start 20260101   # K线
python fetch_market_data.py --category futures --symbol RB0 --market SHFE       # 期货
python fetch_market_data.py --category forex --symbol XAUUSD                    # 外汇
python fetch_market_data.py --category fund --symbol 000001                     # 基金
python fetch_market_data.py --schema                                            # 自描述
```

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

## 参考文档

| 文档 | 内容 |
|:---|:---|
| `references/data-source-matrix.md` | 完整数据源矩阵（免费/付费/代理需求） |
| `references/eastmoney-macro-api.md` | 东方财富宏观API端点+缓存策略 |
| `references/baostock-interface-guide.md` | Baostock接口文档 |
| `references/macro-data-sources.md` | 宏观数据源调研全记录 |
| `references/engine-availability-and-pitfalls.md` | 各引擎可用性+踩坑记录 |
| `references/yfinance-interface-guide.md` | yfinance 港美股接口 |
| `references/improvement-roadmap.md` | 后续改善路线图 |
| `references/architecture-conventions.md` | 架构约定（v3.5+ 所有脚本开发遵守） |
| `references/_archive/` | 已归档的历史文档（10个） |

## 更新日志

**v3.5.0 — 全面像素级优化**
- ⚙️ TTL 配置化：`engines.yaml` → `macro.cache` 段，修改 TTL 不再需要改源码
- 📐 版本统一：`draw_kline.py` / `technical_indicators.py` 改用 `__version__`
- 📄 双 Formatter：`format_macro.py` + `format_market.py`，数据采集和展示完全分离
- 🏷️ circuit_breaker 加 `--schema`：所有用户可调用模块均已自描述
- 🏥 健康检查：`health_check.py` — 9源并行扫描，1.5s 出结果
- 🚪 统一入口：`jw-data` — 一个命令，`jw-data macro cpi` = `python fetch_macro.py --category cpi`
- 🔪 死代码清理：删 `fetch_stock/fetch_financial/data_validator`，10→10（+3 -3）
- 📚 文档精简：17 references → 7 活 + 10 归档，移除虚设 JQData 章节
- 🔍 交叉验证：M2 双源对比实时接线，日历去硬编码改 MCP 动态提示
- ❌ 错误聚合：API 失败不再静默吞，JSON 和 Markdown 均可见
- 脚本：10 → **10**（替换为更高质量）

**v3.4.1**
- 🔪 砍掉死代码：`fetch_stock.py`、`fetch_financial.py`、`data_validator.py` — fetch_market_data.py 已覆盖全部功能
- 脚本从 10 个精简到 7 个

**v3.4.0 (2026-05-27)**
- SKILL.md 重写：Usage 段前置，changelog 压缩
- 脚本合并：mydata 脚本全部移入 `scripts/`，旧目录清理
- 版本统一：全栈 `__version__ = "3.4.0"`
- 交叉验证接线：M2 部署 Baostock vs 东财双源对比（`--category money` 自动触发）
- 日历去硬编码：`_calendar_hint()` / `_us_macro_hint()` 改为 MCP 实时查询提示
- 错误聚合：`main()` 收集所有 API 失败 → `_errors` 段 + Markdown 错误节
- LPR 独立：新增 `--category lpr` 选项
- 世界银行缓存 TTL → 365天

**v3.3.0** — 宏观全系：+LPR +世界银行 + Jin10 美国快讯

**v3.2.0** — 东方财富 API 接入：CPI/PMI/GDP/PPI

**v3.1.0** — 宏观数据模块上线：Baostock 货币/利率/准备金 + 缓存

**v3.0.0** — 熔断降级 + 交易时钟 + 标准信封 + `--force`

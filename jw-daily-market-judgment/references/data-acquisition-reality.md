# 数据采集实测记录

> 最后更新: 2026-06-02 | jw-daily-market-judgment v3.3.0

## jw-investment-data 实测结果

### 指数行情获取

| 方法 | 000001(上证) | 399001(深证) | 399006(创业板) | 结论 |
|------|:--:|:--:|:--:|------|
| `fetch_market_data.py --category quote --symbol 000001` | ❌ 返回平安银行 | — | — | 不支持指数代码 |
| `fetch_market_data.py --category quote --symbol sh000001` | ❌ 无数据 | — | — | 不支持指数前缀格式 |
| `mcp_minimax_search_web_search` | ✅ | ✅ | ✅ | **首选方案** |

**结论**: 指数行情必须通过 web search 获取，不能依赖 `fetch_market_data.py`。

### 脚本运行环境

- 必须使用 `python3`（非 `python`），否则中文注释导致 SyntaxError
- 路径: `cd ~/.hermes/skills/jw-investment-data/scripts`
- **必须用 `timeout 25` 包裹所有脚本调用**，防止超时阻塞

### baostock 依赖（2026-06-02 实测）

`technical_indicators.py` 依赖 `baostock`，系统无 pip 时需在 venv 中安装：

```bash
# 安装（只需一次）
uv venv ~/.hermes/skills/jw-investment-data/.venv
uv pip install baostock --python ~/.hermes/skills/jw-investment-data/.venv/bin/python -i https://pypi.tuna.tsinghua.edu.cn/simple

# 调用（必须用 venv python）
~/.hermes/skills/jw-investment-data/.venv/bin/python ~/.hermes/skills/jw-investment-data/scripts/technical_indicators.py --symbol 600519 --format markdown
```

**⚠️ baostock 限制**：
- ✅ 支持：A股个股代码（600519、000968、002995 等）
- ❌ 不支持：ETF（510050、159915 等）、指数（sh000001 等）
- 有缓存时直接返回（~1ms），无缓存时首次调用 ~600ms

### 超时问题（2026-06-01 发现）

`fetch_market_data.py` 串行调用 8 个引擎，无总超时，首次调用最坏 80 秒。

**实测表现**：
- 有缓存时：~1ms（直接返回缓存）
- 无缓存正常：~7秒（6引擎成功）
- 网络波动时：超时（8引擎串行等待）

**解决方案**：已在 SKILL.md 采集流程中所有脚本调用前加 `timeout 25`。

### technical_indicators.py bug 修复

**问题**：第246行使用 `VERSION` 变量（未定义），导致 Markdown 输出时 NameError。
**修复**：`sed -i 's/VERSION)/__version__)/g' technical_indicators.py`
**状态**：已修复（2026-06-01）

### K线和技术指标

- `fetch_market_data.py --category kline` 对个股可用（如 600519），对指数不可用
- `technical_indicators.py` 对个股可用（需 venv python），对 ETF/指数不可用
- 输出格式：JSON 和 Markdown 均可用

### 各引擎可用性（2026-06-01 实测）

| 引擎 | 状态 | 响应时间 | 备注 |
|------|------|---------|------|
| tencent_http | ✅ | ~0.3s | 最快 |
| sina_https | ✅ | ~3s | 稳定 |
| baostock | ✅ | ~1s | K线数据首选 |
| akshare | ✅ | ~1s | 内部模块 stock_zh_a_spot_tx |
| baidu | ✅ | ~2s | 稳定 |
| tushare | ✅ | ~2s | 稳定 |
| xueqiu | ❌ | — | 需要cookie |
| yfinance | ❌ | — | Yahoo限流 |

6/8 引擎可用，数据置信度高。

## Web Search 数据质量

2026-06-01 实测，`mcp_minimax_search_web_search` 搜索"A股 今日行情"可获取：
- 指数收盘价和涨跌幅
- 成交额
- 涨跌家数、涨停/跌停数
- 板块涨跌排行
- 连板梯队信息
- 北向资金动向

数据来源：东方财富、新浪财经、凤凰网财经等权威财经网站，质量可靠。

**注意**：不同财经网站的成交额、涨跌家数可能有微小差异（统计口径不同），取多个来源的中位数即可。

## 推荐采集流程

```bash
# 0. 技术指标（个股，用 venv python）
~/.hermes/skills/jw-investment-data/.venv/bin/python ~/.hermes/skills/jw-investment-data/scripts/technical_indicators.py --symbol 600519 --format markdown

# 1. 指数行情 → web search（必须，脚本不支持指数）
mcp_minimax_search_web_search(query="A股 今日行情 上证指数 深证成指")

# 2. 涨跌家数、板块涨跌、北向资金 → web search（必须，脚本不覆盖）
mcp_minimax_search_web_search(query="A股 涨跌家数 涨停 跌停 北向资金")

# 3. 连板梯队 → web search
mcp_minimax_search_web_search(query="A股 连板梯队 首板晋级率 高度板")

# 4. 融资融券 → web search
mcp_minimax_search_web_search(query="A股 融资融券余额 两融")
```

**关键原则**：先调脚本（技术指标），再用 web search 补充（指数/涨跌家数/资金流向）。不要跳过脚本直接全用 web search。

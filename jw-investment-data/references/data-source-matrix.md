# 数据源全矩阵

## 快速决策表

| 我想查... | 主引擎 | 备选引擎 | 第三源 | 不需要 pip install |
|----------|--------|---------|--------|-------------------|
| A股实时行情 | `ak.stock_zh_a_spot_em()` | `ef.stock.get_realtime_quotes()` | `bs.query_history_k_data_plus()` | 新浪 `hq.sinajs.cn` |
| A股日K线 | `ak.stock_zh_a_hist()` | `ef.stock.get_quote_history()` | `bs.query_history_k_data_plus()` | — |
| A股财务数据 | `ak.stock_financial_abstract()` | `ef.stock.get_financial_data()` | — | — |
| 港股实时行情 | `yf.Ticker.info` | `ak.stock_hk_spot_em()` | `ef.stock.get_realtime_quotes()` | 腾讯 `qt.gtimg.cn` |
| 美股实时行情 | `yf.Ticker.info` | `ak.stock_us_spot_em()` | pdr `DataReader` | — |
| 国内期货 | `ak.futures_zh_daily_sina()` | — | — | — |
| 外汇汇率 | `ak.currency_boc_sina()` | `yf.Ticker` | Jin10 MCP | — |
| 宏观经济 | `ak.macro_china_gdp()` | pdr Fred | — | — |
| 基金净值 | `ak.fund_open_fund_daily_em()` | `ef.fund` | — | — |

## 校验阈值

| 数据类别 | 三源阈值 | 说明 |
|---------|---------|------|
| 股票行情 | 2% | 实时价差异来自延迟 vs 实时 |
| K线 | 不做浮点校验 | 改比记录数和首尾日期 |
| 财务数据 | 5% | 口径差异（TTM vs 年报） |
| 外汇 | 1% | 汇率波动极小 |
| 宏观 | 5% | 源间口径差异 |

## 引擎失败时的降级路径

```
AkShare 失败 → efinance → Baostock → 手动 HTTP 接口
yfinance 失败 → AkShare 对应接口 → efinance
所有 Python 引擎失败 → HTTP 直连接口（qt.gtimg.cn / hq.sinajs.cn）+ 网页抓取（雪球 xueqiu.com）
```

## 🔴 网络受限环境回退路径

当本地 Python 引擎因网络限制全部不可达时，使用代理的网络工具（search / web_fetch）走不同出口：

| 源 | 方法 | 数据内容 |
|------|------|---------|
| **腾讯 qt.gtimg.cn** | web_fetch GET | A股实时行情（纯文本，`~` 分隔字段） |
| **雪球 xueqiu.com** | web_fetch 网页 | A/港/美股行情 + PE/PB/市值/股息率 |
| **新浪 hq.sinajs.cn** | web_fetch GET | A股实时行情（逗号分隔 JS） |
| **搜索摘录** | tavily_search | 昨收/前日数据（及时性滞后1天） |

### 腾讯 API 字段速查（`qt.gtimg.cn/q=sh600519`）

```
按 ~ 分割，字段索引：
[3]=最新价  [4]=昨收  [5]=今开
[30]=涨跌额  [31]=涨跌幅  [32]=最高  [33]=最低
[38]=PE(TTM)  [43]=总市值(亿元)  [46]=PB
```

代码前缀：上证 `sh` / 深证 `sz` / 港股 `hk`

完整回退协议见 `references/http-fallback-apis.md`

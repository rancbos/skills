# yfinance 常用接口速查

> GitHub: https://github.com/ranaroussi/yfinance
> 数据源：Yahoo Finance

## 安装

```bash
pip install yfinance
```

## 港股

```python
import yfinance as yf

# 腾讯
tk = yf.Ticker("0700.HK")

# 核心字段（info dict）
info = tk.info
price = info["regularMarketPrice"]     # 当前价
pe = info.get("trailingPE")            # PE-TTM
pb = info.get("priceToBook")           # PB
roe = info.get("returnOnEquity")       # ROE
div_yield = info.get("dividendYield")  # 股息率
mcap = info.get("marketCap")           # 总市值
rev = info.get("totalRevenue")         # 营收
ni = info.get("netIncomeToCommon")     # 净利润
fiftytwo_high = info.get("fiftyTwoWeekHigh")  # 52周最高
fiftytwo_low = info.get("fiftyTwoWeekLow")    # 52周最低
```

## 美股

```python
# 苹果
tk = yf.Ticker("AAPL")
info = tk.info
# 同上，字段名称一致
```

## 历史K线

```python
# 日K（近一年）
df = tk.history(period="1y")

# 指定日期范围
df = tk.history(start="2025-01-01", end="2026-05-27")

# 周K / 月K
df = tk.history(period="1y", interval="1wk")  # 1wk, 1mo

# 列：Open, High, Low, Close, Volume, Dividends, Stock Splits
```

## 财务数据

```python
# 三大报表
tk.financials       # 年度利润表
tk.balance_sheet    # 资产负债表
tk.cashflow         # 现金流量表

# 季度数据
tk.quarterly_financials
```

## 指数

```python
hsi = yf.Ticker("^HSI")     # 恒生
spx = yf.Ticker("^GSPC")    # 标普500
nq = yf.Ticker("^IXIC")     # 纳斯达克
spx_hist = spx.history(period="1mo")
```

## 外汇

```python
# 黄金期货作为 XAU 代理
gold = yf.Ticker("GC=F")      # 黄金期货
oil = yf.Ticker("CL=F")       # WTI原油
# 汇率: USDCNY=X, EURUSD=X
usdcny = yf.Ticker("USDCNY=X")
```

## 常见坑

1. 对A股支持很差，**不要用 yfinance 查 A 股**
2. 港股代码格式：`0700.HK`（4位数补零 + `.HK`）
3. 美股直接传 ticker 名（`AAPL`、`TSLA`、`MSFT`）
4. `info` dict 字段偶有空，始终用 `.get()` 防 KeyError
5. 历史数据默认是 UTC 时区，需要用 `df.index.tz_convert('Asia/Shanghai')`

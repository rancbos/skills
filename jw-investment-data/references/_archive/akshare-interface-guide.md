# 操盘手AkShare 核心接口速查

> 官方文档: https://akshare.akfamily.xyz/

## 安装

```bash
pip install akshare
```

## A股行情

```python
import akshare as ak

# 沪深A股实时行情（全量DataFrame）
df = ak.stock_zh_a_spot_em()
# 列：代码, 名称, 最新价, 涨跌幅, 涨跌额, 成交量, 成交额, 换手率, 量比, 市盈率, 市净率, ...

# 单只筛选
row = df[df["代码"] == "600519"].iloc[0]
price = row["最新价"]   # float
```

## A股历史K线

```python
import akshare as ak

# 复权类型: ""=不复权, "qfq"=前复权, "hfq"=后复权
# period: "daily" | "weekly" | "monthly"
df = ak.stock_zh_a_hist(
    symbol="600519",       # 代码
    period="daily",        # 频率
    start_date="20250101", # YYYYMMDD
    end_date="20260527",
    adjust="qfq"           # 复权
)
# 列：日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率
```

## A股财务数据

```python
# 财报摘要
df = ak.stock_financial_abstract(symbol="600519")
# 列：日期, 总营收, 净利润, 每股收益, 每股净资产, 净资产收益率, ...

# 分红数据
df = ak.stock_dividents_cninfo(symbol="600519")
```

## 港股行情

```python
# 实时
df = ak.stock_hk_spot_em()
row = df[df["代码"] == "00700"].iloc[0]

# 历史K线
df = ak.stock_hk_hist(symbol="00700", period="daily", start_date="20250101", end_date="20260527", adjust="qfq")
```

## 美股行情

```python
# 实时
df = ak.stock_us_spot_em()

# 历史K线
df = ak.stock_us_hist(symbol="106.AAPL", period="daily", start_date="20250101", end_date="20260527", adjust="qfq")
```

## 宏观数据

```python
# GDP
df = ak.macro_china_gdp()

# CPI（月度）
df = ak.macro_china_cpi_monthly()

# PMI
df = ak.macro_china_pmi()

# 货币供应 M0/M1/M2
df = ak.macro_china_money_supply()
```

## 外汇

```python
# 中行外汇牌价
df = ak.currency_boc_sina()

# 历史汇率
df = ak.currency_hist()
```

## 期货

```python
# 国内期货日线
df = ak.futures_zh_daily_sina(symbol="RB0")  # 螺纹钢

# 国际期货（COMEX/NYMEX）
df = ak.futures_foreign_hist(symbol="黄金")
```

## 基金

```python
# 开放式基金净值
df = ak.fund_open_fund_daily_em(symbol="000001")

# 基金基本信息
df = ak.fund_open_fund_info_em(symbol="000001", indicator="单位净值走势")
```

## 常见坑

1. 部分接口会返回全量数据（几千行），筛选时用 `df[df["代码"] == "xxx"]`
2. 日期格式统一用 `YYYYMMDD` 字符串
3. 网络不稳定时可能超时，重试 2-3 次通常可解
4. 接口偶有变更，更新 `pip install --upgrade akshare` 获取最新接口

# efinance 常用接口速查

> GitHub: https://github.com/Micro-sheep/efinance (3.7k⭐)
> 数据源：东方财富

## 安装

```bash
pip install efinance
```

## A股行情

```python
import efinance as ef

# 实时行情（多只）
df = ef.stock.get_realtime_quotes(stock_codes=["600519", "000001"])
# 列：股票代码, 股票名称, 最新价, 涨跌幅, 涨跌额, 成交量, 成交额, 换手率, 量比, 动态市盈率

# 单只
info = ef.stock.get_realtime_quotes(stock_codes=["600519"])
price = float(info.iloc[0]["最新价"])
```

## A股历史K线

```python
# klt: 101=日, 102=周, 103=月
# beg/end: YYYYMMDD 或 YYYYMMDDHHMMSS
df = ef.stock.get_quote_history(
    "600519", 
    beg="20250101", 
    end="20260527", 
    klt=101
)
# 列：日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率
```

## 港股

```python
# 港股代码格式: "00700.HK" 或直接 "00700"
df = ef.stock.get_realtime_quotes(stock_codes=["00700.HK"])
```

## 基金

```python
# 基金信息
info = ef.fund.get_base_info("000001")

# 基金净值
nav = ef.fund.get_realtime_quotes("000001")
```

## 优势

1. 基于东方财富数据，接口稳定性高
2. 轻量即用，无复杂依赖
3. 港股/基金/债券/期货 覆盖面广
4. 返回 pandas DataFrame，直接可用

## 常见坑

1. 港股代码需加 `.HK` 后缀（如 `00700.HK`）
2. 少数接口可能因东方财富改版而变动
3. 不做高频调用（会被反爬）

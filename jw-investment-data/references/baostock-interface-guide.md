# Baostock 常用接口速查

> 官方文档: https://www.baostock.com/helpDocsHome
> 特点：完全免费、无需注册、专注 A 股历史数据

## 安装

```bash
pip install baostock
```

## 基本用法

```python
import baostock as bs

# 每次使用前登录
lg = bs.login()
print(lg.error_msg)  # "success" 表示登录成功

# 退出（脚本结束前）
bs.logout()
```

**注意**：`baostock` 是阻塞式连接，不需要重复 login。本 Skill 中 Baostock 作为第三校验源，仅在需要时调用。

## A股日K线

```python
import baostock as bs

lg = bs.login()

# 上证（6开头）→ sh.xxxxxx
# 深证（0/3开头）→ sz.xxxxxx
code = "sh.600519"   # 茅台

# frequency: "d"=日, "w"=周, "m"=月
# adjustflag: "1"=后复权, "2"=前复权, "3"=不复权
rs = bs.query_history_k_data_plus(
    code,
    "date,code,open,high,low,close,volume,amount,adjustflag",
    start_date='2025-01-01',
    end_date='2026-05-27',
    frequency="d",
    adjustflag="2"
)

# 逐行读取
rows = []
while (rs.error_code == '0') & rs.next():
    rows.append(rs.get_row_data())

bs.logout()
```

## A股分钟K线

```python
# 5分钟、15分钟、30分钟、60分钟
rs = bs.query_history_k_data_plus(
    code,
    "date,time,code,open,high,low,close,volume,amount,adjustflag",
    start_date='2026-05-01',
    end_date='2026-05-27',
    frequency="5",    # 5分钟
    adjustflag="3"
)
```

## 上市公司基本信息

```python
rs = bs.query_stock_basic(code="sh.600519")
row = rs.get_row_data()
# 列：code, code_name, ipoDate, outDate, type, status

# 所有 A 股列表
rs = bs.query_stock_basic()
```

## 财务数据

```python
# 季频盈利能力（需要指定年份和季度）
rs = bs.query_profit_data(code="sh.600519", year=2025, quarter=4)
# 营收、净利、EPS、ROE、毛利率、净利率等

# 季频营运能力
rs = bs.query_operation_data(code="sh.600519", year=2025, quarter=4)

# 季频成长能力
rs = bs.query_growth_data(code="sh.600519", year=2025, quarter=4)
```

## 常见坑

1. **必须先 `login()`**，否则所有查询报错
2. 只支持 **A股**，没有港股/美股
3. 数据偏历史（非实时），日终更新，不适合盘中交易
4. 代码格式 `sh.600519` / `sz.000001`（注意前缀）
5. 返回是迭代器模式，用 `while rs.next()` 逐行取

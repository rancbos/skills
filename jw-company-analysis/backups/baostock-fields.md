# baostock 财务数据字段名参考

> **用途**：baostock 的财务数据字段名与直觉不同，本文档记录正确字段名，避免 KeyError。

## 利润表 (`query_profit_data`)

| 字段名 | 含义 | 示例值 |
|--------|------|--------|
| `gpMargin` | 毛利率 | 0.214787 (21.48%) |
| `npMargin` | 净利率 | 0.083054 (8.31%) |
| `roeAvg` | ROE | 0.212202 (21.22%) |
| `netProfit` | 净利润 | 1214259274.84 (元) |
| `epsTTM` | EPS TTM | 0.807240 (元) |
| `MBRevenue` | 营收 | 14620170066.18 (元) |
| `totalShare` | 总股本 | — |
| `liqaShare` | 流通股本 | — |

## 成长能力 (`query_growth_data`)

| 字段名 | 含义 | 示例值 |
|--------|------|--------|
| `YOYNI` | 净利润同比增长率 | 0.099358 (9.94%) |
| `YOYPNI` | 扣非净利润同比增长率 | 0.098628 (9.86%) |
| `YOYEquity` | 净资产同比增长率 | — |
| `YOYAsset` | 总资产同比增长率 | — |
| `YOYEPSBasic` | 基本EPS同比增长率 | — |

## 资产负债 (`query_balance_data`)

| 字段名 | 含义 | 示例值 |
|--------|------|--------|
| `liabilityToAsset` | 资产负债率 | 0.55 (55%) |
| `currentRatio` | 流动比率 | 1.285731 |
| `quickRatio` | 速动比率 | 0.997431 |
| `cashRatio` | 现金比率 | — |
| `assetToEquity` | 权益乘数 | — |

## 使用示例

```python
import baostock as bs
lg = bs.login()

# 利润表
rs = bs.query_profit_data(code='sz.000680', year=2025, quarter=4)
data = []
while (rs.error_code == '0') and rs.next():
    data.append(rs.get_row_data())
df = pd.DataFrame(data, columns=rs.fields)
print(f"毛利率: {df.iloc[0]['gpMargin']}")
print(f"净利率: {df.iloc[0]['npMargin']}")
print(f"ROE: {df.iloc[0]['roeAvg']}")

bs.logout()
```

## ⚠️ 注意事项

- 所有比率字段都是小数形式（0.21 = 21%），需要手动转换
- `netProfit` 单位是元，不是亿元
- baostock 不支持 `ma`、`kdj` 等技术指标，需手动计算
- 数据可能有延迟，建议与年报/季报交叉验证

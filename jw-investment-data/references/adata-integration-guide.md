# adata 2.9.5 集成指南

> 系统已安装 adata 2.9.5，提供高价值财务和市场数据。以下为已验证可用的函数。

## 已验证可用函数

### 1. finance.get_core_index — ⭐⭐⭐⭐⭐ 最高价值

72行×43列完整财务指标，多年历史数据。

```python
import adata
df = adata.stock.finance.get_core_index(stock_code='002379')
```

**字段列表（43列）**：
| 字段 | 含义 | 分析用途 |
|------|------|---------|
| basic_eps | 基本每股收益 | Step 2.1 |
| diluted_eps | 稀释每股收益 | Step 2.1 |
| non_gaap_eps | 扣非每股收益 | Step 2.1 |
| net_asset_ps | 每股净资产 | Step 4 |
| cap_reserve_ps | 每股资本公积 | Step 2.2 |
| undist_profit_ps | 每股未分配利润 | Step 2.2 |
| oper_cf_ps | 每股经营现金流 | Step 2.3 |
| total_rev | 营业总收入 | Step 2.4 |
| gross_profit | 毛利润 | Step 2.1 |
| net_profit_attr_sh | 归母净利润 | Step 2.1 |
| non_gaap_net_profit | 扣非净利润 | Step 2.1 |
| total_rev_yoy_gr | 营收同比增速 | Step 2.4 |
| net_profit_yoy_gr | 净利润同比增速 | Step 2.4 |
| non_gaap_net_profit_yoy_gr | 扣非净利润同比增速 | Step 2.4 |
| total_rev_qoq_gr | 营收环比增速 | Step 2.4 |
| net_profit_qoq_gr | 净利润环比增速 | Step 2.4 |
| non_gaap_net_profit_qoq_gr | 扣非净利环比增速 | Step 2.4 |
| roe_wtd | 加权ROE | Step 2.4 |
| roe_non_gaap_wtd | 扣非加权ROE | Step 2.4 |
| roa_wtd | 加权ROA | Step 2.4 |
| gross_margin | 毛利率 | Step 2.1 |
| net_margin | 净利率 | Step 2.1 |
| adv_receipts_to_rev | 预收账款/营收 | Step 2.2 |
| net_cf_sales_to_rev | 销售现金流/营收 | Step 2.3 |
| oper_cf_to_rev | 经营现金流/营收 | Step 2.3 |
| eff_tax_rate | 有效税率 | Step 2.1 |
| curr_ratio | 流动比率 | Step 2.2 |
| quick_ratio | 速动比率 | Step 2.2 |
| cash_flow_ratio | 现金比率 | Step 2.2 |
| asset_liab_ratio | 资产负债率 | Step 2.2 |
| equity_multiplier | 权益乘数 | Step 2.2 |
| equity_ratio | 权益比率 | Step 2.2 |
| total_asset_turn_days | 总资产周转天数 | Step 2.1 |
| inv_turn_days | 存货周转天数 | Step 2.1 |
| acct_recv_turn_days | 应收账款周转天数 | Step 2.1 |
| total_asset_turn_rate | 总资产周转率 | Step 2.1 |
| inv_turn_rate | 存货周转率 | Step 2.1 |
| acct_recv_turn_rate | 应收账款周转率 | Step 2.1 |

**⚠️ 注意**：数据按时间正序排列（最旧在前），需用 `df.tail(N)` 取最近N期。

### 2. info.get_stock_shares — ⭐⭐⭐ 股本结构

```python
df = adata.stock.info.get_stock_shares(stock_code='002379')
# 返回: stock_code, change_date, total_shares, limit_shares, list_a_shares, change_reason
```

用途：Step 0 获取总股本/限售股/流通股，判断流通比例和解禁风险。

### 3. market.get_market — ⭐⭐ K线行情

```python
df = adata.stock.market.get_market(stock_code='002379', start_date='2026-01-01')
# 返回: stock_code, trade_time, trade_date, open, close, high, low, volume, amount, change_pct, change, turnover_ratio, pre_close
```

用途：Step 6 补充行情源，计算技术指标。

### 4. market.get_capital_flow — ⭐⭐ 资金流向

```python
df = adata.stock.market.get_capital_flow(stock_code='002379')
# 返回: stock_code, trade_date, main_net_inflow, sm_net_inflow, mid_net_inflow, lg_net_inflow, max_net_inflow
```

用途：Step 6 技术面分析，判断主力资金动向。

### 5. info.get_concept_east — ⭐ 概念板块

```python
df = adata.stock.info.get_concept_east(stock_code='002379')
# 返回: stock_code, concept_code, name, source, reason
```

用途：Step 3 产业链分析，了解公司所属概念板块。

## 不可用函数（已验证）

| 函数 | 问题 |
|------|------|
| `market.get_dividend` | Exceeded 30 redirects |
| `info.get_industry_sw` | 返回空 DataFrame |
| `market.get_market_bar` | 超时 |
| `info.get_dynamic_core_index` | 返回 None |
| `market.list_market_current` | columns 为空 |

## 与 baostock 的互补关系

| 数据类型 | baostock | adata | 推荐 |
|---------|----------|-------|------|
| 财务指标（利润/负债/现金流/杜邦） | ✅ 5年×6维 | ✅ 43列多年 | 两者互补 |
| 营运能力（周转率） | ✅ query_operation_data | ✅ 内置在 finance | adata更全 |
| 业绩预告/快报 | ✅ 专用函数 | ❌ | baostock |
| 股本结构 | ❌ | ✅ get_stock_shares | adata |
| 资金流向 | ❌ | ✅ get_capital_flow | adata |
| 概念板块 | ❌ | ✅ get_concept_east | adata |
| K线 | ✅ query_history_k_data_plus | ✅ get_market | baostock更稳定 |
| 分红 | ✅ query_dividend_data | ❌ | baostock |

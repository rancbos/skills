# adata 2.9.5 能力全景图

> 最后验证：2026-06-04，双环传动(002472)

## 已接入 comprehensive（11源）

| # | 数据源 | 函数 | 返回格式 |
|---|--------|------|---------|
| 1 | 43列财务核心 | stock.finance.get_core_index | DataFrame×20期 |
| 2 | 业绩预告 | baostock.query_forecast_report | 逐行 |
| 3 | 业绩快报 | baostock.query_performance_express_report | 逐行 |
| 4 | 营运能力 | baostock.query_operation_data | 逐行×12季 |
| 5 | 股本变动 | stock.info.get_stock_shares | DataFrame |
| 6 | 概念板块(东财) | stock.info.get_concept_east | DataFrame |
| 7 | 板块归属 | stock.info.get_plate_east | DataFrame |
| 8 | 北向资金 | sentiment.north.north_flow | DataFrame×30日 |
| 9 | 解禁数据 | sentiment.stock_lifting_last_month | DataFrame×全局 |
| 10 | 人气榜 | sentiment.hot.pop_rank_100_east | DataFrame×100 |
| 11 | 指数成分 | stock.info.index_constituent | DataFrame×300 |

comprehensive 总耗时：60-120秒

## 已测试可用未接入

- info.get_concept_ths: 同花顺概念（比东财多）
- hot.hot_concept_20_ths: 热门概念TOP20+热度值
- hot.hot_rank_100_ths: 热门股TOP100+热度值
- market.get_market_five: 五档盘口
- north.north_flow_current: 当日实时北向资金
- hot.list_a_list_daily: 每日异动股（龙虎榜）

## 不可用（已验证）

- market.get_dividend: 重定向超过30次（adata bug）
- info.get_dynamic_core_index: 返回None
- info.get_industry_sw: 返回空DataFrame
- info.get_concept_baidu: 返回空DataFrame
- sentiment.securities_margin: 返回空

## 覆盖率

整体约85-88%。剩余12-15%（机构评级/股东关系/竞争对手/行业市占率）无结构化API。

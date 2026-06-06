# adata API 能力地图（2026-06-03 实测）

> 本文档记录 adata 2.9.5 可用函数及连通性，供后续接入参考。

## 已接入（fetch_market_data.py comprehensive）

| 函数 | 返回 | 连通性 | 备注 |
|------|------|--------|------|
| `stock.finance.get_core_index(stock_code)` | DataFrame 43列×N期 | ✅ 稳定 | 核心财务指标，comprehensive 主力数据 |
| `stock.info.get_stock_shares(stock_code)` | DataFrame 股本变动 | ✅ 稳定 | 总股本/限售/流通，按日期 |
| `stock.info.get_concept_east(stock_code)` | DataFrame 概念板块 | ✅ 稳定 | 东方财富概念归属 |
| `stock.market.get_capital_flow(stock_code)` | DataFrame 资金流向 | ⚠️ 不稳定 | 东方财富接口偶尔断连 |
| `stock.market.get_market(stock_code, start_date)` | DataFrame K线 | ✅ 稳定 | 开/收/高/低/量/额/涨跌幅/换手率 |

## 已验证可用，待接入

| 函数 | 返回 | 连通性 | 对分析的价值 |
|------|------|--------|-------------|
| `sentiment.north.north_flow()` | DataFrame 30日北向资金 | ✅ 稳定 | net_hgt/buy_hgt/sell_hgt + 深股通 + 合计，Step 5 市场情绪 |
| `sentiment.stock_lifting_last_month()` | DataFrame 当月解禁股 | ✅ 稳定（191行） | stock_code/lift_date/volume/amount/ratio/price，Step 5 风险预警 |
| `sentiment.hot.pop_rank_100_east()` | DataFrame 人气榜TOP100 | ✅ 稳定 | rank/stock_code/price/change_pct，Step 5 市场热度 |
| `stock.info.get_plate_east(stock_code)` | DataFrame 板块归属 | ✅ 稳定 | 行业/板块/概念三级分类，Step 3 产业链 |
| `stock.info.index_constituent(index_code)` | DataFrame 指数成分股 | ✅ 稳定（300行） | 沪深300/中证500等，Step 0 指数归属 |

## 已验证但连通性差

| 函数 | 问题 | 备注 |
|------|------|------|
| `stock.market.get_dividend(stock_code)` | `Exceeded 30 redirects` | 东方财富分红页面重定向过多，需换数据源 |
| `stock.info.get_dynamic_core_index(stock_code)` | 返回 None | 可能需要不同参数或已弃用 |
| `stock.info.get_industry_sw(stock_code)` | 返回空 DataFrame | 申万行业接口可能需要行业代码而非股票代码 |
| `stock.info.concept_constituent_east(concept_code)` | ConnectionError | 概念成分股接口不稳定 |

## 未测试

| 函数 | 推测用途 |
|------|---------|
| `sentiment.north.north_flow_current()` | 当日北向资金实时 |
| `sentiment.north.north_flow_min()` | 分钟级北向资金 |
| `sentiment.hot.hot_concept_20_ths()` | 同花顺热门概念TOP20 |
| `sentiment.hot.hot_rank_100_ths()` | 同花顺人气榜TOP100 |
| `sentiment.hot.list_a_list_daily()` | A股每日热度 |
| `stock.info.all_concept_code_east()` | 全部东方财富概念代码 |
| `stock.info.all_concept_code_ths()` | 全部同花顺概念代码 |
| `stock.market.get_market_five(stock_code)` | 五档盘口 |
| `stock.market.get_market_bar(stock_code)` | 盘口数据 |
| `stock.market.east_market()` | 东方财富行情 |
| `stock.market.east_capital_flow()` | 东方财富资金流 |
| `stock.market.baidu_market()` | 百度股市通行情 |
| `stock.market.baidu_capital_flow()` | 百度资金流 |
| `stock.market.sina_market()` | 新浪行情 |
| `stock.market.qq_market()` | 腾讯行情 |

## 使用注意

1. **adata 东方财富接口不稳定**：`get_capital_flow` / `concept_constituent_east` 等可能随机失败，comprehensive 中已做容错处理
2. **sentiment 模块是对象非模块**：`adata.sentiment.north` 是 NorthFlow 对象，需调用其方法（如 `.north_flow()`），不能直接调用对象本身
3. **DataFrame 列名不含 stock_code**：`finance.get_core_index` 返回的列名是 `stock_code`，但 `get_stock_shares` 返回的也是 `stock_code`，可用此列做关联
4. **排序不一致**：有些返回最新在前，有些最新在后，使用前需 `sort_values('date')`

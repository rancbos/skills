# 东方财富宏观数据 API 参考

> 发现日期: 2026-05-27 | 方法: curl 探测 + datacenter-web API 逆向

## 基础信息

- **Base URL**: `https://datacenter-web.eastmoney.com/api/data/v1/get`
- **认证**: 无需 API Key
- **User-Agent**: `Mozilla/5.0` 即可
- **NBS API 替代**: 国家统计局 `data.stats.gov.cn/easyquery.htm` 因 WAF IP 封锁(403 UrlACL)不可用

## 通用请求格式

```
GET /api/data/v1/get?sortColumns=REPORT_DATE&sortTypes=-1&pageSize=N&pageNumber=1&reportName=RPT_ECONOMY_{NAME}&columns=ALL
```

## 已知可用端点

### 1. CPI — 居民消费价格指数
```
reportName: RPT_ECONOMY_CPI
字段:
  REPORT_DATE          → 报告日期
  NATIONAL_SAME        → 全国同比(%)
  NATIONAL_SEQUENTIAL  → 全国环比(%)
  CITY_SAME            → 城市同比(核心CPI代理)
  RURAL_SAME           → 农村同比
```
验证: 2026-04 CPI +1.2% YoY / +0.3% MoM ✅

### 2. PMI — 采购经理人指数
```
reportName: RPT_ECONOMY_PMI
字段:
  REPORT_DATE   → 报告日期
  MAKE_INDEX    → 制造业PMI
  NMAKE_INDEX   → 非制造业PMI
```
验证: 2026-04 制造业 50.3 / 非制造业 49.4 ✅

### 3. GDP — 国内生产总值
```
reportName: RPT_ECONOMY_GDP
字段:
  REPORT_DATE            → 报告日期
  TIME                   → 描述("2026年第1季度")
  DOMESTICL_PRODUCT_BASE → 国内生产总值(亿元)
  SUM_SAME               → 同比(%)
  FIRST/SECOND/THIRD_SAME → 三大产业同比
```
验证: 2026Q1 334,193亿 / +5.0% ✅

### 4. PPI — 工业生产者出厂价格指数
```
reportName: RPT_ECONOMY_PPI
字段:
  REPORT_DATE    → 报告日期
  BASE_SAME      → 同比(%)
  BASE_ACCUMULATE → 累计
```
验证: 2026-04 PPI +2.8% ✅

## 不存在/不可用的端点

以下 reportName 不存在(返回 code:9501):
- RPT_ECONOMY_MONEYSUPPLY (M2)
- RPT_ECONOMY_SOCIALFINANCING (社融)
- RPT_ECONOMY_TRADE (进出口)
- RPT_ECONOMY_FOREX (外汇储备)
- RPT_ECONOMY_INDUSTRY (工业)
- RPT_ECONOMY_RETAIL (零售)
- RPT_ECONOMY_INVEST (投资)
- RPT_ECONOMY_LPR (LPR)

### RPT_ECONOMY_MONEY — 部分可用但无法用于 M2 交叉验证

`reportName=RPT_ECONOMY_MONEY` **可以返回数据**（HTTP 200），但返回字段中**不含 `M2`/`M2_SAME`** 等货币供应量字段。推测该端点返回的是其他货币指标（如公开市场操作），与 Baostock `query_money_supply_data_month` 不兼容。

**结论（2026-05-27 实测）**: 东方财富无法提供 M2 双源交叉验证。M2 当前仅 Baostock 单源，标注"单源待验证"。fetch_macro.py v3.4 中 `_em_m2()` 会返回 None → 触发错误聚合"东方财富 M2 交叉验证源获取失败" — 这是预期行为。

→ M2走Baostock, LPR走中国货币网, 其余走web_search兜底

## 交叉验证（v3.4 现状）

| 指标 | 主源 | 第二源 | 状态 |
|:---|:---|:---|:--:|
| M2 | Baostock | 东方财富 RPT_ECONOMY_MONEY | ❌ 东方财富端点不含M2字段 |
| CPI | 东方财富 | 国家统计局(IP被封) | ⚠️ 单源 |
| PMI | 东方财富 | — | ⚠️ 单源 |
| GDP | 东方财富 | — | ⚠️ 单源 |
| PPI | 东方财富 | — | ⚠️ 单源 |
| LPR | 中国货币网 | — | ⚠️ 单源 |

- 差异阈值: ≤3% 通过（目前仅 M2 尝试双源，但失败）
- fetch_macro.py v3.4 的 `main()` 中 M2 交叉验证代码已接线，若未来东方财富开放 M2 字段则自动生效

## 缓存策略

```
~/.hermes/cache/jw-investment-data/macro/
├── cpi_latest.json   TTL 35d (次月10日发布)
├── pmi_latest.json   TTL 5d  (次月1日发布)
├── gdp_latest.json   TTL 90d (下季度中发布)
├── ppi_latest.json   TTL 35d
├── m2_latest.json    TTL 35d
├── lpr_latest.json   TTL 25d (每月20日发布)
└── _index.json
```

## 已知限制

1. 东方财富 API 不返回 `REPORT_DATE` 超过约20年的历史数据 — 仅适合作最新值查询
2. 接口无频率限制文档 — CSDN文章提到实践中间隔1s安全
3. 字段名可能跨版本变化 — 产生新指标时需先调 columns=ALL 确认字段名

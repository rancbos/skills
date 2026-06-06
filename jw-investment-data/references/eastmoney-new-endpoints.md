# 东方财富新增宏观端点（v3.5.0）

> 发现日期: 2026-06-04 | 方法: curl 探测 RPT_ECONOMY_* 变体名

## 新增可用端点

### 5. 固定资产投资
```
reportName: RPT_ECONOMY_ASSET_INVEST
字段:
  REPORT_DATE     → 报告日期
  BASE            → 当期金额(亿元)
  BASE_SAME       → 累计同比(%)
  BASE_ACCUMULATE → 累计金额(亿元)
验证: 2026-04 累计141293亿 / 同比-12.01% ✅
```

### 6. 工业增加值
```
reportName: RPT_ECONOMY_INDUS_GROW
字段:
  REPORT_DATE     → 报告日期
  BASE_SAME       → 当月同比(%)
  BASE_ACCUMULATE → 累计同比(%)
验证: 2026-04 当月+4.1% / 累计+5.6% ✅
```

### 7. 财政收入
```
reportName: RPT_ECONOMY_INCOME
字段:
  REPORT_DATE     → 报告日期
  BASE            → 累计金额(亿元)
  BASE_SAME       → 累计同比(%)
  BASE_ACCUMULATE → 累计金额(亿元)
验证: 2026-04 累计21791亿 / 同比+6.68% ✅
```

## 确认不可用的端点（与原有文档一致）

| reportName | 结果 |
|-----------|------|
| RPT_ECONOMY_SOCIAL_FINANCING | 403/不存在 |
| RPT_ECONOMY_TRADE | 不存在 |
| RPT_ECONOMY_FOREX | 不存在 |
| RPT_ECONOMY_INVEST | 不存在（用ASSET_INVEST替代） |
| RPT_ECONOMY_RETAIL | 不存在 |
| RPT_ECONOMY_INDUSTRY | 不存在（用INDUS_GROW替代） |

## Jin10 MCP 交叉验证能力

| MCP 工具 | 能验证的指标 | 方式 |
|---------|-------------|------|
| `list_calendar()` | CPI/PMI/GDP/外汇储备 | 返回预期值+前值+实际值 |
| `search_flash("社融")` | 社会融资规模 | 返回最新快讯摘要 |
| `search_flash("M2")` | M2货币供应量 | 返回最新快讯摘要 |
| `search_flash("外汇储备")` | 外汇储备 | 返回最新快讯摘要 |
| `search_flash("进出口")` | 进出口数据 | ⚠️ 返回空结果，不可用 |

## 数据发布时间规律

| 时间段 | 指标 | 发布机构 |
|--------|------|----------|
| 上旬 7-12日 | 进出口数据、外汇储备 | 海关总署、外汇局 |
| 中旬 13-18日 | 社融/货币、固投/工业/房地产/70城房价 | 央行、统计局（通常同日发布） |
| 月末 | PMI(统计局)、LPR(20日) | 统计局、中国货币网 |
| 季度中 | GDP(统计局) | 统计局 |
| 特殊 | 1-2月数据合并发布(3月中旬) | — |

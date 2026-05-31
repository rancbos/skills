# 宏观数据源调研与接入记录

> 调研时间: 2026-05-27 | 版本: v1.0

## 已接入

### 东方财富 API (Phase 2)

**端点**: `https://datacenter-web.eastmoney.com/api/data/v1/get`
**认证**: 无需认证，免费
**格式**: JSON，`{success, result: {data: [...]}}`

| 报表名 | 关键字段 | 频率 |
|--------|---------|:--:|
| `RPT_ECONOMY_CPI` | `NATIONAL_SAME`(同比), `NATIONAL_SEQUENTIAL`(环比) | 月度 |
| `RPT_ECONOMY_PMI` | `MAKE_INDEX`(制造业), `NMAKE_INDEX`(非制造) | 月度 |
| `RPT_ECONOMY_GDP` | `DOMESTICL_PRODUCT_BASE`(亿元), `SUM_SAME`(同比) | 季度 |
| `RPT_ECONOMY_PPI` | `BASE_SAME`(同比) | 月度 |

**调用示例**:
```python
url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
params = "sortColumns=REPORT_DATE&sortTypes=-1&pageSize=3&pageNumber=1&reportName=RPT_ECONOMY_CPI&columns=ALL"
headers = {"User-Agent": "Mozilla/5.0"}
```

### Baostock (Phase 1)

**依赖**: `pip install baostock`
**认证**: 无需注册或API Key，直接 `bs.login()`

| 函数 | 关键字段 | 格式注意 |
|------|---------|---------|
| `query_money_supply_data_month` | M0/M1/M2 总量及同比 | ❗ 日期格式 `yyyy-mm`，非 `yyyy-mm-dd` |
| `query_deposit_rate_data` | 活期/3月/6月/1年 | `yyyy-mm-dd` |
| `query_loan_rate_data` | 6月/1年/5年以上 | `yyyy-mm-dd` |
| `query_required_reserve_ratio_data` | 大型/中小型机构 | `yearType='0'` |

**陷阱**: `login()`/`logout()` 会打印到 stdout，需 `sys.stdout = open(os.devnull, 'w')` 抑制。

## 不可用

### 国家统计局 API (data.stats.gov.cn)

**端点**: `https://data.stats.gov.cn/easyquery.htm`
**阻断原因**: WAF (Web Application Firewall) IP封锁，返回 `403 Forbidden` + `reason:UrlACL`
**尝试过**: 标准User-Agent、Referer头 — 均无效
**替代**: 东方财富API覆盖了CPI/PMI/GDP核心指标

### AkShare 1.18.63 宏观模块

**原因**: 1.18版本重构，全部 `macro_china_*` 函数被移除
**模块列表**: fund, futures, stock, bond, stock_fundamental — 无 macro 模块

## 待接入 (Phase 3)

| 来源 | 方式 | 覆盖 | 成本 |
|------|------|------|:--:|
| FRED | `fredapi` Python包 | 美GDP/CPI/非农/利率 | 免费(需注册API Key) |
| Trading Economics | REST API | 全球宏观仪表盘 | 免费额度有限 |

## 参考文章

- SegmentFault: [宏观数据从哪来？一篇文章理清主流经济数据库与API](https://segmentfault.com/a/1190000047648498)
- DataFocus: [15个免费数据源网站](https://www.datafocus.ai/infos/stayed-up-late-organized-15-super-useful-free-data-source-websites-no-more-fear-of-finding-data)
- CSDN: [宏观数据获取方法汇总](https://blog.csdn.net/2302_79730293/article/details/138867483)

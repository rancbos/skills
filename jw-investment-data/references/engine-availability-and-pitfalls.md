# 引擎实测状态 & 已知陷阱

> 最后更新: 2026-05-27 | jw-investment-data v3.5.0

## 行情引擎可用性矩阵（无代理）

| 引擎 | 状态 | 覆盖市场 | 数据类型 | 失败原因 |
|------|:--:|---------|---------|---------|
| 腾讯 HTTP (qt.gtimg.cn) | ✅ | A/HK | 实时行情 | — |
| Baostock | ✅ | A | K线/财务 EOD | — |
| AkShare 1.18 | ⚠️ | A | 实时行情(腾讯源) | 分页限制(200条) |
| 新浪 HTTPS | ✅ | A/HK | 实时+五档盘口 | — |
| 百度股市通 | ✅ | A | 独立源+盘口 | — |
| Tushare | ✅ | A | T+1/估值 | 需 token |
| 雪球 | ✅ | A | 独立源 | cookie→API 两步法 |
| yfinance | ⚠️ | HK/US | 行情/财务 | 需代理 |
| efinance | ❌ | A/HK | 实时行情 | 东方财富封 IP |

## 宏观数据源可用性矩阵

| 数据源 | 状态 | 指标 | 备注 |
|------|:--:|------|------|
| 东方财富 CPI | ✅ | CPI 同比/环比 | `RPT_ECONOMY_CPI`，`NATIONAL_SAME`/`NATIONAL_SEQUENTIAL` |
| 东方财富 PPI | ✅ | PPI 同比 | `RPT_ECONOMY_PPI`，`BASE_SAME` |
| 东方财富 PMI | ✅ | 制造/非制造 | `RPT_ECONOMY_PMI`，`MAKE_INDEX`/`NMAKE_INDEX` |
| 东方财富 GDP | ✅ | 季度 GDP+三大产业 | `RPT_ECONOMY_GDP`，`SUM_SAME`/`FIRST_SAME`/`SECOND_SAME`/`THIRD_SAME` |
| **东方财富 M2** | **❌** | M2 同比 | `RPT_ECONOMY_MONEY` **不返回 M2_SAME 字段**，交叉验证源不可用 |
| Baostock 货币 | ✅ | M0/M1/M2 月度 | `query_money_supply_data_month()` |
| Baostock 利率 | ⚠️ | 存/贷款利率 | **偶发失败**（返回空数据），非必得 |
| Baostock 准备金 | ⚠️ | 大型/中小型 | **偶发失败**（同利率），非必得 |
| 中国货币网 LPR | ✅ | 1Y/5Y | `chinamoney.com.cn/ags/.../LprHis`，每月 20 日更新 |
| 世界银行 | ✅ | 中美 GDP/CPI 年度 | `api.worldbank.org`，年度数据，TTL 365 天 |
| 国家统计局 | ❌ | 全部 | IP 被 WAF 封锁，403 UrlACL |

## 缓存陷阱

### CPI 缓存丢字段（v3.4.0 修复）

**症状**: `KeyError: 'cpi_mom'`  
**根因**: v3.0 的缓存写入只存了 `period`/`cpi_yoy`/`source`，丢弃了 `cpi_mom`（环比）。第二次调用命中缓存时缺少环比字段。  
**修复**: v3.4.0 缓存写入加入 `cpi_mom` 字段（`cpi.get("cpi_mom")`），markdown 格式化改为 `.get("cpi_mom", 0)` 防崩。

### 交叉验证缓存未正常写入

**症状**: `_verifications` 段始终只有单源标注。  
**根因**: v3.0-v3.3 的 `_verify_two_source()` 和 `_verify_single()` 函数定义了但从未被 `main()` 调用。M2 交叉验证数据写入 `money["cross_source"]` 而非统一的 `_verifications` 缓存。  
**修复**: v3.4.0 重写 `main()` 末尾的验证汇总逻辑，M2 双源对比结果正确写入 `_verifications`。

## 引擎特定陷阱

### 腾讯 qt.gtimg.cn 接口

1. **GBK 编码**：返回非 UTF-8，subprocess 必须 `capture_output=True` + `decode('gbk')`
2. 不可用 `text=True`，否则 UnicodeDecodeError
3. A股前缀：60/68/9 → `sh`，其他 → `sz`；港股前缀：`hk`
4. 响应格式：`v_sh600519="1~名称~代码~现价~昨收~今开~成交量..."`
5. 解析用 `~` 分割，关键索引：f[3]=现价, f[4]=昨收, f[31]=涨跌额, f[32]=涨跌幅%

### Baostock 注意事项

1. **login/logout 打印污染**：必须用 `sys.stdout=open(os.devnull,'w')` 包裹
2. 只支持 A 股（无港股/美股），数据偏历史（EOD）非实时
3. 代码格式：`sh.600519` / `sz.000001`；返回迭代器模式 `while rs.next()`
4. **宏观接口偶发空返回**：利率和准备金率查询可能在无报错情况下返回空结果——脚本已做防御处理（`else: _record_error(...)`）

### AkShare 1.18.63 迁移备忘

- `ak.stock_zh_a_spot_em()` → `from akshare.stock.stock_zh_a_tx import stock_zh_a_spot_tx`
- code 格式: `600519` → `sh600519` / `sz000001`
- 返回列名: `最新价` → `zxj` / `涨跌幅` → `zdf` / `总市值` → `zsz`
- 分页限制: 200条/次，`offset` 分页参数

### yfinance 1.4.0 proxy 适配

```python
import yfinance, requests
session = requests.Session()
session.proxies = {"http": PROXY_URL, "https": PROXY_URL}
tk = yfinance.Ticker("AAPL", session=session)
```

### 东方财富 API 字段名陷阱

- CPI 环比字段叫 `NATIONAL_SEQUENTIAL`（不是 `MOM`）
- CPI 同比字段叫 `NATIONAL_SAME`（不是 `YOY`）
- GDP 总量字段叫 `DOMESTICL_PRODUCT_BASE`（拼写错误保留在 API 中，`DOMESTICL` 缺少 A）
- M2 接口 `RPT_ECONOMY_MONEY` 返回的字段名可能不包含 `M2_SAME`——已验证不可用

## 版本号一致性检查（v3.5.0）

脚本应统一使用 `__version__` 变量（而非 `VERSION`），且与 SKILL.md frontmatter 中的 `version` 字段一致。v3.5.0 状态：

| 脚本 | __version__ | --schema | 状态 |
|:---|:---|:--:|:--:|
| fetch_macro.py | 3.4.1 | ✅ | ✅ |
| health_check.py | 1.0.0 | ✅ | ✅ v3.5.0 新增 |
| format_macro.py | 1.0.0 | ❌ | ✅ v3.5.0 新增（内部模块，不需要 --schema） |
| jw-data | 1.0.0 | ✅ | ✅ v3.5.0 新增（shell wrapper, schema 通过 `jw-data schema`） |
| fetch_market_data.py | 3.0.0 (VERSION=) | ✅ | ⚠️ 旧式 VERSION 变量，待迁移 |
| technical_indicators.py | 2.0.0 | ✅ | ⚠️ 版本落后，待升 |
| draw_kline.py | 2.0.0 | ✅ | ⚠️ 版本落后，待升 |
| circuit_breaker.py | — | ❌ | 内部模块，不需要 |
| market_clock.py | — | ❌ | 内部模块，不需要 |
| output_contract.py | — | ❌ | 内部模块，不需要 |

### 健康检查发现（v3.5.0）

`health_check.py` 首次运行时确认：
- ✅ 东方财富 CPI/PMI/GDP/PPI — 全部正常
- ❌ 东方财富 M2 (`RPT_ECONOMY_MONEY`) — 端点可通但数据为空（null），无法作为交叉验证源
- ✅ 中国货币网 LPR — 正常
- ✅ 世界银行 — 正常
- ✅ Baostock 登录+货币数据 — 正常
- ⚠️ Baostock 利率/准备金 — 脚本中有 `_record_error` 兜底（偶发失败）

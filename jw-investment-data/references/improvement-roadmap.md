# jw-investment-data 改善路线图

> 最后更新: 2026-05-27 | 当前版本: v3.5.0

## 已完成（v3.0 → v3.5.0）

| 版本 | 内容 |
|:---|:---|
| v3.5.0 | ⚙️ TTL配置化(engines.yaml) + 📐 版本统一(draw_kline/tech_ind) + 📄 format_market拆分 + 🏷️ circuit_breaker --schema + 📐 全脚本 --version 标志 + 🏥 健康检查 + 📄 format_macro独立 + 🚪 统一入口(jw-data) + 🔪 死代码清理 + 📚 文档精简 |
| v3.4.1 | 🔪 砍死代码：fetch_stock.py/fetch_financial.py/data_validator.py → 10→7脚本；17→7参考文档 |
| v3.4.0 | 📋 SKILL.md 重写（Usage导向）+ 交叉验证接线 + M2双源对比 + 日历去硬编码 + 错误聚合 + LPR独立 + 版本统一 |
| v3.3 | 宏观全系：LPR(中国货币网) + 世界银行(中美背景) + Jin10 美国快讯 |
| v3.2 | 东方财富 API 接入：CPI/PMI/GDP/PPI |
| v3.1 | 宏观 Phase 1：Baostock M0/M1/M2/利率/准备金 + 本地缓存 |
| v3.0 | 熔断器 + 交易时钟 + 标准信封 + --force |
| v2.x | 置信度体系 + Markdown输出 + --schema + YAML配置 + 多引擎接入 |

## 进行中 / 部分完成

### 交叉验证（v3.4.0 部分接线）

| 指标 | 主源 | 验证源 | 状态 |
|:---|:---|:---|:--:|
| M2 | Baostock | 东方财富 RPT_ECONOMY_MONEY | ⚠️ 已验证：东财端点不返回 M2_SAME，无法对比 |
| CPI | 东方财富 | — | ⚠️ 单源，待第二源 |
| PMI | 东方财富 | — | ⚠️ 单源，待第二源 |
| GDP | 东方财富 | — | ⚠️ 单源，待第二源 |
| PPI | 东方财富 | — | ⚠️ 单源，待第二源 |

### 美国宏观

| 方案 | 状态 |
|:---|:---|
| FRED API | ⏳ 需免费 API Key 注册 |
| 世界银行年度数据 | ✅ 已接入（但年度滞后，非实时） |
| Jin10 MCP 快讯搜索 | ✅ Agent 侧实时查询 |

## 待办（优先级排序）

### 🔴 P0 — 数据源恢复

1. **M2 交叉验证源**：东方财富 `RPT_ECONOMY_MONEY` 不可用（health_check 确认）→ 寻找替代源（中国人民银行官网 / Wind 免费接口）
2. **CPI/PMI/GDP/PPI 第二源**：目前全依赖东方财富单源，需要一个独立验证源。候选：国家统计局 API（需解决 IP 封锁）/ 新浪财经宏观频道

### 🟡 P1 — 架构改善

3. **FRED 美国宏观**：需免费 API Key 注册
4. **Baostock 利率/准备金偶发失败**：降级方案或重试逻辑
5. **`format_market.py` 引擎名表不完整**：当前只覆盖腾讯/新浪/Baostock/AkShare/yfinance/efinance，缺失百度/Tushare/雪球

## 数据源全景（当前状态）

| 类别 | 来源 | 指标 | 认证 | 状态 |
|:---|:---|:---|:--:|:--:|
| 宏观 | 东方财富 API | CPI/PMI/GDP/PPI | ❌ | ✅ |
| 宏观 | Baostock | M0/M1/M2/利率/准备金 | ❌ | ✅（利率/准备金偶发失败） |
| 宏观 | 中国货币网 | LPR 1Y/5Y | ❌ | ✅ |
| 宏观 | 世界银行 | 中美 GDP/CPI 年度 | ❌ | ✅ |
| 宏观 | Jin10 MCP | 日历+美国快讯 | ❌ | ✅（Agent侧实时） |
| 行情 | 腾讯/新浪/百度/AkShare/雪球/Tushare | A股实时+K线 | ❌ | ✅ |
| 行情 | yfinance | 港美股 | ❌ | ⚠️ 需代理 |
| 行情 | efinance | 东方财富 | ❌ | ❌ 封 IP |
| 宏观 | 国家统计局 | 全部 | ❌ | ❌ IP WAF 封锁 |
| 宏观 | FRED | 美国宏观 | 免费注册 | ⏳ |

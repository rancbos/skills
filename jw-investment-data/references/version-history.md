# 版本历史

## 更新日志

**v3.9.0 — comprehensive 增强：18个数据源**
- 🏆 comprehensive 从11源扩展到18源：+concept_ths（同花顺概念）+hot_concept（热门概念TOP20）+hot_rank（热门股TOP100）+market_five（五档盘口）+north_flow_current（北向实时）+daily_movers（每日异动）+rates（贷款/存款利率，baostock数据暂不可用）
- 📊 公司分析量化数据覆盖率从80%提升至88%
- 🔧 新增7个helper函数，修复pandas Timestamp序列化问题

**v3.8.0 — comprehensive 增强：11个数据源**
- 🏆 comprehensive 从6源扩展到11源：+plate（行业/板块归属）+north_flow（北向资金30日）+stock_lifting（当月解禁）+popularity（人气榜TOP100）+index_membership（指数成分：沪深300/中证500/上证50/创业板指）
- 📊 公司分析量化数据覆盖率从70%提升至80%+
- 🔧 新增6个helper函数：`_adata_plate`/`_adata_north_flow`/`_adata_stock_lifting`/`_adata_popularity`/`_adata_index_membership`

**v3.7.0 — 综合财务画像 + 资金流向 + adata引擎**
- 🏆 comprehensive 新增：`--category comprehensive` 一次调用返回 adata财务43列×20期 + baostock业绩预告/快报/营运能力 + 股本结构变动 + 概念板块
- 💰 capital_flow 新增：`--category capital_flow` 返回30天资金流向（主力/大单/中单/小单/超大单）
- 🔧 adata 引擎接入：`adata.stock.finance.get_core_index`（43列完整财务）、`adata.stock.info.get_stock_shares`（股本变动）、`adata.stock.info.get_concept_east`（概念板块）、`adata.stock.market.get_capital_flow`（资金流向）
- 🔧 baostock 新增3个查询：`query_forecast_report`（业绩预告）、`query_performance_express_report`（业绩快报）、`query_operation_data`（营运能力）
- 📐 schema 更新：comprehensive + capital_flow 类别加入

**v3.6.0 — 5年多维财务 + 公司概况**
- 📊 financial 增强：`_baostock_financial()` 从单期利润表升级为5年×6维查询（profit+balance+cashflow+dupont+growth+dividend），返回结构化JSON含summary摘要
- 🏢 profile 新增：`--category profile` 获取公司概况（基本信息+行业分类+最近4季财务摘要）
- 🔧 修复 `query_cash_flow` → `query_cash_flow_data`（baostock正确函数名）
- 📐 schema 更新：financial描述更新 + profile类别加入

**v3.5.0 — 全面像素级优化**
- ⚙️ TTL 配置化：`engines.yaml` → `macro.cache` 段，修改 TTL 不再需要改源码
- 📐 版本统一：`draw_kline.py` / `technical_indicators.py` 改用 `__version__`
- 📄 双 Formatter：`format_macro.py` + `format_market.py`，数据采集和展示完全分离
- 🏷️ circuit_breaker 加 `--schema`：所有用户可调用模块均已自描述
- 🏥 健康检查：`health_check.py` — 9源并行扫描，1.5s 出结果
- 🚪 统一入口：`jw-data` — 一个命令，`jw-data macro cpi` = `python fetch_macro.py --category cpi`
- 🔪 死代码清理：删 `fetch_stock/fetch_financial/data_validator`，10→10（+3 -3）
- 📚 文档精简：17 references → 7 活 + 10 归档，移除虚设 JQData 章节
- 🔍 交叉验证：M2 双源对比实时接线，日历去硬编码改 MCP 动态提示
- ❌ 错误聚合：API 失败不再静默吞，JSON 和 Markdown 均可见
- 脚本：10 → **10**（替换为更高质量）

**v3.4.1**
- 🔪 砍掉死代码：`fetch_stock.py`、`fetch_financial.py`、`data_validator.py` — fetch_market_data.py 已覆盖全部功能
- 脚本从 10 个精简到 7 个

**v3.4.0 (2026-05-27)**
- SKILL.md 重写：Usage 段前置，changelog 压缩
- 脚本合并：mydata 脚本全部移入 `scripts/`，旧目录清理
- 版本统一：全栈 `__version__ = "3.4.0"`
- 交叉验证接线：M2 部署 Baostock vs 东财双源对比（`--category money` 自动触发）
- 日历去硬编码：`_calendar_hint()` / `_us_macro_hint()` 改为 MCP 实时查询提示
- 错误聚合：`main()` 收集所有 API 失败 → `_errors` 段 + Markdown 错误节
- LPR 独立：新增 `--category lpr` 选项
- 世界银行缓存 TTL → 365天

**v3.3.0** — 宏观全系：+LPR +世界银行 + Jin10 美国快讯

**v3.2.0** — 东方财富 API 接入：CPI/PMI/GDP/PPI

**v3.1.0** — 宏观数据模块上线：Baostock 货币/利率/准备金 + 缓存

**v3.0.0** — 熔断降级 + 交易时钟 + 标准信封 + `--force`

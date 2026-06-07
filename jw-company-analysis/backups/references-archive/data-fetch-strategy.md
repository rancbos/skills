# 取数策略详细表

> 本文档是 jw-company-analysis 概览区"分层取数策略"的完整版本。Agent 执行时只需参考 SKILL.md 中的精简版本，本文档供人类查阅。

## 数据层完整映射

| 数据层 | 主源 | 覆盖Step | 说明 |
|--------|------|---------|------|
| 股价/行情 | `jw-investment-data` quote（6源交叉验证✅） | Step 0, 8 | 9秒内出结果，置信度高 |
| 技术指标 | `jw-investment-data` indicators（MA/MACD/RSI/Boll✅） | Step 6 | 0.5秒，全部覆盖 |
| K线图 | `jw-investment-data` chart/kline | Step 6 | PNG输出 |
| 宏观数据 | `jw-investment-data` fetch_macro（CPI/PMI/GDP/M2✅） | Step 0.6 | 缓存机制，秒级响应 |
| 财务数据 | `jw-investment-data` comprehensive（adata 43列+baostock预告/快报/营运✅） + financial（5年×6维✅） | Step 2 | **覆盖85%+**：EPS/营收/净利/ROE/毛利率/净利率/现金流/负债率/周转率/业绩预告/营运能力 |
| 公司概况 | `jw-investment-data` profile（基本信息+行业+4季摘要✅） | Step 0 | 上市日期/行业分类/最近4季ROE/毛利率/净利润 |
| 股本结构 | `jw-investment-data` comprehensive→shares（股本变动历史✅） | Step 0 | 总股本/限售股/流通股/变动日期 |
| 概念板块 | `jw-investment-data` comprehensive→concept（东方财富概念✅） | Step 3 | 概念板块归属 |
| 行业/板块归属 | `jw-investment-data` comprehensive→plate（行业+板块+概念✅） | Step 0,3 | 行业分类/地域板块/概念板块（28项+） |
| 指数成分 | `jw-investment-data` comprehensive→index_membership（✅） | Step 0 | 沪深300/中证500/上证50/创业板指 |
| 解禁风险 | `jw-investment-data` comprehensive→stock_lifting（✅） | Step 5 | 当月解禁股数据（代码/日期/数量/金额/比例） |
| 北向资金 | `jw-investment-data` comprehensive→north_flow（✅） | Step 5 | 沪股通/深股通30日净流入 |
| 同花顺概念 | `jw-investment-data` comprehensive→concept_ths（✅） | Step 3 | 同花顺概念板块（减速器/机器人/新能源汽车等） |
| 热门概念 | `jw-investment-data` comprehensive→hot_concept（✅） | Step 5 | 同花顺热门概念TOP20（市场情绪/板块轮动） |
| 热门股 | `jw-investment-data` comprehensive→hot_rank（✅） | Step 6 | 同花顺热门股TOP100（市场热度） |
| 五档盘口 | `jw-investment-data` comprehensive→market_five（✅） | Step 6 | 买卖5档价格+数量 |
| 北向资金实时 | `jw-investment-data` comprehensive→north_flow_current（✅） | Step 5 | 当日实时沪/深/合计净流入 |
| 每日异动 | `jw-investment-data` comprehensive→daily_movers（✅） | Step 5 | 每日异动股列表（龙虎榜/涨跌幅异常） |
| 资金流向 | `jw-investment-data` capital_flow（主力/大单/中单✅） | Step 6 | 30天资金净流入 |
| 定性数据 | web search（必须） | Step 1, 3, 5 | 管理层/事件/行业/竞争对手——API无法覆盖 |
| 估值/机构预测 | web search + 脚本计算 | Step 4 | PE分位/DCF参数/机构目标价 |

## 分层策略

- **量化层**（脚本）：股价/K线/技术指标/宏观/财务/公司概况 → 覆盖 Step 0, 0.5, 0.6, 2, 6, 8
- **定性层**（web search）：管理层/事件/行业/竞争对手/机构预测 → 覆盖 Step 1, 3, 4, 5
- **原则**：脚本能获取的数据优先用脚本（结构化+可验证），web search 做定性补充和交叉验证

## 数据覆盖率

comprehensive 11源已覆盖85-88%量化数据，剩余12-15%（机构评级/股东关系/竞争对手/行业市占率）依赖非公开数据源，web search 是唯一途径。详见 `jw-investment-data/references/adata-capability-map.md`。

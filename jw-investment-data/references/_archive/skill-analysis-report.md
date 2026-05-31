# 20+ 投研数据 Skill 分析报告

> 来源：2026-05-27 对 `/root/mydata/skills---/投研数据/` 的全面分析
> 版本：v2.0（含分析逻辑扩充）

## 一、数据源总览

| 数据源 | 类型 | 认证 | 覆盖市场 | 特征 |
|--------|------|:--:|---------|------|
| Baostock | Python库 | ❌ | A股 | EOD、免费、无需Token |
| AkShare | Python库 | ❌ | 多市场 | 免费、聚合东财/新浪/腾讯 |
| Tushare Pro | HTTP API | ✅ | A股/港股/美股 | 最全、T+1、频率限制 |
| 聚宽 | Python SDK | ✅ | A股 | 因子数据、量化策略 |
| 大虾皮 | CLI工具 | ✅ | A股 | 市场温度/选股/新闻 |
| 腾讯财经 | HTTP | ❌ | A股 | 实时行情 `qt.gtimg.cn` |
| 新浪财经 | HTTP | ❌ | A股/港股 | 实时+五档盘口 |
| Yahoo Finance | HTTP | ❌(需代理) | 美股 | 免费、全球 |
| 通达信 | 本地客户端 | ❌(需客户端) | 多市场 | 实时/公式选股/交易 |
| sc-proxy | 透明代理 | ✅ 按次 | A股 | cn-stock底层 |

## 二、调用方式分类

1. **Python原生导入**：baostock/tushare/jqdatasdk/akshare
2. **HTTP裸调**：腾讯/新浪/daxiapi
3. **MCP协议**：stock-mcp-query/stock-datasource
4. **透明代理**：cn-stock → sc-proxy → Tushare
5. **CLI包装**：daxiapi / stock-data-fetcher
6. **WebSocket**：stock-rt-subscribe

## 三、取数架构值得借鉴的模式

### 3.1 多源降级链 + 熔断器（stock-data-acquisition）
P0(3s) → P1(5s) → P2(10s) → P3(兜底)
CLOSED→OPEN→HALF_OPEN 三态

### 3.2 时间锚定宪法（stock-data-acquisition）
北京时间 → 市场状态(盘前/盘中/午间/收盘/假日) → 动态TTL(盘中5min/盘后24h)

### 3.3 输出契约标准化（cn-stock）
`{ok: bool, source: str, data: <payload>, error: {code, message, retryable}, ts: int}`

### 3.4 自描述脚本（daisy-financial-research）
`--schema` / `--dry-run` / `--format json|table` / exit 0-5

### 3.5 LRU缓存+增量更新（stock-backtest-simulator）
`cache_key = f"{symbol}_{strategy}_{data_end_date}"`

### 3.6 熔断器持久化（stock-data-acquisition）
状态持久化到 JSON，跨会话续接

## 四、分析逻辑值得借鉴的模式

### 4.1 多智能体辩论（daisy debate_runner）
- Bull→Bear→Synthesis / Aggressive→Conservative→Neutral→PortfolioManager
- 强制引述对方论点（避免平行独白）
- 结构化输出：Rating/Thesis/What-would-change/Risks/Holding
- 轮次上限防无限循环，不超过3轮

### 4.2 跨会话决策日志（daisy dexter_memory_log）
- record→resolve→backtest→context 完整闭环
- 回测指标：per-rating mean/hit-rate/t-stat/annualized/Sortino/cumulative alpha+drawdown
- 决策级alpha而非组合NAV
- auto-resolve批量结算pending条目

### 4.3 多因子筛选（daisy screen_a_share）
- 三层过滤：硬过滤→百分位打分→红线扫描
- red_flags()：ST/负PE/零股息/异常换手/商誉炸弹/高质押
- reason()：每只入选股解释为什么入选

### 4.4 可转债分析（a-share-convertible-bond）
- 三模式分发：个债/策略筛选/市场全景
- 双风格输出：formal(研报) vs brief(快速)
- 公式外显原则：展示中间步骤便于验证

### 4.5 57检查点体系（stock-data-acquisition）
- CP = 前提条件 + 验证代码 + 失败处理
- 按模块分层，每层独立可测

## 五、已落地的改进

| 改进 | 目标Skill | 版本 |
|------|----------|------|
| 熔断器+降级链 | jw-investment-data | v3.0 |
| 交易时段感知缓存 | jw-investment-data | v3.0 |
| 标准输出信封 | jw-investment-data | v3.0 |
| 脚本--schema自描述 | jw-investment-data | v3.0 |
| K线增量缓存 | jw-investment-data | v3.0 |
| 标准化来源标注块 | jw-investment-data | v3.0 |
| 红线扫描+检查点 | jw-stock-value-analyzer | v1.7 |
| 辩论双视角 | jw-stock-value-analyzer | v1.7 |
| 决策记忆日志 | jw-stock-value-analyzer | v1.7 |
| 结构化输出升级 | jw-stock-value-analyzer | v1.7 |
| 回测统计 | jw-stock-value-analyzer | v1.7 |

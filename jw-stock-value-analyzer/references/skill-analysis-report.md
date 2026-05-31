# jw-stock-value-analyzer 参考技能分析报告

> 分析时间: 2026-05-27 | 版本: v1.0

## 数据源处理层 (来自 20+ 参考skill)

### 三源交叉校验 (来自 reference skills)
- 交易所直连 (腾讯/新浪/AkShare) — 共享上游
- 独立数据库 (Baostock/Tushare/雪球) — 完全独立
- 百度股市通 (adata) — 第五独立源
- 源独立性标注: `N源(M独立)` 格式

### 熔断器 (来自 stock-data-acquisition 模块二)
- CLOSED → 3次连续失败 → OPEN → 600s后半开探测 → CLOSED
- 状态持久化到 `~/.hermes/cache/circuit_breakers.json`

### 交易时钟 (来自 stock-data-acquisition 模块一+三)
- 北京时间 → 市场状态 (盘前/盘中/午间/收盘/周末/假日)
- 动态缓存 TTL (盘中5min / 盘后24h)

### 标准信封 (来自 cn-stock)
- `{ok, source, data, error: {code, message, retryable}, ts}`

## 分析逻辑层

### 红线扫描 (来自 daisy screen_a_share red_flags)
- ST/负PE/杠杆ROE/商誉炸弹/高质押/现金流/换手率 10项
- 一票否决 → 结论降级

### 辩论双视角 (来自 daisy debate_runner)
- Bull→Bear→Synthesis 三轮对抗
- 强制引述对方论点
- 5段固定输出: Rating/Thesis/What-would-change/Risks/Holding

### 决策记忆日志 (来自 daisy dexter_memory_log)
- record→resolve→backtest→context 闭环
- 追加式 Markdown, `<!-- ENTRY_END -->` 分隔
- 回测指标: per-rating mean_alpha/hit_rate/t-stat/Sortino

### 检查点体系 (来自 stock-data-acquisition)
- CP1-CP7 分析前校验
- 任一 danger 级红线 → 结论降级
- ≥2检查点未通过 → 置信度降级

## 输出结构层

### 三档深度 (来自 daisy + a-share-convertible-bond)
- brief (速览) → standard (标准) → deep (深度报告)
- 自动判断机制: 用户措辞 → 输出模式

### 标准化来源块 (来自 akshare-stock)
- 5行固定格式: 数据来源/分析时间/市场状态/独立校验/工具版本

### 能力边界声明 (来自 cn-stock)
- "本分析不覆盖" 章节
- 明确声明不做技术面/短期时机判断/衍生品评估

### 可视化评分卡 (来自 daisy screen_a_share)
- 维度 | 评分 | 权重 | 贡献 | 一句话
- 替换扁平评分表

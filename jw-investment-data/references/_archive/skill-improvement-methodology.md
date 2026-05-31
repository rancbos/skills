# 参考 Skill 研究方法论

> 在本会话中反复使用的系统化方法论。用于 jw-investment-data v3.0-v3.3 和 jw-stock-value-analyzer v1.7-v1.8 的优化，共研究 20+ 投研 skill。

## 四维度分析框架

对每个参考 skill，从四个维度提取可借鉴点：

| 维度 | 关注点 | 产出物 |
|------|--------|--------|
| **数据源** | 用什么数据、从哪来、怎么取的 | 数据源矩阵、调用方式分类 |
| **调用方式** | API 类型、认证机制、容错设计 | 模式分类(Python import/HTTP/MCP/CLI) |
| **分析逻辑** | 数据处理方式、思考框架、决策机制 | 可复用分析范式 |
| **输出结构** | 格式、呈现、深度分级、读者体验 | 输出模板、标注规范 |

## 实施流程

```
1. 批量加载 → 通读 20+ SKILL.md + 关键脚本
2. 四维提取 → 矩阵归纳（数据源/调用/分析/输出）
3. 优先级排序 → 🔴高(立即可行) 🟡中(架构改进) 🟢低(远期)
4. 依次落地 → 先复用小模块 → 再改造核心脚本 → 后更新文档
5. 交叉验证 → 每个改进追溯对标 skill，确保不跑偏
```

## 本会话已完成的改进

| 轮次 | 改进内容 | 参考来源 |
|:--:|------|------|
| 1 | 熔断器+交易时钟+标准信封 | stock-data-acquisition + cn-stock |
| 2 | --schema自描述+K线缓存+来源标注块 | daisy-financial + akshare-stock |
| 3 | 红线扫描+检查点+决策日志+辩论 | daisy screen_a_share + debate_runner + dexter_memory_log |
| 4 | 三档输出+图标+评分卡+能力边界 | daisy §6-7 + akshare-stock + cn-stock + convertible-bond |
| 5 | 宏观数据模块 Phase 1-3 | segmentfault + datafocus + 东方财富逆向 + 世界银行 API |

# 空计划回退 — summary_plan.json 全空时的阶段 3 策略

## 触发条件

`summary_plan.json` 同时满足：
- `recommended_units` 为空数组 `[]`
- `appendix_units` 为空数组 `[]`
- `excluded_or_weak` 包含全部候选

## 不触发的条件

- 任何 `recommended_units` 或 `appendix_units` 有内容 → 走正常流程
- `summary_plan.json` 不存在 → 走旧规则（cluster数 ≤10 全展开）

## 根因分析

通常由 `validate_candidates.py` 的格式字段缺失导致全 D 评分：

| 惩罚项 | 扣分 | 含义 |
|--------|------|------|
| `missing_source_quote` | -30 | execute_code 提取的候选只有 R 段内容，没有 `source_quote`（带行号的代码块） |
| `v3_not_passed` | -30 | 候选未走 v3 校验管道 |
| `missing_or_invalid_source_line` | -15 | 缺少 `source_chapter`/`source_line` 字段 |
| `missing_v3_reason` | -10 | v3 不通过时缺少原因说明 |
| `empty_related` | -5 | 缺少关联候选 ID |

前三项（合计 -75 分）是**格式层面的元数据缺失**，与候选人正文（R/I/A1/A2/E/P/B）的内容质量无关。

**判断格式问题的信号**：`candidate_scores.json` 的 penalties 集中在 `missing_source_quote`、`v3_not_passed`、`missing_or_invalid_source_line`，而 `missing_v2_scenario`（场景缺失）、`missing_evidence`（证据缺失）等实质性缺失的惩罚不存在 → 高度确认是格式问题。

## 回退流程（5 步）

### 1. 读全部候选人文件

读取 `candidates/` 下的所有 `.md` 文件（通常 7 个：frameworks/principles/cases/boundaries/glossary/insights/procedures.md，总计 ≤100KB）。不凭 `summary_plan.json` 做筛选——它已被 D 级评分污染。

### 2. 验证内容可用性

逐候选抽查：是否有 R 引用文段？是否有 I 含义解释？是否有 A1 案例？是否有 A2 场景？是否有 E/P/B 段？

如果抽查通过（≥80% 候选七段完整），则确认内容可用，进入步骤 3。

### 3. 按主题手动编组

37 个单成员 cluster 需要合并为 12-16 个方法论主题组。编组原则：
- 紧密相关的方法论可以合并（如"便宜是硬道理"和"安全边际"可编入同组）
- 每个主题组产出 1 个完整七段展开
- 术语类候选归入术语表（附录A）
- 实操方法类候选归入方法摘要（附录B）
- 补充框架类候选归入额外附录

### 4. 撰写 SUMMARY.md

按五问 + 核心方法论 + 附录 + 审计的结构撰写。每个方法论单元确保 R/I/A1/A2/E/P/B 七段完整，原文引用 ≤150 字，标注出处章节。

### 5. 审计区记录

在 `SUMMARY.md` 的审计信息中说明：
- pipeline 打分情况（全 D、原因分析）
- 人工复审结论（内容可用、格式字段缺失不影响内容质量）
- 编组逻辑（37→16 的合并映射）

## 相关案例

- 《投资中最简单的事》（邱国鹭，2020）：37 候选全 D 级（pipeline_phase2.py），人工复审确认所有七段完整，产出 16 个方法论单元 + 术语表 + 实操摘要 + 行业轮动框架附录。SUMMARY.md 49,946 bytes。

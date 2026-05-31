# Quality Gates — v4.4 候选质量闸门

本文件定义 `jw-content-summary` 阶段 2 → 阶段 3 之间的确定性质量门。目标不是替代判断，而是把候选质量、聚类质量和 SUMMARY 选题计划暴露成可审计数据，避免靠 agent 体感决定“质量还行”。

## 核心原则

1. 脚本只给信号，不自动删除候选。
2. 低分候选不等于无价值；它可能需要补证、降级到附录，或返回阶段 2 重提取。
3. 用户闸门确认的是“决策包”，不是孤立的数量统计。
4. 阶段 3 写作优先服从 `summary_plan.json`，必要时才回看 candidates 正文。

## v4.4 脚本链路

阶段 2 子代理完成后，按顺序运行：

```bash
python ~/.hermes/skills/jw-content-summary/scripts/validate_candidates.py \
  books/<书名>/candidates

python ~/.hermes/skills/jw-content-summary/scripts/cluster_candidates.py \
  books/<书名>/candidates \
  books/<书名>/clusters.json

python ~/.hermes/skills/jw-content-summary/scripts/score_candidates.py \
  books/<书名>/candidates \
  books/<书名>/clusters.json \
  books/<书名>/candidate_scores.json

python ~/.hermes/skills/jw-content-summary/scripts/build_summary_plan.py \
  books/<书名>/clusters.json \
  books/<书名>/candidate_scores.json \
  books/<书名>/summary_plan.json
```

如要强制检查最新 extractor 字段：

```bash
python ~/.hermes/skills/jw-content-summary/scripts/validate_candidates.py \
  --strict books/<书名>/candidates
```

## validate_candidates.py

检查内容：

- 必要字段是否存在。
- `source_quote` 是否 ≤150 字。
- `v3_pass` 是否为布尔值。
- 常见字段别名是否误用。
- v4.4 质量字段：`source_line`、`related`。

默认模式：
- 旧候选档案缺 `source_line` / `related` 时只 warning。
- 适合历史回放或不想打断流程的场景。

strict 模式：
- 缺 `source_line` / `related` 直接失败。
- 适合新书正式流程。

## cluster_candidates.py

v4.4 不再只按标题聚类，而是综合：

| 信号 | 权重 | 作用 |
|---|---:|---|
| title similarity | 40% | 捕捉同名/近名方法论 |
| keyword overlap | 30% | 捕捉语义接近但标题不同的候选 |
| related overlap | 15% | 使用 extractor 显式交叉引用 |
| summary token overlap | 15% | 辅助判断主题相近 |

输出新增：

- `quality.single_member_ratio`
- `quality.suggested_merge_count`
- `quality.suspicious_similarity_count`
- cluster 内 `merge_evidence`
- cluster 内 `warnings`

注意：
- suggested_merge 只是提示，不自动合并。
- 单成员 ratio 高说明候选高度离散，阶段3可能需要更多聚类工作。

## validate_candidates.py 输出误解备忘

`total_entries` 字段含义：**格式校验失败的条目数**，不是候选总数。

- `ok: true` + `total_entries: 0` = 无格式违规，pipeline 正常
- 实际候选数量看 `score_candidates.py` 输出的 `candidate_count`
- `format_mismatches` 数组才是具体哪些字段出问题

## 全C（0 A/B）时 build_summary_plan 的推荐决策

`methodology_treatise` 类型书籍候选覆盖均匀时，所有候选可能同为 60 分（C 级）。此时 `summary_plan.json` 输出 `recommended=0, appendix=ALL, weak=N`，这是**正常输出，不是错误**。

闸门2决策规则：
- **继续阶段3**：以附录池为主，SUMMARY 从池中精选核心单元
- **不重新提取**：重跑同质候选无意义
- **不要求用户选择**：脚本决策已做，用户只确认方向

建议重启条件（才值得重新提取）：
- A级候选占比 ≥ 20%
- `candidate_count > 100` 且 `single_member_ratio < 0.5`

## build_summary_plan.py

生成 `candidate_scores.json`。

基础 100 分，常见扣分：

| 问题 | 扣分 |
|---|---:|
| 缺 source_quote | -30 |
| source_quote >150 字 | -20 |
| 缺或无效 source_line | -15 |
| v3_pass 未通过 | -30 |
| 缺 v3_reason | -10 |
| 缺 v2_scenario（适用类型） | -10 |
| v1_status weak/failed | -15 |
| related 为空 | -5 |
| 所在 cluster 为单成员 | -5 |

分级：

| 等级 | 分数 | 默认处理 |
|---|---:|---|
| A | ≥85 | 优先进入 SUMMARY 完整七段 |
| B | 70-84 | 可进入 SUMMARY，注意补边界 |
| C | 55-69 | 附录或补证后再写 |
| D | <55 | 默认不展开，返回阶段 2 或 rejected |

## build_summary_plan.py

生成 `summary_plan.json`，把 clusters + scores 转成阶段 3 写作计划。

核心字段：

- `recommended_units`: 建议完整展开的 Top A/B cluster。
- `appendix_units`: 可简写或放附录的 B/C cluster。
- `excluded_or_weak`: 不建议展开或需补证的 cluster。
- `gate_questions`: 闸门 2 给用户的决策问题。

阶段 3 原则：
- 优先读 `summary_plan.json`。
- 对 recommended units 写完整 R/I/A1/A2/E/P/B。
- appendix units 不丢弃，至少保留标题、一句话、引用和未展开原因。
- excluded_or_weak 不直接写入正文，除非用户明确要求或补证后升级。

### methodology_treatise 全 A 时的 SUMMARY 全量策略

当同时满足以下条件时，summary_plan.json 的 recommended 数量不限制 top 10，应将全部候选纳入 SUMMARY：

1. `book_type = methodology_treatise`（方法论专著）
2. `candidate_scores.json` 中 A 级占比 ≥ 95%
3. 总候选数合理（≤ 60）

**原因**：`build_summary_plan.py` 默认只推荐 top 10，是针对"散文随笔类书籍"的策略。但方法论专著的核心价值是体系完整性，每一个原子方法论单元都是体系骨架，漏掉任何一个都会破坏系统性。

**判断流程**：闸门2 读取 summary_plan.json → 检查 book_type → 如果是 methodology_treatise 且 A≥95%，通知用户全量写入，否则按 recommended 数量写作。

**注意**：全量写入仍遵循 summary_plan 的 why_include 和 risks；附录/excluded 不删除，以简版或注释形式保留。

## 闸门 2 决策包格式

阶段 2 完成后，向用户报告：

```text
闸门 2 决策包

1. 提取概况
- extractor: ...
- candidate_count: ...
- cluster_count: ...
- granularity: ...

2. 质量分布
- A: ...
- B: ...
- C: ...
- D: ...
- weak V1: ...
- single_member_ratio: ...

3. 推荐进入 SUMMARY 的单元
- u01: 标题 — why_include
- u02: 标题 — why_include

4. 风险
- suggested_merge_count: ...
- suspicious_similarity_count: ...
- 缺 boundary/glossary 的地方

5. 需要用户决定
A. 按 recommended_units 写完整七段，appendix_units 简写
B. 只写 A 级候选
C. 全量写完整七段
D. 返回阶段 2 补提取
```

## 脚本 CLI 常见陷阱

### build_summary_plan.py 参数顺序

**正确顺序**（clusters 在前，scores 在后）：

```bash
python build_summary_plan.py <clusters.json> <candidate_scores.json> <summary_plan.json>
```

**错误顺序的后果**：如果颠倒（scores 在前，clusters 在后），脚本不会报错退出，但 `summary_plan.json` 中 `cluster_count` 和 `grade_distribution` 为 null，`recommended_units` 为空数组（`[]`）。外表看起来 `ok: true`，实际是静默失败。

**识别方法**：检查 `summary_plan.json` 中 `inputs.cluster_count` 是否为 null。如果为 null + `recommended_units` 为空 → 极可能是参数顺序错误。

**与全C场景的区分**：
- 全C 正常输出：`recommended=0, appendix=ALL, cluster_count` 有值
- 参数顺序错误：`recommended=0, appendix=0, cluster_count=null`

## 反向检查

质量闸门可能误伤好内容，尤其是散文/随笔/哲学类文本。遇到以下情况，不要机械按分数删除：

- 候选分数低，但 `v3_reason` 明显指出强反直觉洞见。
- 单成员 cluster，但它是全书核心概念。
- related 为空是因为该书结构单线，而不是提取失败。
- source_line 缺失来自历史候选，不代表原文不存在。

处理方式：标记风险、补证或降级，不自动删除。

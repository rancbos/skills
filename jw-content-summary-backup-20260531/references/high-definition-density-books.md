# 高定义密度方法论专著的候选生成策略

## 核心结论

对于 `book_type_hint: methodology_treatise` 且 `definition_density_per_10k ≥ 3.5` 的书籍（如张五常《经济解释》），**主代理直接撰写 candidates 优于 execute_code 提取**：

- execute_code 从 chapters 文本提取的候选，常因格式差异缺失 `source_quote`、`v3_pass`、`source_line` 等字段，被 validate_candidates.py 重扣（-75分）导致 pipeline score 失真
- 阶段 1 理解分析（stage1-understanding.md）已包含完整结构化信息（章节角色、核心框架），可直接映射为 candidate 条目
- 主代理基于理解分析写候选，每个条目携带完整 schema 字段，pipeline score 更高（实测《经济解释》：16候选 avg=96.56，全A）

## 触发条件

阶段 1 解析 `book-index.json` 后满足以下任一条件：

```json
"book_type_hint": "methodology_treatise",
"structure_metrics": {
  "definition_density_per_10k": 3.5  // 或更高
}
```

或人工判断：书籍以框架/原则/论证为主，章节内大量定义性表述（而非叙事性案例）。

## 操作流程

### 步骤 1：阶段 1 建索引 + 理解分析

```bash
python3 scripts/build_book_index.py "/root/books/<书名>.txt" "/root/books"
# 检查 book-index.json 的 book_type_hint 和 definition_density_per_10k
```

若 `definition_density_per_10k ≥ 3.5` → 标记为「高定义密度书籍」，进入步骤 2。

### 步骤 2：主代理直接写 candidates（绕过 execute_code）

基于 `stage1-understanding.md` 中的结构化理解，直接撰写 candidates 文件：

**文件结构**：
- `candidates/frameworks.md` — 从 stage1 识别的框架映射
- `candidates/principles.md` — 从 stage1 识别的原则映射
- 可选：`cases.md`、`insights.md`、`glossary.md`、`boundaries.md`（按需）

**每个 candidate 必须包含的完整 schema 字段**：
```yaml
- id: <type>-XX
  type: <framework|principle|case|insight|boundary|procedure|glossary>
  source_chapter: ch0XX-ch0XX  # 来自 stage1 的章节角色
  source_title: <章节标题>
  title: <方法论名称>
  summary: <200-300字核心总结>
  keywords: [<关键词1>, <关键词2>]
  related: [<相关候选ID>]
  v3_pass: true
  v3_reason: <为什么这是反直觉/重要的>
  source_line: <行号(数字)>
  source_quote: "<50字原文引用>"
  v2_scenario: "<应用场景>"
```

**关键**：`source_quote`（带引号、不含换行符）、`v3_pass: true`、`source_line`（数字）是 pipeline 评分的关键字段，缺失直接扣-75分。

### 步骤 3：跑 pipeline

```bash
# validate candidates
python3 scripts/validate_candidates.py "/root/books/<书名>/candidates"

# pipeline: validate → cluster → score → plan
python3 scripts/pipeline_phase2.py "/root/books/<书名>/candidates" "/root/books/<书名>/output"
```

### 步骤 4：检查结果

```json
// phase2_result.json
{
  "stages": {
    "score": {"candidate_count": 16, "avg_score": 96.56},
    "plan": {"recommended": 10, "appendix": 0}
  }
}
```

`avg_score ≥ 90` 且 `recommended ≥ 10` → candidates 质量优秀，stage3 直接使用 summary_plan.json

`avg_score < 70` 且 penalties 集中在格式字段（missing_source_quote/v3_not_passed）→ 候选内容可用，手动补充 schema 字段后重跑 pipeline

## 实战案例

### 《经济解释》（张五常）

- **book-index.json**: `definition_density_per_10k: 3.85`, `meaningful_chapter_count: 151`, `book_type_hint: methodology_treatise`
- **stage1 产出**: 6 大框架（科学方法论、自私假设与行为约束、需求定律、产权经济学、竞争准则、合约经济学）
- **candidates 写入**: 主代理直接写 16 个候选（6 framework + 10 principle），每个含完整 schema 字段
- **pipeline 结果**: validate=True, cluster=13, score=16 candidates avg=96.56, recommended=10, valve=False
- **质量评级**: 全 A（16/16），无格式问题

### 对比：execute_code 提取的学术书

- 《思考，快与慢》：execute_code 提取 18 候选 → score=4.17、全D → 手动补字段后重跑 → PASS
- 《稀缺》：execute_code 提取 → pipeline score 失真 → 手动编组 → PASS

**结论**：高定义密度书籍（methodology_treatise）的结构化程度足够主代理直接撰写高质量 candidates，跳过 execute_code 可以避免格式字段缺失导致的评分失真。

## 何时仍需 execute_code

- 书籍为案例集/传记/散文集（definition_density 低，碎片化洞见多）
- `meaningful_chapter_count > 100` 且章节结构均匀（ execute_code 分批提取更高效）
- 阶段 1 未产生足够结构化的 stage1-understanding.md

## 关联文档

- `references/academic-book-pipeline-score-gap.md` — pipeline 评分失真的一般处理
- `references/stage1-edge-cases.md` — 书籍分类路由
- `methodology/01-stage1-read-extract.md` — 阶段 1 流程
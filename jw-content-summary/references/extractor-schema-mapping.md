# Extractor Schema 完整字段映射

九类 extractor 的 YAML schema 与七段（R/I/A1/A2/E/P/B）填充方式的对照参考。

## 通用必需字段（9类 extractor 共同）

```yaml
- id: pr-01                          # 类型前缀-序号
  title: 原则名称                      # ≤60字
  type: principle                     # 与文件名一致
  source_chapter: ch011 / 第二章 财务与投资  # chXXX / 章节名
  source_line: 42                     # 引用位置：行号（整数）、章节名（ch017）、或年份描述（1984年致股东信）
  source_quote: "原文引用，≤150字。"     # 直接引用的巴菲特原话
  summary: "用自己的话，5-15行，说明本原则核心。"  # 面向读者
  keywords: [关键词1, 关键词2, 关键词3]   # 3-5个
  v3_pass: true                       # 布尔值，必须
  v3_reason: "为什么这是独特洞见而非常识。"  # 2-5句
  v2_scenario: "什么时候用这个原则？"       # 1-2句
  related: [fw-03, ca-07]             # 可选，不超过3条
```

## 七段填充方式（每类 extractor 的 R/I/A1/A2/E/P/B）

| 字段 | 含义 | 在 YAML 中的来源 |
|------|------|-----------------|
| R (Reason/来源) | 原文引用 | `source_quote` + `source_chapter` |
| I (Insight/洞察) | 核心洞见一句话 | 从 `summary` 提炼首句 |
| A1 (Application/应用场景) | 典型应用 | `v2_scenario` |
| A2 (Anti-application/慎用场景) | 反面/边界 | `v2_scenario` 的反面，或另写 `boundary` 条目 |
| E (Example/实例) | 书中案例 | `case` extractor 的 `source_quote` |
| P (Principle/原则) | 行动准则 | 从 `summary` 提炼行动句 |
| B (Boundary/边界) | 适用边界 | `keywords` 中的边界词或专门 `boundary` 条目 |

## 九类 extractor 的填充差异

### framework
- `title`: 框架名称（如"市场先生框架"）
- `source_quote`: 框架的定义性表述
- `summary`: 框架的核心构成要件 + 用途
- `keywords`: [框架名称, 核心概念, 适用场景]

### principle
- `title`: 原则名称（如"不做清单原则"）
- `source_quote`: 巴菲特原话中的规则性表述
- `summary`: 原则的内涵 + 为什么重要
- `keywords`: [原则名称, 行动关键词, 避免什么]

### case
- `title`: 案例名称（如"禧诗糖果收购"）
- `source_quote`: 案例描述的关键引语
- `summary`: 案例经过 + 结果 + 核心教训
- `keywords`: [公司名, 行业, 投资类型]

### boundary
- `title`: 警示名称（如"会计诡计"）
- `source_quote`: 警示内容的原文
- `summary`: 问题本质 + 如何识别 + 后果
- `keywords`: [风险类型, 警示信号, 识别方式]

### procedure
- `title`: 步骤名称（如"估值三步法"）
- `source_quote`: 步骤描述中的关键引语
- `summary`: 步骤概览 + 每步要点
- `keywords`: [步骤名称, 分析方法, 决策流程]
- `v2_scenario` 须写清楚输入和输出

### boundary
- `title`: 边界名称（如"不适用于高成长股"）
- `source_quote`: 边界条件的原文
- `summary`: 边界是什么 + 超出边界会怎样
- `keywords`: [适用边界, 前提条件, 限制条件]

### insight
- `title`: 洞见名称（如"商誉的真正含义"）
- `source_quote`: 洞见的原文表述
- `summary`: 洞见内容 + 为什么反直觉
- `keywords`: [洞见主题, 反直觉点, 认知更新]

### glossary
- `title`: 术语名称（如"经济商誉"）
- `source_quote`: 术语定义的原文
- `summary`: 术语的标准定义 + 巴菲特的修正/补充
- `keywords`: [术语, 相关概念, 学科领域]

### definition
- 与 glossary 基本相同，但侧重概念辨析和对比

## 常见错误

| 错误 | 结果 |
|------|------|
| 缺 `v3_pass` 字段 | validate 报告 missing_required_fields |
| `source_line` 为空 | validate 报告 invalid_source_line |
| `related` 非列表 | validate 报告 invalid_related |
| `source_quote` > 150字 | validate 报告 quotes_too_long |
| 用 `chapter` 代替 `source_chapter` | validate 报告 missing_required_fields |
| 用 `principle` 代替 `summary` | validate 报告 missing_required_fields |

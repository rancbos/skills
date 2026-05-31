# Wiki 架构

> jw-llm-wiki 的目录结构和文件组织。

## 目录结构

```
wiki/
├── SCHEMA.md           # 规范、标签分类
├── index.md            # 内容目录
├── log.md              # 操作日志
├── purpose.md          # 研究方向（可选）
├── raw/                # 不可变原始来源
│   ├── articles/       # 网页文章、剪藏
│   ├── papers/         # PDF、arxiv 论文
│   ├── transcripts/    # 会议记录、访谈
│   └── assets/         # 来源引用的图片、图表
├── entities/           # 实体页面
├── concepts/           # 概念页面
├── comparisons/        # 对比分析
├── queries/            # 查询结果
├── _crystallize/       # 结晶化洞见
│   ├── pending.md      # 待处理洞见
│   └── processed.md    # 已处理洞见
├── _archive/           # 归档页面
├── _meta/              # 图谱数据
│   ├── graph-data.json # 图谱数据
│   └── knowledge-graph.mmd # Mermaid 图
└── .wiki-cache.json    # 缓存
```

## 三层架构

| 层 | 目录 | 说明 |
|----|------|------|
| 第1层 | `raw/` | 不可变原始来源。Agent 只读不改。 |
| 第2层 | `entities/`, `concepts/`, `comparisons/`, `queries/` | Wiki 本体。Agent 拥有的 markdown 文件。 |
| 第3层 | `SCHEMA.md` | 定义结构、规范和标签分类。 |

## 页面类型

| 类型 | 目录 | 说明 |
|------|------|------|
| entity | `entities/` | 实体页面（人物、组织、产品、模型） |
| concept | `concepts/` | 概念/主题页面 |
| comparison | `comparisons/` | 对比分析 |
| query | `queries/` | 值得保留的查询结果 |

## Frontmatter 规范

```yaml
---
title: 页面标题
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query
tags: [标签1, 标签2]
category: rujia | dao | invest | ...
sources: [raw/articles/source.md]
confidence: EXTRACTED | INFERRED | AMBIGUOUS | UNVERIFIED
evidence: "原文摘录或推理依据"
contested: false
contradictions: []
---
```

## 置信度级别

| 级别 | 说明 | evidence 要求 |
|------|------|--------------|
| EXTRACTED | 信息直接出现在原文里 | 必须提供原文摘录（建议 ≤50 字） |
| INFERRED | 从多处原文推断出来 | 必须说明推理依据 |
| AMBIGUOUS | 原文说法不清楚或有歧义 | 可选 |
| UNVERIFIED | 来自 Agent 的背景知识 | 可选 |

## 标签分类

标签必须来自 SCHEMA.md 的分类。需要新标签时，先在 SCHEMA.md 添加再使用。

## 页面阈值

- **创建页面**：实体/概念出现在 2+ 来源中，或是一个来源的核心内容
- **添加到已有页面**：来源提及了已覆盖的内容
- **不创建页面**：顺带提及、次要细节、领域外内容
- **拆分页面**：超过 ~200 行时 —— 拆分为子主题并交叉链接
- **归档页面**：内容完全被取代时 —— 移至 `_archive/`，从索引移除

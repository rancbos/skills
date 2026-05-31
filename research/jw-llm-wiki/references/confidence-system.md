# 置信度系统详解

## 概述

置信度系统用于标注 wiki 页面中信息的来源和可信度，帮助用户快速识别哪些信息是原文直接支持的，哪些是推断或来自背景知识。

**核心原则：** 置信度必须有证据支持，不能随意标注。

## 四个置信度级别

### 1. EXTRACTED（原文摘录）

**含义：** 信息直接出现在原文里，字面可以找到。

**evidence 要求：** 必须提供原文摘录（建议 ≤50 字）

**示例：**
```yaml
confidence: EXTRACTED
evidence: "《论语》原文：'学而时习之，不亦说乎？'"
```

**使用场景：**
- 直接引用原文
- 原文明确陈述的事实
- 原文中的具体数据、日期、人名

**验证方法：** 在原始素材中搜索 evidence 中的引文，确认可以找到

### 2. INFERRED（推断）

**含义：** 信息是从多处原文推断出来的，原文没有直接说。

**evidence 要求：** 必须说明推理依据

**示例：**
```yaml
confidence: INFERRED
evidence: "从《论语》多处关于'仁'的论述推断，孔子认为'仁'是最高道德标准"
```

**使用场景：**
- 综合多处原文得出的结论
- 对原文的合理解读
- 基于原文的逻辑推演

**验证方法：** 检查推理链条是否合理，是否有原文支持

### 3. AMBIGUOUS（有歧义）

**含义：** 原文说法不清楚，或者有歧义。

**evidence 要求：** 可选（建议说明歧义所在）

**示例：**
```yaml
confidence: AMBIGUOUS
evidence: "原文对'天命'的解释存在多种解读，学界尚无定论"
```

**使用场景：**
- 原文表述模糊
- 学术界存在争议
- 不同学派有不同解读

**处理建议：** 标记为 `contested: true`，等待用户进一步验证

### 4. UNVERIFIED（未验证）

**含义：** 信息来自 Agent 的背景知识，原文没有证据。

**evidence 要求：** 可选（建议说明知识来源）

**示例：**
```yaml
confidence: UNVERIFIED
evidence: "这是学术界的一般性共识，但原文未提及"
```

**使用场景：**
- 背景知识补充
- 原文未涉及但相关的领域知识
- 一般性常识

**处理建议：** 明确告知用户这是背景知识，非原文内容

## 置信度赋值规则

### 规则 1：单一来源 → 默认 INFERRED

```
来源：《论语》
内容：孔子的核心思想是'仁'
置信度：INFERRED（因为是推断，非直接引用）
```

### 规则 2：多来源充分支持 → 可标记 EXTRACTED

```
来源：《论语》、《孟子》、《荀子》
内容：儒家强调'仁义礼智'
置信度：EXTRACTED（多部经典明确支持）
evidence: "《论语》：'克己复礼为仁'；《孟子》：'仁，人心也'"
```

### 规则 3：存在矛盾或歧义 → AMBIGUOUS

```
来源：《论语》、《老子》
内容：对'无为'的理解
置信度：AMBIGUOUS（儒道两家理解不同）
evidence: "儒家'无为'指'德治'，道家'无为'指'自然'"
```

### 规则 4：来自背景知识 → UNVERIFIED

```
来源：无
内容：孔子生于公元前551年
置信度：UNVERIFIED（原文未提及，来自背景知识）
```

## 在 Frontmatter 中的使用

```yaml
---
title: 论语
created: 2026-05-30
updated: 2026-05-30
type: entity
tags: [儒家, 十三经, 四书]
sources: [raw/articles/quanxue-rujia.md]
confidence: EXTRACTED
evidence: "《论语》是孔子弟子及再传弟子记录的孔子言行"
contested: false
---
```

## 在页面内容中的使用

### 段落级标注

```markdown
## 核心思想

孔子的核心思想是'仁'。<!-- confidence: INFERRED -->

'仁'的含义包括：爱人、克己复礼、忠恕之道。<!-- confidence: EXTRACTED -->
```

### 列表项标注

```markdown
## 主要观点

- 儒家强调'仁义礼智' <!-- confidence: EXTRACTED -->
- 道家主张'无为而治' <!-- confidence: INFERRED -->
- 法家提倡'以法治国' <!-- confidence: AMBIGUOUS -->
```

## 健康检查中的置信度报告

### Lint 输出示例

```
置信度报告：
- EXTRACTED：45 个条目
- INFERRED：23 个条目
- AMBIGUOUS：5 个条目
- UNVERIFIED：12 个条目

需要验证：
- [[论语]] 中的'仁'的定义（AMBIGUOUS）
- [[老子]] 中的'无为'解释（AMBIGUOUS）
- [[孔子]] 的生卒年（UNVERIFIED）

抽查结果：
- ✓ [[论语]] '学而时习之' — 原文可找到
- ✗ [[论语]] '仁者爱人' — 原文中无此表述，应改为 INFERRED
```

### 验证流程

1. **统计各置信度数量**
2. **高亮 AMBIGUOUS 条目** — 提示用户优先验证
3. **抽查 EXTRACTED 条目** — 检查是否能回溯到原文
4. **标记问题条目** — 无法回溯的应降级为 INFERRED 或 UNVERIFIED

## 最佳实践

### 1. 证据必须真实

不要为了让内容看起来可信而编造 evidence。如果原文没有直接支持，就老实标记为 `INFERRED` 或 `UNVERIFIED`。

### 2. 证据要具体

```yaml
# 好的 evidence
evidence: "《论语·学而》：'学而时习之，不亦说乎？'"

# 不好的 evidence
evidence: "原文有相关论述"
```

### 3. 推断要说明依据

```yaml
# 好的 evidence
evidence: "从《论语》多处关于'仁'的论述推断，孔子将'仁'视为最高道德标准"

# 不好的 evidence
evidence: "孔子认为'仁'很重要"
```

### 4. 歧义要明确标注

```yaml
confidence: AMBIGUOUS
evidence: "原文对'天命'的解释存在两种主要观点：命运论和使命论"
contested: true
```

### 5. 背景知识要诚实标注

```yaml
confidence: UNVERIFIED
evidence: "这是历史学界的一般性共识，但《论语》原文未提及"
```

## 常见错误

### 错误 1：把推断标成原文

```yaml
# 错误
confidence: EXTRACTED
evidence: "孔子说'仁者爱人'"

# 正确
confidence: INFERRED
evidence: "从《论语》多处关于'仁'的论述综合推断"
```

### 错误 2：证据缺失

```yaml
# 错误
confidence: EXTRACTED
evidence: ""

# 正确
confidence: UNVERIFIED
# 或者补充证据
confidence: EXTRACTED
evidence: "《论语·学而》原文：'学而时习之，不亦说乎？'"
```

### 错误 3：歧义不标注

```yaml
# 错误
confidence: EXTRACTED
evidence: "儒家'无为'指'德治'"

# 正确
confidence: AMBIGUOUS
evidence: "儒家'无为'指'德治'，道家'无为'指'自然'，两者含义不同"
contested: true
```

## 与 llm-wiki 的对比

| 特性 | llm-wiki | jw-llm-wiki |
|------|----------|-------------|
| 置信度级别 | 4 级（EXTRACTED/INFERRED/AMBIGUOUS/UNVERIFIED） | 4 级（EXTRACTED/INFERRED/AMBIGUOUS/UNVERIFIED） |
| evidence 要求 | 必填 | 必填（EXTRACTED/INFERRED） |
| 验证机制 | 脚本自动验证 | Lint 人工抽查 |
| 标注粒度 | 段落级 | 段落级/列表项级 |

## 未来改进

### 1. 自动验证脚本

开发脚本自动检查 EXTRACTED 条目是否能回溯到原文。

### 2. 置信度可视化

在知识图谱中用不同颜色表示不同置信度级别。

### 3. 置信度统计

自动生成置信度统计报告，追踪知识库整体质量。

### 4. 置信度趋势

追踪置信度随时间的变化，识别质量下降的区域。

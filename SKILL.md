---
name: content-summary-jw
description: 总结一本书的核心方法论、框架和原则。当用户说"帮我总结XX书"、"拆解《XX》"、"提炼一本书的方法论"、"这本书在讲什么"时使用。
agent_created: true
---

# content-summary-jw — 书籍内容蒸馏总结

## 使命

把一本书里的核心方法论、框架、原则、案例、反例和术语，提炼成结构化的总结报告，让人读完后能真正理解并在实际场景中运用。

**边界**:
- ✅ 做: 方法论提炼 / 框架总结 / 原则提取 / 概念体系整理 / 书摘
- ❌ 不做: 作者人设角色扮演

## 核心方法论: 四阶段流水线

```
阶段 1: 整书理解 (Adler 分析阅读) + 阶段产出持久化
阶段 2: 并行提取 → 候选方法论单元池 (candidates/)
阶段 3: 三重验证筛选 → 优先级评分 → verified.md
阶段 4: 结构化总结撰写 → SUMMARY.md + INDEX.md
```

## 何时调用此 skill

用户说类似:
- "帮我总结《穷查理宝典》"
- "拆解《矛盾论》的方法论"
- "提炼这本书的核心框架"
- "这本书在讲什么"
- "summarize this book: <path>"

## 输入要求

在开始前**必须**从用户处确认:
1. **书的文本来源**: PDF / EPUB / TXT 文件路径，或可访问的纯文本。**不要**在没有文本的情况下"凭记忆"总结。
2. **书名 + 作者 + 出版年**: 用于目录命名和审计。

## 重要区分：阶段 1 的四问 vs 阶段 4 的四问

**两者形式相同，但语义和目的不同，不得混淆:**

| | 阶段 1 的四问（Adler 分析阅读） | 阶段 4 的四问（输出结构） |
|---|---|---|
| **目的** | 读取策略：读者向自己提问以理解全书 | 导读引导：向读者展示总结前的概览 |
| **"有道理吗"** | 批判性评价：发生在读完书之后，写入阶段 1 的理解成果中 | 概述性评价：写在 SUMMARY 开头，供读者快速判断是否值得深入 |
| **位置** | 内化在 agent 上下文中，不出现在 SUMMARY/INDEX 里 | 出现在 SUMMARY.md 和 INDEX.md 的固定前置位置 |

**操作要点**: 阶段 1 的批判性评价（作者的局限/偏见/争议点）应写入 `stage1-understanding.md` 的批判段，不得直接混入阶段 4 的四问输出结构。

## 输出结构

```
books/<book-slug>/
├── stage1-understanding.md    # 阶段 1 产出: 整书理解的持久化记录
├── INDEX.md                   # 阶段 4 产出: 全书导航 + 元信息 + 四问摘要
├── SUMMARY.md                 # 阶段 4 产出: 核心方法论 + 四问展开 + 审计
├── candidates/                # 阶段 2 产出: 原始候选池 (审计用)
│   ├── frameworks.md
│   ├── principles.md
│   ├── cases.md
│   ├── counter-examples.md
│   └── glossary.md
├── verified.md                # 阶段 3 产出: 通过验证的单元 + 优先级评分
└── rejected/                  # 阶段 3 产出: 未通过验证的单元 (含原因)
    └── <id>.md
```

## 书籍分类与 extractor 策略

**阶段 1 末尾必须完成书籍类型判断**，据此决定各 extractor 的处理权重:

| 书籍类型 | 特征 | 重点 extractor | 可简化的 extractor |
|---|---|---|---|
| 方法论专著 | 大量框架/原则/推理 | 全部认真跑 | — |
| 散文/随笔集 | 碎片化洞见，少体系 | framework + principle | case（轻量） |
| 学术/理论著作 | 术语密集，论证严密 | glossary + framework | — |
| 传记/案例集 | 大量真实事件 | case 为主 | framework（轻量） |

## 长书策略

当书籍文本超过 5 万字，或预估 token 消耗可能溢出上下文窗口时:

1. **分块**: 按章节将书籍切分为独立文本块，每块独立运行 extractor
2. **合并**: 各块候选池合并去重后，再进入阶段 3
3. **阶段 1 先行**: 先完成全书的阶段 1 理解（结构/术语/主线），再按块执行阶段 2，避免在局部文本上浪费 token

## 质量红线 (违反则阻止输出)

1. 每个方法论单元必须有**原文引用**，标注出处章节
2. 每个单元必须有完整的 R / I / A1 / A2 / E / B 六段
3. 原文引用 ≤150 字/段
4. 总结必须体现作者**独特的反直觉见解**，不是常识复述

## 交卷前自检清单（阶段 4 末尾必须执行）

在输出 SUMMARY.md 之前，逐项确认:

- [ ] **红线 1**: 每个方法论单元都有原文引用，标注了章节位置
- [ ] **红线 2**: 每个方法论单元都有 R/I/A1/A2/E/B 六段，缺一不可
- [ ] **红线 3**: 所有原文引用单段 ≤150 字
- [ ] **红线 4**: 总结体现了作者独特的反直觉见解，不是普通常识
- [ ] **四问板块**: 一至四每问都已填写，无占位符残留
- [ ] **锚点一致**: SUMMARY.md 中每个方法论的标题即为目录锚点，保持完全一致
- [ ] **INDEX/SUMMARY 分工**: INDEX 不重复 SUMMARY 的详细四问展开内容，只保留摘要

## 调用惯例

- **阶段之间主动汇报进度** — 不要静默跑完再 dump 结果
- **不凭记忆总结** — 没文本就停下来问
- **保留审计轨迹** — candidates/ 和 verified.md 都要留
- **并行执行**: 阶段 2 的 5 个 extractor 在支持并行 spawn 时同时运行；若环境不支持并行，改用串行但保持 extractor 之间互不读取彼此输出

## 详细执行方法论

完整执行细节见以下文件:
- `methodology/00-overview.md` — 整体流水线概述
- `methodology/01-stage1-read-extract.md` — 阶段 1: 整书理解
- `methodology/02-stage2-parallel-extract.md` — 阶段 2: 并行提取
- `methodology/03-stage3-triple-verify.md` — 阶段 3: 三重验证筛选
- `methodology/04-stage4-summarize.md` — 阶段 4: 结构化总结撰写

提取器模板:
- `extractors/framework-extractor.md` — 框架提取器
- `extractors/principle-extractor.md` — 原则提取器
- `extractors/case-extractor.md` — 案例提取器
- `extractors/counter-example-extractor.md` — 反例提取器
- `extractors/glossary-extractor.md` — 术语提取器

输出模板:
- `templates/INDEX.md.template`
- `templates/SUMMARY.md.template`

---

## 模板版本记录

| 版本 | 日期 | 变更内容 |
|---|---|---|
| v1.0 | 2026-05-08 | 初始版本，建立四阶段流水线 |
| v2.0 | 2026-05-08 | 增加前置四问板块；目录前置；核心方法论作为独立大标题 |
| v3.0 | 2026-05-08 | 增加书籍分类策略；长书分块策略；阶段1产出持久化；INDEX/SUMMARY 分工；质量门控自检清单；并行/串行回退方案；优先级评分 |

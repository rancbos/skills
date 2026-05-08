# 阶段 2 — 并行提取

## 目标

在整书理解（阶段 1）的基础上，同时从5个不同角度扫描全书，最大化候选单元覆盖率。

**前置参考**: 阶段 1 末尾已判断书籍类型（见 `stage1-understanding.md`），据此决定各 extractor 的处理重点——方法论专著全部认真跑，传记集以 case 为主，散文集轻量处理。

---

## 为什么要并行

- **覆盖**: 单一视角会漏。框架提取器找不到的"反例"，反例提取器会找到。
- **独立性**: 每个 extractor 独立判断，避免互相污染 — 三重验证才能真正起作用（V1 跨域要求"独立出现"）

## 5 个 sub-agent

每个 sub-agent 接收:
- 阶段 1 的整书理解成果（提供全局上下文）
- 书本文本（或文本路径）
- 对应的 extractor prompt (`extractors/<type>-extractor.md`)

**并行执行**: 在支持并行 spawn 的环境中，同时启动 5 个 extractor。
**串行回退**: 若环境不支持并行 spawn，改为串行执行，但保持每个 extractor **互不读取彼此输出**，以维持 V1 跨域验证的独立性要求。

| # | extractor | 查找对象 | 产出文件 |
|---|---|---|---|
| 1 | framework-extractor | 思维模型/决策框架/推理方法 | `candidates/frameworks.md` |
| 2 | principle-extractor | 原则/清单/规则/断言 | `candidates/principles.md` |
| 3 | case-extractor | 作者在书中亲自使用的实例 | `candidates/cases.md` |
| 4 | counter-example-extractor | 作者警告的失败/反例/陷阱 | `candidates/counter-examples.md` |
| 5 | glossary-extractor | 关键概念词典 | `candidates/glossary.md` |

## 每个候选单元的最小字段

```yaml
id: f01                           # 类型缩写 + 序号
title: 逆向思维                    # 简短标题
type: framework                   # framework/principle/case/counter-example/term
source_chapter: 第三讲             # 书中位置
source_quote: |                   # 原文引用 ≤150 字
  "反过来想,总是反过来想..."
summary: |                        # 用自己的话, 5-10 行
  ...
tags: [decision, mental-model]    # 便于后续链接
```

## 输出前的自检

每个 extractor 在提交候选之前自问:
1. 这个单元**在书中**有明确根据吗？（不是我脑补）
2. 它属于我这个 extractor 的职责范围吗？（不要越界）
3. 它是不是已经在别处被别的 extractor 提取过了？（重复不是问题，阶段 3 会合并）

---

## 长书分块策略

若书籍文本超过 5 万字，或阶段 1 标记了"长书":

1. **按章节切分**为独立文本块
2. 每块独立运行 extractor，产出该块的候选池
3. 所有块完成后，合并去重，形成统一的 `candidates/` 目录
4. 阶段 3 在合并后的完整候选池上进行验证

---

## 不在本阶段做的事

- **不做筛选** — 宁错杀，留给阶段 3 三重验证
- **不做最终总结** — 只出候选，不出 SUMMARY.md

---

## 常见失败模式

1. **跳过批判阶段** — 导致总结把作者的偏见当真理
2. **骨架不是"作者的骨架"，而是自己的想法** — 注意你在写摘要还是在写读后感
3. **术语定义用字典/常识而非作者的特定用法** — 作者用"能力圈"和字典用"能力圈"不是一回事
4. **没有足够证据就评价** — "我觉得"不等于"我证明了"
5. **跳过解释阶段直接提取** — 关键术语不理解，提取就会走偏

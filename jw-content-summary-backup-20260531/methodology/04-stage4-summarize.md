# 阶段 3 — 单文件 SUMMARY 渲染

## 目标

在不压缩最终质量的前提下，用 `clusters.json` 减少重复阅读，生成一份完整 `SUMMARY.md`。

## 输入

- `stage1-understanding.md`
- `summary_plan.json`（v4.4 首选输入，由 `clusters.json` + `candidate_scores.json` 生成）
- `clusters.json`
- `candidate_scores.json`
- `candidates/*.md`
- 必要原文片段（只为补足引用/案例/边界）

## 输出

- `books/<slug>/SUMMARY.md`
- `books/<slug>/SUMMARY.html`（同步生成，样式嵌入式，支持暗色模式）

## SUMMARY.md 结构

```
# {{BOOK_TITLE}} — 方法论总结

## 一、作者的写作意图
## 二、这本书在谈什么
## 三、全书的内容结构
## 四、这本书有道理吗
## 五、这本书与自己的关系
## 六、核心方法论
## 附录：未完整展开的方法论（如有）
## 审计信息
## 方法论展开策略

### 默认规则

- 优先读取 `summary_plan.json`：
  - `recommended_units`：默认完整 R/I/A1/A2/E/P/B 七段展开
  - `appendix_units`：默认进入附录，除非用户要求完整展开
  - `excluded_or_weak`：默认不写入正文，除非返回阶段 2 补证或用户明确要求
- 如果缺少 `summary_plan.json`，回退到旧规则：cluster 数 ≤10 全部展开；cluster 数 >10 全量展开（v4.22 闸口已移除，全量模式）。
- `candidate_scores.json` 的 A/B/C/D 是决策信号，不是自动删除规则。

### 如果用户选择 Top 10 完整展开

`SUMMARY.md` 中：

- Top 10：完整 R/I/A1/A2/E/P/B 七段
- 其余：放「附录：未完整展开的方法论」
  - 标题
  - 一句话 summary
  - 原文引用
  - 为什么未展开（如：证据弱/重复/优先级低）

这样不丢失信息，但避免主文过长。

## RIAAEPB 七段

### R — Reading（原文）

- 直接引用 ≤150 字
- 必须标注出处（章节 / 页码 / 段落标识）
- 若原书是英文，引用英文原文 + 自己翻译的中文，**不要用现成译本**

### I — Interpretation（自述）

- 用自己的话重写方法论核心骨架
- 5–15 行
- 一个没读过原书的人能否理解？不能就重写

### A1 — Past Application（书中案例）

- 作者在书中亲自用这个方法论处理过的具体案例
- 至少 1 条，≤3 条
- 问题 → 使用 → 结论 → 结果

### A2 — Application Scenarios（应用场景）

- 3–5 条具体场景
- 可参考候选中的 `v2_scenario`
- 必须区分相邻方法论，避免混淆

### E — Key Points（执行要点）

- 1-2-3 要点
- 每步有可判断的完成标准
- 判停点显式写出

### P — Procedure（步骤）

P 不是 E 的重复。E 是「要做什么」，P 是「怎么做」。

P 段必须：
1. 还原因果链
2. 区分 🔵必经 与 🟡条件触发
3. 显式化隐性前提
4. 用可操作动词，不用原则替代步骤
5. 通过新手反向验证

### B — Boundary（边界）

- 什么时候不要用
- 作者警告过的失败模式
- 容易混淆的相邻方法论

## 质量自检

- [ ] `summary_plan.json` 已读取；recommended / appendix / weak 三类均已处理
- [ ] 原文引用 ≤150 字，且有出处
- [ ] 完整展开的方法论都有 R/I/A1/A2/E/P/B 七段
- [ ] 五问正文完整，无占位符
- [ ] 独特洞见体现反直觉，不是普通常识
- [ ] cluster 已处理：合并/展开/附录三者之一
- [ ] A/B 级候选优先写入；C/D 级候选已说明降级或排除原因
- [ ] 锚点一致

## 常见失败模式

1. **cluster 不处理** — 同一方法论重复展开多次
3. **Top 10 后的信息丢失** — 未展开的必须进附录
4. **P 段变成 E 段复读** — P 要有输入/操作/输出链
5. **独特洞见写成赞美** — “这本书很深刻”不是洞见

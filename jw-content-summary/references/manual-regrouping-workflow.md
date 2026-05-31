# 手动编组工作流（v4.29）

当 `clusters.json` 显示 `single_member_ratio: 1.0` 时（所有候选人都是独立单成员集群），阶段 3 必须绕过 `summary_plan.json` 的推荐列表，改用手动编组。

## 触发判断

```json
// clusters.json 关键字段
{
  "single_member_ratio": 1.0,
  "single_member_count": 41,
  "suggested_merge_count": 0
}

// candidate_scores.json 全部 A 级
{
  "grade_distribution": {"A": 41, "B": 0, "C": 0, "D": 0}
}
```

**信号**：全 A + 全部单成员 = 内容质量高，但聚类算法未能发现语义重叠。不要相信 plan 的 excluded_or_weak 列表。

## 编组步骤

### 1. 读取全部候选人源文件

```bash
# 5个类型文件，通常≤100KB
candidates/boundaries.md  # bd-01 ~ bd-08
candidates/cases.md       # ca-01 ~ ca-07
candidates/frameworks.md  # fw-01 ~ fw-08
candidates/principles.md  # pr-01 ~ pr-10
candidates/procedures.md  # pc-01 ~ pc-08
```

**不要只读 `clusters.json` 的 summary 字段**——summary 是缩略版，可能丢失细节（如步骤、公式、案例的具体数字）。读实际的候选人文件。

### 2. 用领域知识识别主题边界

以《以交易为生》为例，书的结构给了自然分组线索：
- 三大支柱（个体心理 / 技术分析 / 资金管理）+ 一要素（交易记录）
- 五大核心方法论（三重滤网 / 阿氏评分 / 2%+6%风控 / 群体心理 / 交易记录）

**编组时确保每个公认核心有专门的独立方法论单元覆盖。**

### 3. 按语义相关性合并候选人

合并原则：
- **principles（原则）**：通常作为组的主干。pr-02+pr-03+pr-04 都讲群体心理 → 合并为 M1
- **procedures（步骤）**：贴到对应的 framework 或 principle 组。pc-01 是 fw-01 的操作步骤 → 合并
- **cases（案例）**：贴到它所演示的方法论组。ca-01（VRSN做空）演示 MACD 背离 → 合并到 M5
- **boundaries（边界）**：bd-07（青蛙效应）是 6%法则的动机解释 → 合并到 M9
- **单成员 framework**：如果太细（如 fw-06 强力指数只有1个候选），可以合并到相关组或作为子节

目标：
- 14 个方法论单元（范围 12-16）
- 每组 2-5 个候选人
- 全部 41 个候选人均被分配（在交叉引用表中验证）

### 4. 写入 SUMMARY.md

每组一个完整的 R/I/A1/A2/E/P/B 七段：
- **R（阅读）**：综合多个候选人的原文引用（blockquote），每个引用标注出处
- **I（解读）**：融合作者的深层洞见，不重复 R 段内容
- **A1/A2（应用）**：两个可独立执行的场景，带具体数字和步骤
- **E（案例）**：如有案例候选则展开
- **P（实践要点）**：bullet list 4-5条
- **B（边界）**：何时失效、什么市场环境不适用

每组元数据标注来源候选 ID：
```markdown
<div class="m-meta">
  <span>📊 4个候选</span>
  <span class="source-badge">pr-05</span>
  <span class="source-badge">pr-06</span>
  <span class="source-badge">pc-04</span>
  <span class="source-badge">bd-07</span>
</div>
```

### 5. 验证

- [ ] 全部 41 个候选 ID 在交叉引用表中出现
- [ ] 五大核心（或书的公认核心）各有独立方法论单元
- [ ] 每个方法论有完整七段
- [ ] 每个 blockquote 标注出处章节

## 反例：常见错误

| 错误 | 正确做法 |
|------|----------|
| 只看 plan 的 recommended_units（10个）写 SUMMARY | 读全部 5 个 candidate 文件，41 个全用 |
| 把 41 个单成员各自写成一个方法论 | 手动合并为 12-16 组 |
| 按 candidate 类型分组（boundaries一组/cases一组） | 按主题语义跨类型合并 |
| 忽略 clusters.json 的 related 字段 | related 字段提供合并线索（如 bd-07 related: ["pr-06", "pc-04"] → 都应归入风控组） |

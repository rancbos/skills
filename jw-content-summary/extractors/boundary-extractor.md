# Boundary (Limitations) Extractor

你负责识别书中方法论的**适用边界 / 禁用条件 / 误用风险 / 失败模式 / 警示误区**。

## v4.12 合并说明

本 extractor 由 boundary-extractor 和 counter-example-extractor 合并而来（v4.12）。两者语义高度重叠（禁用条件 ≈ 失败模式），合并为统一的 boundary extractor。

- 历史 `type: counter-example` 条目在 validate/cluster/score 阶段自动映射到 `type: boundary`
- 输出文件统一为 `candidates/boundaries.md`，不再生成 `counter-examples.md`

## 何时启动

阶段 1 判定为以下类型时重点启动：
- 实操手册（步骤/清单密集）
- 争议性理论
- 容易被误用的方法论
- 边界讨论密集的书籍

其他类型书籍：按需提取，不强制全跑。

## 你找什么（两类视角，同一输出格式）

**边界视角（禁用条件 / 失效条件）**
- 作者明确说「不要在 X 情况下使用」
- 方法失效条件
- 易混淆相邻概念
- 前提条件不足导致的失败
- 作者提醒的风险

**反例视角（失败模式 / 误区 / 警告）**
- 作者明确警告不要做的事
- 常见误用方式
- 失败案例
- 作者批判的常识或行业误解

两种视角可引用同一原文，但都输出到同一个 schema。

## 输出格式

追加到 `books/<slug>/candidates/boundaries.md`：

```yaml
- id: b01
  title: {{边界/失败模式标题}}
  type: boundary
  source_chapter: ch008 / 第八章
  source_line: 12   # 引用在源章节文件中的行号（v3.22）
  source_quote: "{{≤150 字原文}}"
  summary: "这个方法在什么条件下不适用/为什么会失败；误用后会怎样。"
  keywords: [边界关键词, 禁用条件, 风险类型]
  applies_to_hint: "可能限制：{{方法论标题}}"   # 边界视角填此项
  linked_method_hint: "可能限制：{{方法论标题}}" # 反例视角填此项（等价）
  failure_condition: "当……时失效"
  v3_pass: true
  v3_reason: "作者给出了容易被忽略的前提条件 / 明确指出了常识做法的隐性危险。"
  v2_scenario: "在{{场景}}中应避免使用。"
  related: [p02, f03]  # 交叉引用（v3.19）：关联的方法论单元 ID，不超过3条
```

**统一字段说明**：`applies_to_hint` 和 `linked_method_hint` 等价，提取时填任一即可，存储时统一为 `applies_to_hint`（boundary 视角优先）。

## 字段名强制规则（v3.19）

**输出字段名必须严格照此格式，不得更改。**
- ❌ 不要使用 `chapter:` 代替 `source_chapter:`
- ❌ 不要使用 `boundary:` 或 `counter-example:` 代替 `summary:`
- ❌ 不要省略 `keywords:` 或 `v2_scenario:`
- ✅ 全部必需字段必须出现

## 引用层级校验（v3.14）

如果书籍是**解读型**（作者 X 解读思想家 Y 的思想），必须遵循：
- ✅ 只引用 **Y 的原话**作为 `source_quote`
- ❌ 不得引用 X 的解读、转述或评价作为 `source_quote`
- ⚠️ 如果找不到 Y 的原话佐证，标记 `v3_pass: false`，`v3_reason: "二次解读无原始引用"`

## 自检

- [ ] 明确写出禁用/失效条件或失败模式
- [ ] 说明它限制哪个方法论
- [ ] 引用 ≤150 字
- [ ] 不是普通反对意见或一般性批评

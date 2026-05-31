# I-section 正则匹配陷阱（v4.60 发现）

## 问题

`validate_summary.py` 的 I-section 长度检查有两种格式：

- **Format A**：`**I — Interpretation...**：<content>\n\n**A1`（内容在同一行）
- **Format B**：`**I — Interpretation...**：\n\n<content>\n\n**A1`（内容在后续行）

Format B 使用 `re.DOTALL` + `(.*?)` 非贪婪匹配，会捕获 `**I**：` 和 `**A1**` 之间的**所有内容**，包括费曼检验、P段增强等子节。

## 触发条件

当 SUMMARY.md 中 I 段和 A1 段之间插入了费曼检验或 P 段增强子节时：

```markdown
**I — Interpretation（深层阐释）**：

格雷厄姆创造的"市场先生"寓言...（195 字符）

**费曼检验**：
- 术语去魅：✅ ...
- 比喻锚点：✅ ...
- 逻辑完整：✅ ...

**A1 — Past Application（书中案例）**：
```

Format B 正则会将"195 字符 + 费曼检验全文"都算作 I 段，导致 `[OVER] I-section unit N self-narration: 1013 chars (limit 300)`。

## 正确结构

费曼检验必须放在 A1 段**之后**，不能放在 I 段和 A1 段之间：

```markdown
**I — Interpretation（深层阐释）**：

格雷厄姆创造的"市场先生"寓言...（≤300 字符）

**A1 — Past Application（书中案例）**：
案例内容...

**费曼检验**：
- 术语去魅：✅ ...
- 比喻锚点：✅ ...
- 逻辑完整：✅ ...
```

## 推荐的七段顺序（避免正则陷阱）

```
**R — Reading**：
> 引文（≤150字符）
> ——第X章

**I — Interpretation**：
用自己的话重写（≤300字符，不含任何子节）

**A1 — Past Application**：
案例（保留数字/人名/时间线）

**A2 — Application Scenarios**：
场景（3-5条）

**E — Key Points**：
执行要点（1-2-3）

**P — Procedure**：
步骤（含机制与杠杆 + 最小可行性实验）

**B — Boundary**：
边界（什么时候不要用）
```

费曼检验、案例保真规则等 v4.54/v4.55 新增子节，放在 P 段增强内部或 B 段之后，不要插入 I-A1 之间。

## 版本

v4.60 发现，需在 methodology/04 的模板中标注此约束。

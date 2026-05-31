# 信件汇编类书籍的 Pipeline 陷阱

> 来源：巴菲特致合伙人+致股东的信全集（259章，1.29M字符，1957-2022年）

## 特征

信件汇编类书籍的特殊性：
- **章节独立性强**：每年一封信，标题独特（"1964年致股东信"），keywords 之间几乎无重叠
- **source_line 是描述性引用**：不是行号，而是"1984年致股东信"、"1965年1月18日信"
- **R-section 引用是年份格式**：`> ——第1965年信` 而非 `> ——第X章`
- **candidates 间相似度极低**：title 独特、keywords 无重叠，最高相似度仅 0.1

## 已知陷阱

### 1. source_line 验证失败（v4.63 修复）

**症状**：`validate_candidates.py` 报 `invalid_source_line: 62`（全部失败）

**原因**：`validate_source_line()` 只接受正整数，不接受"1984年致股东信"等描述性引用

**修复**：验证函数扩展支持年份（`\d{4}年`）、章节名（`ch\d+`）、中文描述

### 2. 聚类无法合并（非 bug，v4.63 确认）

**症状**：62 个 candidates → 62 个 clusters，即使阈值降到 0.35 也不合并

**原因**：信件汇编的 candidates 本身就是不同的方法论（title 独特、keywords 无重叠），最高相似度仅 0.1

**结论**：62 个独立 clusters 是正确行为。真正的问题是阶段 2 提取过多 candidates，应更精准控制数量（见下方策略）

**设计原则（v4.64）**：纯质量门控，不设数量上限。62 个 clusters 中 61 个达到 A/B 级 + avg_score≥65 → 61 recommended。质量决定一切，数量不设上限。

### 3. R-section 年份引用不通过 validator（v4.63 修复）

**症状**：`validate_summary.py` 报 `No R-section chapter citations found`

**原因**：正则只匹配"第X章"格式，不匹配"第1965年信"格式

**修复**：新增 `r_year_citations` 正则匹配 `> ——第?\d{4}年`

## 阶段 2 提取策略

信件汇编类书籍应更精准控制 candidates 数量：
- 按主题聚类（投资哲学、案例研究、公司治理等），而非按年份逐信提取
- 优先提取 framework 和 principle 类型，减少 case 类型（案例过多会导致 SUMMARY 过长）
- 目标：30-40 个高质量 candidates，而非 60+ 个碎片化 candidates

## 验证数据

| 指标 | 巴菲特致股东的信 |
|------|-----------------|
| 总字符 | 1,293,414 |
| 章节数 | 259 |
| Candidates 数 | 62 |
| Clusters 数 | 62（全部单成员） |
| Recommended | 61（v4.64 纯质量门控，无数量上限） |
| Appendix | 1 |
| Avg Score | 89.52 |
| validate_summary | PASS |

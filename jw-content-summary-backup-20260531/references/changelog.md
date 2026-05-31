# Changelog — jw-content-summary 完整版本历史

本文件记录 `jw-content-summary` skill 的所有版本变更。与 SKILL.md 同步规则：修改此 skill 时，**必须同步更新三处**：① 本文件新增对应版本条目 ② `version` frontmatter 字段递增 ③ SKILL.md 的版本摘要区更新最近版本。三者缺一不可。

---

## v4.51 (2026-05-29)

**Pitfall 6 修正：H4 标题格式绕过 R-block 引文长度校验。**

**触发场景**：《毛泽东文集》SUMMARY.md 使用 `#### R段（原文引用）` H4 标题格式（无 `**R — Reading**：` 粗体行），validate_summary.py 输出 PASS。但实际检查发现 R-block 引文长度正则 `r'\*\*R — Reading[^\n]*\n\n> (.+?)\n> ——'` 未找到任何匹配——R-block 长度检查被完全跳过，引文即使超 150 字符也不会被拦截。

**根因**：v4.48 Pitfall 6 建议用 `#### 段名` H4 标题替代 `**R — Reading**：` 粗体格式，但 validator 的 R-block 长度检查正则只匹配 `**R — Reading` 粗体格式。H4 标题通过了 section completeness 检测（`R段` 匹配 H2 前缀列表），但绕过了 R-block 长度检测。

**修复内容**：
- SKILL.md Pitfall 6 重写：列出三种格式的校验覆盖差异，推荐安全格式（H4 + 内联粗体行）
- `references/validate-summary-format.md` 新增「H4 标题变体」节
- 版本号：4.50 → 4.51

---
## v4.41 (2026-05-28)

**§4.2 新增「阶段3主代理直接写入时机」：避免 delegate_task 600s 超时。**

**触发场景**：《八次危机》stage2 完成后子代理执行 stage3，600s 超时。但 stage1+stage2 产物完整（stage1-understanding.md + candidates/ + summary_plan.json），主代理可基于已有产物直接写入 SUMMARY。

**修复内容**：
- §4.2 新增「阶段3主代理直接写入时机」，明确三个判断条件（stage1 存在 + candidates/ 有内容 + summary_plan.json 存在）
- 列出4种不需要调用 delegate_task 的场景（stage3 超时重试、validate 失败格式修复、全单成员碎片回退）
- 明确2种仍需 delegate_task 的场景（主代理上下文不足、多本并行带宽不足）
- 补充主代理直接写入格式规范（五问独立 H2、单元标题格式、R段独立行引文、审计节字面量）

**实战**：《八次危机》stage3 超时，子代理产出7.6K SUMMARY.md 但 validate 失败（缺五问/缺 R 段引文/缺审计节）。主代理直接重写29K→validate PASS。

**版本号**：4.40 → 4.41。

---
## v4.40 (2026-05-28)

**validate_summary.py 两项格式兼容修复：Q1-Q5五问格式 + `chXXX` 章节引用格式。**

**修复内容**：

1. **Q1-Q5 五问格式支持**：周金涛《周金涛理论大集》使用 `### Q1：...` / `### Q2：...` 格式（而非标准五问列表或编号五问），validate 报错五问缺失。修复：新增 `five_q_qformat = ['Q1：', ..., 'Q5：']`，三格式任一完整即通过。

2. **`chXXX` 章节引用支持**：《周金涛理论大集》R段使用 `> ——《周金涛理论大集》，ch008` 格式（原正则只匹配 `> ——第N章`）。修复：新增 `r_ch_citations` 正则，与中文章节引用并列检测。

**实战**：《周金涛理论大集》10方法论单元，validate PASS。

**版本号**：4.39 → 4.40。

---
## v4.39 (2026-05-28)

**validate_summary.py 三项格式兼容修复：五问双格式、H2/H3双前缀、R段作者名引用支持、审计节跳过、import os补充。**

**实战**：《原则——应对变化中的世界秩序》逆向推导 SUMMARY.md 使用 H2 段落标题 + 编号五问 + 作者名引用 → 修复后 validate PASS。

**版本号**：4.38 → 4.39。

---
## v4.38 (2026-05-28)

**阶段3子代理格式错误处理：主代理直接重写而非再次调用子代理。**

**实战**：周金涛《人生财富靠康波涛动周期论》子代理输出17K但格式错误（`#### R段`、问答体五问）→ 主代理直接重写28K → validate PASS。

**版本号**：4.37 → 4.38。

---
## v4.37 (2026-05-28)

**学术类书籍 pipeline 评分失真处理：penalties集中在格式字段（missing_source_quote/v3_not_passed）时，内容可用性独立于score。** 参考案例：《思考，快与慢》18候选全D→手动编组10单元→validate_summary.py PASS。新建 `references/academic-book-pipeline-score-gap.md`。版本4.36→4.37。

---
## v4.36 (2026-05-28)

**validate_summary.py I-section 正则修复：Format A（header 同行内容）优先，Format B（header 后换行）作 fallback，解决跨 unit 误捕获问题。** 实战：《稀缺》14 单元 I-section 超长误报 → 修复后 PASS。版本4.35→4.36。

---
## v4.35 (2026-05-28)

**validate_summary.py R-section 空格支持（`> —— 第3章`）+ section header 中文变体前缀匹配（`R — 原文引用` 等）。** 实战：巴菲特之道 PASS。版本4.34→4.35。

---
## v4.33 (2026-05-28)

**references/batch-processing-guidelines.md 更新：API限流+源文件发现。** 实战：3并行触发429，1并行成功。版本→4.33。

---
## v4.32 (2026-05-28)

**§7 新增「单章主导型」书籍分类及路由规则。** 实战：《价值：我对投资的思考》ch010 承载99.2%内容，绕开execute_code extractor。版本→4.32。

---
## v4.31 (2026-05-28)

**§10 质量红线新增两个高频陷阱（审计信息字面量、R段≤150字符），references/validate-summary-format.md 前置高频失败表。** 版本→4.31。

---
## v4.30 (2026-05-28)

**§9.2 新增「全单成员碎片的根因」：per_file granularity 陷阱，不需要回退。** 新建 references/per-file-granularity-bug.md。版本→4.30。

---
## v4.29 (2026-05-28)

**§9.1 新增「全单成员碎片 vs 全空计划」区别。** 实战：《查理·芒格的投资思想》24个A级单成员候选→人工编组12个方法论单元，validate PASS。版本→4.29。

---
## v4.28 (2026-05-28)

**execute_code Python 3.12 Unicode 字符陷阱；case 候选缺 linked_method_hint 字段修复；第X部分结构书籍处理模式。** 版本→4.28。

---
## v4.27 (2026-05-28)

**pipeline_phase2 终端输出字段名不匹配。** 新建 references/pipeline-printout-mismatch.md。版本→4.27。

---
## v4.26 (2026-05-28)

**validate_summary.py 格式陷阱（R-section 必须有 `**R — Reading**：` + `> ——第X章` 独立行）。** 新建 references/validate-summary-format.md。版本→4.26。

---
## v4.25 (2026-05-27)

**§8 五问描述修复：对齐 methodology/04-stage4-summarize.md 模板。** 版本→4.25。

---
## v4.24 (2026-05-27)

**空计划回退：全量读取+手动编组策略。** 新建 references/empty-plan-fallback.md。版本→4.24。

---
## v4.23 (2026-05-27)

**脚本合并(pipeline_phase2.py)+安全阀(>100自动降级)+模式统一(execute_code必选,delegate_task备选)。** 版本→4.23。

---
## v4.22 (2026-05-27)

**闸口移除+结构优化：全量连续运行。** 版本→4.22。

---
## v4.0-v4.21

见详细变更日志（略）。
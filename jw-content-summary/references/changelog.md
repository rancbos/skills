# Changelog — jw-content-summary 完整版本历史

本文件记录 `jw-content-summary` skill 的所有版本变更。与 SKILL.md 同步规则：修改此 skill 时，**必须同步更新三处**：① 本文件新增对应版本条目 ② `version` frontmatter 字段递增 ③ SKILL.md 的版本摘要区更新最近版本。三者缺一不可。

---



## v4.68 (2026-05-31)

**book-index.json 精简验证固化：pipeline 零质量损失确认。**

核心变更：
1. 巴菲特书 pipeline 对比验证：未截断（255KB）vs 截断（151KB）→ 62 candidates, avg_score=89.52, 61 recommended, 1 appendix，完全一致
2. `build_book_index.py` `first_last_paras()` 函数添加验证注释，标记 max_len=200 和 last=[] 为已验证安全阈值

**验证数据**：
- book-index.json：255KB → 151KB（-40.6%）
- first_paragraphs 最大长度：203 字符（200 截断 + 3 字符 "..."）
- last_paragraphs：已删除
- pipeline 输出：62 candidates, 62 clusters, avg=89.52, 61 recommended, 1 appendix

**版本号**：4.67 → 4.68。

---
## v4.67 (2026-05-31)

**Token 优化续：changelog 去重 + 版本表裁剪 + 过时内容清理。**

核心变更：
1. changelog.md 去重：539→467 行（-13%），消除 v4.65-v4.54 重复条目
2. SKILL.md §12 版本表裁至 10 条（17→10）
3. methodology/04 删除过时 "Top 10 完整展开" 节（v4.64 已移除数量限制）
4. methodology/02 阶段 2 嵌入措辞强化，增加 Token 节省量化说明

**版本号**：4.66 → 4.67。

---
## v4.66 (2026-05-31)

**Token 优化：SKILL.md 瘦身 + 索引精简 + 阶段2嵌入强制化。**

核心变更：
1. **🔴P0** SKILL.md changelog 移出：v4.54-v4.65 完整历史移到 `references/changelog.md`，SKILL.md 546→334 行（-39%）
2. **🔴P0** `build_book_index.py` 索引精简：first_paragraphs 截断 200 字符，删除 last_paragraphs，book-index.json 从 118KB 降到 76KB（-35%）
3. **🔴P0** `methodology/02` 阶段2嵌入强制化：子代理必须在 context 中嵌入 stage1 核心内容，禁止独立读取

**预期收益**：
- SKILL.md 每次运行减少 ~5K input tokens
- book-index.json 每次运行减少 ~40K input tokens
- 阶段2 每个子代理减少 ~50K input tokens（总计 100-200K）

**版本号**：4.65 → 4.66。

---

## v4.65 (2026-05-31)

**精简输出：删除 SUMMARY.html，明确核心产出只有 SUMMARY.md。**

核心变更：
1. **🟡P1** `SKILL.md` §5：输出结构精简，核心产出只有 `SUMMARY.md`，其余为可选保留的中间产物
2. **🟡P1** `SKILL.md` §11：脚本列表删除 `md_to_html.py`
3. **🟡P1** `methodology/04`：输出删除 `SUMMARY.html`

**设计原则**：用户关注的只是最终的 SUMMARY.md，中间文件可选保留用于审计，不强制输出。

**版本号**：4.64 → 4.65。

---

---

## v4.64 (2026-05-31)

**移除数量上限，纯质量门控。**

核心变更：
1. **🔴P0** `build_summary_plan.py`：删除 `idx <= 10` 的 Top 10 限制，改为纯质量门控（A/B 级 + avg_score≥65 → recommended）
2. **🔴P0** `pipeline_phase2.py`：删除 SAFETY_MAX_CANDIDATES/SAFETY_MAX_RECOMMENDED 安全阀逻辑
3. **🟡P1** `SKILL.md` §7：安全阀改为"质量门控"，明确不设数量上限

**设计原则**：只评判方法论应不应该输出，不限制输出数量。质量由 A/B/C/D 分级和 avg_score 决定，不由人为设定的数字截断。

**版本号**：4.63 → 4.64。

---

---

## v4.63 (2026-05-31)

**信件汇编类书籍全链路修复：source_line + 聚类阈值 + R-section 年份引用 + dry-run 聚类预览。**

基于巴菲特致股东的信全集（259章，1.29M字符，62个candidates）完整三阶段实战发现并修复 6 个问题：

1. **🔴P0** `validate_candidates.py` 和 `score_candidates.py` 的 `source_line` 验证只接受正整数，信件合集的描述性引用（如"1984年致股东信"、"ch017"、"第三章"）全部报 `invalid_source_line`（62/62 失败）。修复：验证函数扩展支持年份、章节名、中文描述
2. **🔴P0** `validate_summary.py` 的 R-section 章节引用正则只匹配"第X章"格式，不匹配"第1965年信"格式。修复：新增 `r_year_citations` 正则匹配 `> ——第?\\d{4}年`
3. **🟡P1** `cluster_candidates.py` 默认阈值 0.58 对信件汇编/案例集类书籍过高（candidates 间 title 独特、keywords 无重叠，最高相似度仅 0.1）。降至 0.35
4. **🟡P1** `pipeline_phase2.py` 的 `--dry-run` 模式增加聚类预览：输出 threshold_0.35 和 threshold_0.25 两个阈值的 clusters 数、single_member_ratio、suggested_merges
5. **🟡P2** `methodology/02-stage2-parallel-extract.md` 新增 execute_code 分批策略文档（分批规则、执行流程、关键注意事项）
6. **🟡P2** `references/extractor-schema-mapping.md` 的 `source_line` 定义从"行号（整数）"扩展为"行号、章节名、或年份描述"

**关键发现**：聚类阈值降低后巴菲特书仍是 62→62 clusters，因为这些 candidates 本身就是不同方法论（title 独特、keywords 无重叠）。62 个独立 clusters 是正确行为——真正的问题是阶段 2 提取过多 candidates，应更精准控制数量而非放宽聚类。

**版本号**：4.62 → 4.63。

---

---

## v4.62 (2026-05-31)

**Pitfall 7：三个脚本粗体格式正则 bug 修复 + 年份引用格式陷阱。**

基于巴菲特致股东的信全集（259章，62个candidates）实战发现：

1. **🔴P0** `validate_candidates.py`、`cluster_candidates.py`、`score_candidates.py` 的 `re.split()` 正则只匹配 `- id:` 不匹配 `- **id**:` 粗体格式，导致 pipeline 只处理 9/62 个候选。修复：正则添加 `\\*{0,2}` 支持
2. **🟡P1** 信件合集的 R-section 引用格式 `> ——1965年信` 不通过 validator（需"第"字），在 `references/validate-summary-format.md` 新增陷阱说明
3. **新增参考文件** `references/bold-format-regex-pitfall.md`：完整诊断和修复步骤

**版本号**：4.61 → 4.62。

---

---

## v4.61 (2026-06-01)

**阶段 2 流程优化：dry-run 测试 + 格式规范 + 减少重复读取。**

基于巴菲特致股东的信总结实战中发现的 3 个脚本解析 bug（extract_field 不支持粗体格式、read_candidates 将标题行解析为候选、字段检查不支持粗体格式），新增预防性优化：

1. **pipeline_phase2.py 增加 --dry-run 模式**：运行 `--dry-run` 只测试候选解析，不运行 cluster/score/plan，立即发现格式问题
2. **methodology/02 增加格式规范**：明确子代理输出的字段格式要求（支持 `- field:` 和 `- **field**:` 两种，禁止全角冒号）
3. **methodology/02 增加预置测试步骤**：在软聚类前先运行 dry-run 测试，避免完整 pipeline 白跑
4. **methodology/02 增加减少重复读取建议**：delegate_task 的 context 参数中嵌入 stage1 核心内容，节省约 50K tokens
5. **脚本 extract_field 正则修复**：cluster_candidates.py、score_candidates.py、validate_candidates.py 的 extract_field/read_candidates 支持 `- **field**:` 粗体格式

**版本号**：4.60 → 4.61。

---

---

## v4.60 (2026-06-01)

**skill-creator 9 维审计修复：5 项优化。**

修复内容：
1. **🟡P1** §4.1 模糊阈值："按需运行 2-5 种候选类型"改为"按 §6 书籍类型表选择"，消除执行歧义
2. **🟡P1** §8 孤立节（阶段1四问 vs 阶段3五问）合并到 §4 主流程说明，消除薄节
3. **🟡P2** §10 Pitfall 6（40 行格式细节）外移到 `references/validate-summary-format.md`，§10 回归质量红线定位
4. **🟡P1** description 增加 4 个口语化触发词（"帮我写读书笔记""读后感""这本书讲了什么""帮我拆解这本书"）
5. **🟡P2** 章节编号修复：删除 §8 后重编号 §9→§7、§10→§8 等，消除 §6→§9 断层；子节 §6.1/6.2（书籍分类子节）+ §7.3/7.4（碎片化回退）归属正确
6. 版本号：4.59 → 4.60。

---

---

## v4.59 (2026-05-31)

**skill-creator 9 维审计修复：阈值注释、触发词、行数瘦身。**

修复内容：
1. **🟡P1** §4.1 表格 delegate_task 矛盾：标注"超时率 ~100%，不推荐"
2. **🟡P1** 5 处硬编码阈值加经验来源注释（100/30/150/3万/12-16组）
3. **🟡P1** §4.3 已读书路径增加 glob pattern；candidates 不存在时 luhmann_connections 降级写入 SUMMARY.md
4. **🟡P1** §8 增加引导语，消除孤立节感
5. **🟡P1** §10 红线映射 validator 步骤（`[validator: ...]`/`[人工判断]`）
6. **🟡P1** description 增加口语化触发词（"帮我看看这本书讲了啥""这本书值不值得读""帮我拆解一下这篇文章"）
7. **🔴P0** SKILL.md 瘦身：§14 版本摘要 32→11 条目、§9.1/§9.2 从 80 行压缩到 19 行（详细步骤已在 references/），最终 479 行 < 500 行上限
8. **🟡P1** §7.1 typo: `delegat_task` → `delegate_task`

**版本号**：4.58 → 4.59。

---

---

## v4.58 (2026-05-31)

**结构性清理：SKILL.md 瘦身 899→544 行 + 冗余文件清理。**

修复内容：
1. **🔴P0-1** 删除根目录 `CHANGELOG.md`（与 `references/changelog.md` 不同步的双文件）
2. **🔴P0-2** SKILL.md changelog 瘦身：v4.0-v4.53 完整历史移到 `references/changelog.md`，SKILL.md 只保留最近 4 版摘要+版本摘要表
3. **🟡P1-3** 删除 `scripts.bak/` 目录（11 个旧脚本备份+pycache，v4.23 遗留）
4. **🟡P1-4** 删除 5 个领域特定脚本（buffett-letters-parser×3、extract_china_governance、cross_validate）
5. **🟡P1-5** `extractors/` 目录新增 README.md 标注为历史参考（旧架构 delegate_task 子代理的 prompt 模板）
6. **🟡P1-6** `methodology/00-overview.md` 版本引用从 v4.55 改为"当前版本"（避免每次发版同步）
7. **🟡P1-7** SKILL.md §4 "按需启动 2-5 个 extractor" 更新为"按需运行 2-5 种候选类型"

**版本号**：4.57 → 4.58。

---

---

## v4.57 (2026-05-31)

**9 维标准化审计修复：🔴P0×2 + 🟡P1×4 + 🟡P2×2。**

基于 skill-creator 的 `skill-audit-checklist.md` 9 维框架审计。

**修复内容**：
1. **🔴P0-1** SKILL.md §4.3：明确 `luhmann_connections` 写回 `candidates/*.md` 的 YAML frontmatter
2. **🔴P0-2** methodology/04 第八节：明确已读书籍 SUMMARY 搜索路径（同级目录/`books/`）
3. **🟡P1-3** 6 个脚本阈值加经验来源注释（150/300/500/0.58/100/10/85-70-55）
4. **🟡P1-4** description 增加口语化/英文/文章触发词（8 个触发场景）
5. **🟡P1-5** 清理 5 个过时文件（03-methodology/changelog-insert/changelog-addition/skill-slimming/plans）
6. **🟡P1-6** 质量自检 15 项全部加 `[阶段2]`/`[阶段3]`/`[validator]`/`[人工]` 标签
7. **🟡P2-7** §9.1 标题下增加"先检查 §9.2 granularity"引导，消除与 §9.2 的逻辑冲突
8. **🟡P2-8** methodology/04 模板每节标注阶段3写入时机（步骤1-7）

**版本号**：4.56 → 4.57。

---

---

## v4.56 (2026-05-31)

**全面审计修复：P0×3 + P1×5 = 8 个问题。**

修复内容：
1. **P0-1** `validate_summary.py`：修复 `all_prefixes` 未定义变量（会崩溃）
2. **P0-2** `validate_candidates.py`：删除 `connections→related` ALIASES 映射（与 v4.54 Luhmann Scan 冲突）
3. **P0-3** `validate_summary.py`：`count_chinese_chars` 改名为 `count_content_chars`（函数名误导）
4. **P1-4** `validate_summary.py`：新增 v4.54 压力测试/关联方法论节检查（warning）
5. **P1-5** `pipeline_phase2.py`：硬编码路径改为 `Path(__file__).parent`
6. **P1-6** `cluster_candidates.py`：`detect_granularity` 接入 main()，per_file 模式自动警告
7. **P1-7** `methodology/00-overview.md`：版本 v3.8→v4.55，阶段描述对齐当前架构
8. **P1-8** SKILL.md §4.3：`connections` 字段改名为 `luhmann_connections`，避免与 extractor `related` 字段语义重叠

**版本号**：4.55 → 4.56。

---

---

## v4.55 (2026-05-31)

**二次借鉴 deep-learning skill：案例保真、缺口分析、拓扑检验、阅读顺序、模糊词禁令。**

v4.54 借鉴了5项"功能层面"的增强，本次补充5项"规则层面"的约束。来源：deep-learning 的 Iron Rules（案例保真/模糊词禁令）、结构笔记模板（缺口分析/阅读顺序）、Feynman Review（拓扑检验）。

**新增内容**：
1. **案例保真规则**（A1 段）：案例必须保留具体数字/人名/时间线，禁止编造
2. **推理链审查**（压力测试）：标记推理链每步证据强度，识别论证缺口
3. **拓扑检验**（关联方法论）：主动寻找"意外连接"——共享底层机制的不同方法论
4. **阅读顺序**：方法论间有前置依赖时标注推荐路径
5. **模糊词禁令**（P 段）：禁止"优化/加强/适当/合理/有效"等模糊词

**版本号**：4.54 → 4.55。

---

---

## v4.54 (2026-05-31)

**借鉴 deep-learning skill 增强认知深度：费曼检验、压力测试、连接扫描、关联方法论。**

**触发场景**：用户研究 `/root/mydata/skills---/deep-learning` skill，发现其专家座席系统（Adler/Feynman/Luhmann/Pragmatist/Critics）和知识网络构建方法论对 jw-content-summary 有借鉴价值。用户要求保留作者原意（不加主观意图确认），只增加认知深度。

**新增内容**：

1. **I 段费曼检验**（methodology/04）：I 段（深层阐释）必须通过三项检验——术语去魅、比喻锚点、逻辑完整。确保方法论能被外行理解。

2. **P 段增强**（methodology/04）：P 段（步骤）新增两个子节——"机制与杠杆"（为什么有效、20/80杠杆、隐含假设）和"最小可行性实验"（本周可执行的最小实验）。

3. **七、压力测试**（methodology/04 + SKILL.md）：在五问之后、核心方法论之前，对全书核心论点做三视角压力测试——Musk（第一性原理质疑）、Socrates（概念定义诘问）、Munger（逆向思考/潜在风险）。

4. **八、关联方法论**（methodology/04 + SKILL.md）：在核心方法论之后，建立本书方法论与已有知识网络的连接——本书内部关联、跨书关联、跨领域连接。

5. **阶段 2.5 连接扫描**（SKILL.md §4.3）：阶段 2 提取 candidates 后，执行 Luhmann Scan——前置依赖、潜在连接、方法论发现。在 candidate 元数据中增加 `connections` 字段。

6. **质量自检更新**（methodology/04）：新增四项验收——I 段费曼检验、P 段增强、压力测试、关联方法论。

7. **新增参考文件**：`references/cognitive-depth-patterns.md` — 记录借鉴来源、设计决策、未借鉴元素原因。

**备份位置**：`/root/.hermes/skills/jw-content-summary-backup-20260531`

**版本号**：4.53 → 4.54。

---

> 完整版本历史（v4.0-v4.53）见 `references/changelog.md`。下方版本摘要表列出自 v4.32 起的关键变更。

---

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

---

## v4.40 (2026-05-28)

**validate_summary.py 两项格式兼容修复：Q1-Q5五问格式 + `chXXX` 章节引用格式。**

**修复内容**：

1. **Q1-Q5 五问格式支持**：周金涛《周金涛理论大集》使用 `### Q1：...` / `### Q2：...` 格式（而非标准五问列表或编号五问），validate 报错五问缺失。修复：新增 `five_q_qformat = ['Q1：', ..., 'Q5：']`，三格式任一完整即通过。

2. **`chXXX` 章节引用支持**：《周金涛理论大集》R段使用 `> ——《周金涛理论大集》，ch008` 格式（原正则只匹配 `> ——第N章`）。修复：新增 `r_ch_citations` 正则，与中文章节引用并列检测。

**实战**：《周金涛理论大集》10方法论单元，validate PASS。

**版本号**：4.39 → 4.40。

---

---

## v4.39 (2026-05-28)

**validate_summary.py 三项格式兼容修复：五问双格式、H2/H3双前缀、R段作者名引用支持、审计节跳过、import os补充。**

**实战**：《原则——应对变化中的世界秩序》逆向推导 SUMMARY.md 使用 H2 段落标题 + 编号五问 + 作者名引用 → 修复后 validate PASS。

**版本号**：4.38 → 4.39。

---

---

## v4.38 (2026-05-28)

**阶段3子代理格式错误处理：主代理直接重写而非再次调用子代理。**

**实战**：周金涛《人生财富靠康波涛动周期论》子代理输出17K但格式错误（`#### R段`、问答体五问）→ 主代理直接重写28K → validate PASS。

**版本号**：4.37 → 4.38。

---

---

## v4.37 (2026-05-28)

**学术类书籍 pipeline 评分失真处理：penalties集中在格式字段（missing_source_quote/v3_not_passed）时，内容可用性独立于score。** 参考案例：《思考，快与慢》18候选全D→手动编组10单元→validate_summary.py PASS。新建 `references/academic-book-pipeline-score-gap.md`。版本4.36→4.37。

---

---

## v4.36 (2026-05-28)

**validate_summary.py I-section 正则修复：Format A（header 同行内容）优先，Format B（header 后换行）作 fallback，解决跨 unit 误捕获问题。** 实战：《稀缺》14 单元 I-section 超长误报 → 修复后 PASS。版本4.35→4.36。

---

---

## v4.35 (2026-05-28)

**validate_summary.py R-section 空格支持（`> —— 第3章`）+ section header 中文变体前缀匹配（`R — 原文引用` 等）。** 实战：巴菲特之道 PASS。版本4.34→4.35。

---

---

## v4.33 (2026-05-28)

**references/batch-processing-guidelines.md 更新：API限流+源文件发现。** 实战：3并行触发429，1并行成功。版本→4.33。

---

---

## v4.32 (2026-05-28)

**§7 新增「单章主导型」书籍分类及路由规则。** 实战：《价值：我对投资的思考》ch010 承载99.2%内容，绕开execute_code extractor。版本→4.32。

---

---

## v4.31 (2026-05-28)

**§10 质量红线新增两个高频陷阱（审计信息字面量、R段≤150字符），references/validate-summary-format.md 前置高频失败表。** 版本→4.31。

---

---

## v4.30 (2026-05-28)

**§9.2 新增「全单成员碎片的根因」：per_file granularity 陷阱，不需要回退。** 新建 references/per-file-granularity-bug.md。版本→4.30。

---

---

## v4.29 (2026-05-28)

**§9.1 新增「全单成员碎片 vs 全空计划」区别。** 实战：《查理·芒格的投资思想》24个A级单成员候选→人工编组12个方法论单元，validate PASS。版本→4.29。

---

---

## v4.28 (2026-05-28)

**execute_code Python 3.12 Unicode 字符陷阱；case 候选缺 linked_method_hint 字段修复；第X部分结构书籍处理模式。** 版本→4.28。

---

---

## v4.27 (2026-05-28)

**pipeline_phase2 终端输出字段名不匹配。** 新建 references/pipeline-printout-mismatch.md。版本→4.27。

---

---

## v4.26 (2026-05-28)

**validate_summary.py 格式陷阱（R-section 必须有 `**R — Reading**：` + `> ——第X章` 独立行）。** 新建 references/validate-summary-format.md。版本→4.26。

---

---

## v4.25 (2026-05-27)

**§8 五问描述修复：对齐 methodology/04-stage4-summarize.md 模板。** 版本→4.25。

---

---

## v4.24 (2026-05-27)

**空计划回退：全量读取+手动编组策略。** 新建 references/empty-plan-fallback.md。版本→4.24。

---

---

## v4.23 (2026-05-27)

**脚本合并(pipeline_phase2.py)+安全阀(>100自动降级)+模式统一(execute_code必选,delegate_task备选)。** 版本→4.23。

---

---

## v4.22 (2026-05-27)

**闸口移除+结构优化：全量连续运行。** 版本→4.22。

---

---

## v4.0-v4.21

见详细变更日志（略）。

---

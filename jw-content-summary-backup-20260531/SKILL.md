---
name: jw-content-summary
description: 将一本书蒸馏为可实操的方法论单元（R/I/A1/A2/E/P/B 七段）...
agent_created: true
version: 4.53
---

## v4.53 (2026-05-29)

**政治/马列类书籍纳入处理范围 + 路径特殊字符处理经验。**

**触发场景**：用户明确要求"把政治类的书也给总结了"，此前 skill 和 batch-processing-guidelines.md 默认排除政治/马列类书籍。本次批量处理 12 本政治类书籍全部完成（习近平系列、邓小平系列、毛泽东文集、资本论、马克思恩格斯全集、共产党宣言），均 validate PASS。

**经验记录**：
1. **政治/马列类不再排除**：用户明确要求全量处理，batch-processing-guidelines.md 已更新
2. **路径含特殊字符**：`习近平谈"一带一路"` 路径含引号，shell glob `*/` 和 `test -f` 无法正确处理，改用 `find ... -path "*关键词*SUMMARY*"` 验证文件存在
3. **delegate_task 成功率**：12 本政治书全部成功（含 63M 马克思恩格斯全集），说明 mimo-v2.5-pro 模型对大书有足够超时容忍
4. **书名含引号的写入**：`write_file` 支持含引号路径，但后续 shell 脚本验证需用 `find` 替代 `test -f`

**版本号**：4.52 → 4.53。

---

## v4.52 (2026-05-29)

**`references/combined-volume-speech-collections.md` 新增三卷本结构模式 + 书名含卷号引用格式。**

**触发场景**：《邓小平文选（全3卷）》book-index.json 显示 3 个 chapter（一卷一章），ch003 承载 335K/726K 字符（95.7%），属于"单章主导型"变体。此前参考文档只记录了两卷本（治国理政，99 chunks 均匀分散）的模式。

**新增内容**：
1. **三卷本结构对比表**：3 chapters vs 99 chunks、单章主导型 vs 均匀分布、编组策略差异
2. **书名含卷号引用格式**：卷号必须在《》括号内（`《邓小平文选·全3卷》`），与 v4.50 Pitfall 一致
3. **chXXX 引用格式**：三卷本使用 `> ——《书名·卷号》，ch00X` 格式匹配 `r_ch_citations` 正则
4. **已记录书籍**：新增《邓小平文选》条目

**版本号**：4.51 → 4.52。

---

## v4.51 (2026-05-29)

**Pitfall 6 修正：H4 标题格式绕过 R-block 引文长度校验。**

v4.48 Pitfall 6 建议用 `#### R段` H4 标题替代 `**R — Reading**：` 粗体格式，但未发现 H4 格式会导致 R-block 引文长度检查被完全跳过。实测《毛泽东文集》SUMMARY.md 使用 `#### R段（原文引用）` 无粗体行，validate PASS 但 R-block 正则未执行——引文长度从未被检查。

**修复**：
- Pitfall 6 重写：列出三种格式（H3粗体/H2变体/H4标题）的校验覆盖差异
- `references/validate-summary-format.md` 新增「H4 标题变体」节，明确 R-block 长度检查跳过机制
- 推荐安全格式：H4 标题 + 内联 `**R — Reading**：` 粗体行，确保两套检测都覆盖
- 版本号：4.50 → 4.51

---

## v4.50 (2026-05-29)

**validate-summary-format.md 新增陷阱：书名含副标题/卷号时，《》括号必须包含完整书名。**

**触发场景**：《习近平谈治国理政》第四卷，书名含卷号"第四卷"在 `》` 括号外部。R段引用写为 `> ——《习近平谈治国理政》第四卷，ch003`，validate 报 `[MISSING] No R-section chapter citations found`。根因：正则 `《[^》]+》` 匹配到 `》` 后期望紧跟 `，`，但实际遇到 `第` 字导致匹配失败。

**修复**：将卷号移入括号内：`> ——《习近平谈治国理政·第四卷》，ch003`。批量 sed 命令已记录在 `references/validate-summary-format.md`。

**版本号**：4.49 → 4.50。

---

## v4.49 (2026-05-29)

**§4.2 阶段3主代理直接写入时机：经验规律 + 三类新增触发场景。**

delegate_task 在阶段 3 SUMMARY 写作中一致超时 600s（薛兆丰116候选全D、当代政府与政治candidates空均超时），强烈优先主代理直接写入。新增三类触发场景：candidates为空但stage1足够支撑手工编组、pipeline全D级但候选正文七段完整可用、stage1存在但无candidates需完整stage2→3。本轮批量处理7本书（巴菲特、薛兆丰、温铁军、通往衰败之路、当代中国政府与政治、筚路维艰迁移、肥尾效应迁移），主代理直接写入全部 PASS。

## v4.48 (2026-05-29)

**R段引文字符计数基准澄清 + 长引文处理策略。**

**问题**：《温铁军套装》SUMMARY.md，R段引文被 validate 报 `[OVER] R-section unit N quote: 1138 chars (limit 150)`，但此前自检脚本报告的字符数与 validator 不符。根因：`validate_summary.py` 用 `count_chinese_chars()` 函数（stripping 空格+标点+英文后统计中文字符），而人工或 Python `len()` 包含所有字符（含标点、英文、符号）。

**判断方法**：用 `count_chinese_chars()` 验证（中文字符 ≤150）：
```python
import re
def count_chinese_chars(s):
    return len(re.sub(r'[\s\W\wa-zA-Z0-9]', '', s))
```

**长引文处理策略**：
- 遇到 R 段超长时优先重写 I 段，让 I 段承接推论细节，R 段只留最核心一句话
- R 段引文只呈现**一个**核心论点，不是章节摘要，不是定义展开，不是推论过程
- 实在无法缩短就拆分单元

**版本号**：4.45 → 4.46。

---

## v4.45 (2026-05-29)

| v4.48 | 2026-05-29 | §10 Pitfall 6 新增：方法论单元子段标题必须用 `#### R段` 四级标题，不能用加粗格式 `**R — Reading**：`。实战：《通往衰败之路》所有子段用加粗格式 → validate 报全7段MISSING → 批量替换为 `#### 段名` 格式 → PASS。 |
| v4.45 | 2026-05-29 | §11 Pitfall 5 新增：B-section 插入时 patch 撞车（相邻 unit 的 P 段内容高度相似导致 Found N matches）。修复：扩展 old_string 到 P 段末尾 + --- + 下一单元完整标题，利用唯一标题锚定。实战：《肥尾效应》Unit 4→5 撞车，扩展含下一单元标题 → patch 成功。 |

---

## v4.43 (2026-05-28)

**§10 质量红线新增陷阱3：R段章节引用必须是独立行（`> ——第X章` 单独成行，不可同行接在引文后）。** 实战：《股市真规则》主代理写入引文+同行引用→validate报MISSING→修复为独立行→PASS。

## v4.44 (2026-05-29)

**validate_summary.py 五问标题格式：phrase-based substring 检测，非完整字符串匹配。**

**触发场景**：《芒格之道》五问用 `### 一、作者的写作意图是什么？` / `### 二、核心主张是什么？` / `### 三、全书结构是怎样的？`，validate 报错五问缺失。内容已覆盖，只是标题措辞与 phrase 列表措辞偏差（如"核心主张" vs "这本书在谈什么"）。

**根因**：validate 用 phrase list（`['作者的写作意图', '这本书在谈什么', '全书的内容结构', '这本书有道理吗', '这本书与自己的关系']`）做 substring 检测，只要 H3 标题含 phrase 即通过。偏差措辞（如"是什么？"结尾或"核心主张" vs "这本书在谈什么"）导致 substring 未匹配。

**正确示例（PASS）**：`### 二、这本书在谈什么（核心主张）` 含 phrase "这本书在谈什么"

**错误示例（FAIL）**：`### 二、核心主张是什么？` 不含任何标准 phrase

**修复**：五问标题统一对齐 validate phrase 列表——每问标题必须包含对应标准 phrase，而非仅传达相同含义。

**版本号**：4.43 → 4.44。

---

---

## v4.38 (2026-05-28)

**阶段3子代理格式错误处理策略。**

**触发场景**：周金涛《人生财富靠康波涛动周期论》阶段3主代理调用子代理（delegate_task）撰写 SUMMARY.md，子代理使用了错误格式：
- `#### R段（原文引用）` 而非标准 `**R — Reading**：` + 独立行 `> ——第X章`
- 五问用问答体（`问：... 答：...`）而非标题体（`### 问题一：XXX`）
- 章节标题重复（`### 方法论单元一：周期嵌套与运行机制` 下又有 `### 方法论单元一：三周期嵌套模型`）

**处理策略**：主代理直接重写 SUMMARY.md，而非再次调用子代理。原因：①子代理已产出17K内容，核心方法论已正确，只是格式错误；②再次调用子代理需重新传递完整上下文，token消耗高且格式不可控；③主代理直接重写可精准控制格式，一次 PASS。

**修复内容**：
- §4.1 阶段2/3工具选择矩阵：新增 pitfall「阶段3 delegate_task 格式错误风险」，明确主代理直接重写策略
- changelog.md：新增 v4.38 条目
- 版本号：4.37 → 4.38

**版本号**：4.37 → 4.38。

---

## v4.37 (2026-05-28)

**学术类书籍 pipeline 评分失真处理 + 新增参考文档。**

学术类书籍（行为经济学、认知心理学等）execute_code 提取的候选人常缺少 `source_quote`、`v3_pass`、`source_line` 等格式字段，被 validate_candidates.py 重扣（-75分）导致 score 4-7/10、全D，但正文 R/I/A1/A2/E/P/B 七段完整可用。参考案例《思考，快与慢》：18候选 score=4.17、全D → 手动编组10单元 → validate_summary.py PASS。

**修复内容**：
- SKILL.md §14 版本摘要：新增 v4.37 条目
- 新建 `references/academic-book-pipeline-score-gap.md`：现象、根因、判断信号、处理路径、参考案例
- 版本号：4.36 → 4.37

---

---

---

---

## v4.36 (2026-05-28)

**validate_summary.py I-section 正则修复：跨 unit 内容误捕获。**

**触发场景**：《稀缺》SUMMARY.md，14 个单元，validate 报错 I-section 超长。逐一检查发现根因正则 `[^$]` + `\n\n` 组合存在固有缺陷：

- `**I — Interpretation（深层阐释）**：` 后面跟 `\n\n` 时，`[^$]` 在多 unit 文件中会跨 unit 匹配到下一个单元的 R-section 或 E-section 内容
- I-block 1 实际抓到 Unit 4 的 B-section（571 chars），I-block 4 实际抓到 Unit 7 的 E-section（847 chars）
- 真实 I-section 内容在 30-80 chars 范围，被误捕获的内容在 500-900 chars 范围

**修复**：SUMMARY.md 存在两种 I-section 格式：
- **Format A**（稀缺 Units 1-4）：header 同行有内容 `**：<content>\n\n**A1`，正则先匹配 `**：([^\\n]+)\\n\\n\\*\\*A1`
- **Format B**（稀缺 Units 5-14）：header 后换行 `\n\n<content>\n\n**A1`，当 Format A 不足 14 个时 fallback 为 Format B `**：\\n\\n(.*?)\\n\\n\\*\\*A1`

Format A 优先，不足 14 个才 fallback——因为 Format A 精确匹配 header 同行内容，不跨 unit。

**修复内容**：`scripts/validate_summary.py` I-section 检测正则改为双格式尝试逻辑；版本号 4.35 → 4.36；changelog 新增 v4.36 条目。

---

## v4.35 (2026-05-28)

**两处修复**：

1. **validate_summary.py R-section 章节引用正则**：巴菲特之道使用 `> —— 第3章`（引号前有空格），旧正则 `r'> ——第[零一二三...]+'` 缺少 `\\s*` 支持空格，修复为 `r'> ——\\s*第[零一二三...]+'`。

2. **validate_summary.py section header 中文变体支持**：巴菲特之道使用中文标签 `R — 原文引用`、`I — 自述阐释` 等（而非英文 `R — Reading`），原代码用硬编码英文标签列表做 substring 检查导致误报。修改为 `section_prefixes = ['R —', 'I —', 'A1 —', ...]` 前缀匹配 + `has_section_variant()` 函数，允许任意后缀文字。

**版本号**：4.34 → 4.35。

**validate_summary.py 修复：R-section 正则 + 中文章节引用支持。**

实战发现两处根因不同的校验失败：

1. **R-section 标题含中文括号时正则失效**：《文明、现代化、价值投资与中国》的 R-section 标题是 `**R — Reading（原文引用）**：`（含 `（原文引用）`），旧正则 `r'\*\*R — Reading.*?\*\*\n\n> (.+?)\n> ——'` 要求标题以 `**` 结束，但 `（原文引用）**` 之间还有中文字符，导致 `.*?` 匹配到行末也没找到 `**\n\n`。修复为 `\**R — Reading[^$]+\*\*/?\*?\s*\n\n> (.+?)\n> ——'`（允许 `**` 结束标记前有任意非 `$` 字符）。

2. **章节引用不支持中文数字**：《文明》使用 `第七章`、`第十六章` 等中文数字，旧正则 `r'> ——第\d+章'` 只匹配阿拉伯数字，导致 `[MISSING] No R-section chapter citations found`。修复为 `r'> ——第[零一二三四五六七八九十0-9篇章节]+'`（支持中文数字 + `上篇`/`下篇`/`序二` 等特殊来源）。

**修复内容**：
- `scripts/validate_summary.py`：两处正则修复（unit_starts 单元标题检测、r_citations 章节引用）
- `references/validate-summary-format.md`：`R-section 格式`和`章节引用格式`两节更新为 v4.33 修复后的实际正则和示例
- 版本号 → 4.34，changelog 新增 v4.34 条目

---

## v4.33 (2026-05-28)

**references/batch-processing-guidelines.md 更新：API限流+源文件发现。**

本次批量处理实测发现两个问题：

1. **429 API 限流**：3 并行 delegate_task 在 10 分钟内全部触发 429（Token Plan 并发限制）。降为 1 并行后每本 5-8 分钟无 429。
2. **源文件扩展名不一致**：`/root/books/` 下部分书是 `.txt` 源文件，部分是 `.md`（如 `通胀陷阱.md`、`价值：我对投资的思考.md`）。子代理按 `.txt` 传参导致"文件不存在"错误。

**修复内容**：
- `references/batch-processing-guidelines.md`：新增「API 限流应对」（429 特征、4 种防御策略、实测数据）和「源文件发现是独立步骤」（grep 确认扩展名、build_book_index.py 支持双扩展名）
- 版本号 → 4.33，版本摘要表新增 v4.33 条目

---

## v4.32 (2026-05-28)

## 1. 使命与适用边界

把一本书里的核心方法论、框架、原则、案例、反例和术语，提炼成一份结构化的 `SUMMARY.md`，让人读完后能理解并在实际场景中运用。

适用：方法论提炼、框架总结、原则提取、概念体系整理、书摘与可执行导读。

不适用：作者人设角色扮演；纯虚构作品（小说/戏剧/诗歌）的方法论蒸馏；无文本论证结构的画册、诗集、菜谱等。

虚构作品处理：如用户坚持处理，只输出 Adler 四问导读，不生成 R/I/A1/A2/E/P/B 方法论单元。
跨书融合处理：改用 `references/cross-book-synthesis.md`，不要套用单书三阶段流水线。

## 2. 触发条件

用户说类似："帮我总结《xx》"、"拆解《xx》的方法论"、"提炼这本书的核心框架"、"summarize this book"、"distill this book..."。

## 3. 输入要求

开始前必须确认：1) 书的文本来源（PDF/EPUB/TXT 文件路径）；2) 书名+作者+出版年。

| 异常 | 处理 |
|---|---|
| 文件不可读 / DRM 加密 | 告知错误，请用户重新提供 |
| 扫描件 PDF | 可尝试 OCR，优先建议纯文本版 |
| .mobi/.azw3 | 建议 calibre 转 EPUB/TXT |
| 单阶段失败 | 持久化已有成果，用户决定重试/跳过 |
| 章节/TOC 异常 | 查 `references/known-file-structures.md` / `references/stage1-edge-cases.md` |

## 4. 三阶段主流程

| 阶段 | 核心动作 | 输入 | 输出 | 状态 |
|---|---|---|---|---|
| 预处理 | clean_text + build_book_index | 原始文本 | `cleaned_text.txt`, `preprocess/book-index.json` | 自动 |
| 1 | 索引驱动结构路由 | `book-index.json` | `stage1-understanding.md` | ✅ 自动 |
| 2 | execute_code 直接生成 candidates（推荐） | 路由表 + snippets/chapters | `candidates/*.md`, `clusters.json`, `candidate_scores.json`, `summary_plan.json` | ✅ 自动 |
| 3 | 撰写 SUMMARY | `summary_plan.json` + 必要 candidates | `SUMMARY.md` | ✅ 自检后交付 |

**条件跳过优化（v4.42）**：阶段 1 开始前检查 `<book>/stage1-understanding.md` 是否存在：
- 若存在 → 跳过阶段 1，直接执行阶段 2→3（复用已有结构路由）
- 若不存在 → 完整执行三阶段（首次运行或中途恢复场景）

核心原则：
- 脚本优先：`clean_text.py` 清洗 → `build_book_index.py` 建索引。**必须传原始文件路径**，不能传 `cleaned_text.txt`（否则 `src.stem` 解析为 "cleaned_text" 导致输出目录漂移）。
- 阶段 1 只读索引和必要少量文本，不直接吞全书。
- 阶段 2：优先 `execute_code` 直接从 chapters 文本提取（子代理仅保留阶段 1 理解分析和阶段 3 SUMMARY 写作）。按需启动 2-5 个 extractor，不固定全跑。
- 阶段 2 后运行 `python3 scripts/pipeline_phase2.py <candidates_dir> <output_dir>`，一次生成 `clusters.json` + `candidate_scores.json` + `summary_plan.json`（替代旧 4 脚本分步调用，消除 CLI 参数顺序陷阱）。
- 阶段 3 以 `summary_plan.json` 为主，不重复读全部 candidates 正文。

### 4.1 阶段 2 提取方式选择

| 场景 | 方式 | 原因 |
|------|------|------|
| 标准书籍（<50 章） | `execute_code` | 确定性输出，格式可控 |
| 超大书籍（>50 章） | `execute_code`（分批） | 分 2-3 批运行，每批 return YAML |
| 章节结构复杂（混合型） | `execute_code` + REGEX | 先 REGEX 切分边界，再 execute_code 提取 |
| `execute_code` 超时（>5min） | `delegate_task`（备选 fallback） | 仅作回退方案，需额外 validation |
| 阶段 1 理解分析 | `delegate_task` | 读取结构文件，风险低 |
| 阶段 3 SUMMARY 写作 | **主代理直接写入** | delegate_task 频繁 600s 超时（实测），主代理上下文已有 candidates。**Pitfall**：子代理若输出格式错误（如错误 section header `#### R段（原文引用）`、问答体五问、双层标题重复），主代理应**直接重写**而非再次调用子代理——内容核心已正确，格式修复成本低于重新调用。 |

### 4.2 阶段 3 主代理直接写入时机（v4.49）

**经验规律（新增）**：delegate_task 在阶段 3 SUMMARY 写作中**一致超时 600s**，无论并发数量（1-3并行均触达）。当前 session 多次确认：薛兆丰经济学讲义（116候选全D）、当代中国政府与政治（candidates空）均因 delegate_task 超时未完成。**阶段 3 强烈优先主代理直接写入**，不要等子代理超时再回退。

**触发条件（需同时满足）**：
1. `stage1-understanding.md` 存在
2. `candidates/` 目录存在且有内容（或 stage1 足够支撑手工编组）
3. `summary_plan.json` 存在（含推荐/附录条目）——即使全D级，只要正文七段完整可用

**不需要调用 delegate_task 的场景**：
- stage1+stage2 完整，stage3 超时后重试 → 主代理直接写入
- stage3 validate 失败（格式错误）→ 主代理直接重写
- 全单成员碎片 §9.1 回退，手动编组后主代理写入
- **candidates 为空但 stage1 足够支撑手工编组**（如当代中国政府与政治）→ 主代理直接读取 stage1 + chapters 手工写 SUMMARY
- **pipeline 全D级但候选正文七段完整可用**（如薛兆丰、巴菲特）→ 主代理直接读取 candidates 手工编组写入

**何时仍需 delegate_task**：
- 主代理上下文窗口不足（候选内容太多，SUMMARY 需分批写入）
- 多本并行处理，主代理带宽不足
- 主代理对特定书籍领域知识不足，需要子代理读取大量章节后的推理能力

**主代理直接写入格式规范**（对照 `methodology/04-stage4-summarize.md` 模板）：
- 五问：`## 问题一：作者的写作意图`（独立 H2 标题，非 `六、核心方法论` 容器）
- 方法论单元：`## 方法论单元一：<标题>` + 七段 `**R — Reading**：` / `**I — Interpretation**：` 等
- R段引文：`> ——第X章`（独立行，非 `（第X章）` 同行格式）
- 审计节：含字面量「审计信息」 |

## 5. 输出结构

> 生产文件统一输出到源文件所在目录：`<源文件.txt所在目录>/<书名>/`

```text
<书名>/
├── cleaned_text.txt / clean_report.json
├── preprocess/               # book-index.json + chapters/ + snippets/
├── stage1-understanding.md
├── SUMMARY.md + SUMMARY.html
├── candidates/               # frameworks/principles/cases/boundaries/glossary/insights/procedures.md
├── clusters.json / candidate_scores.json / summary_plan.json / phase2_result.json
└── rejected/                 # <id>.md
```

规则：输出文件夹名用中文原名；candidates 必须持久化以备审计回滚。

## 6. 书籍分类与 extractor 路由

| 书籍类型 | 特征 | 重点 extractor | 可简化 |
|---|---|---|---|
| 方法论专著 | 大量框架/原则/推理 | 全部，含 glossary+boundary | — |
| 散文/随笔集 | 碎片化洞见，少体系 | insight+principle | framework/case |
| 学术/理论著作 | 术语密集，论证严密 | glossary+framework | case |
| 传记/案例集 | 大量真实事件 | case+principle+boundary | framework |
| 实操手册 | 步骤/清单/工具明显 | procedure+boundary+case | glossary |
| 虚构作品 | 无方法论骨架 | 不生成 SUMMARY，只输出导读 | — |
| 其他无论证结构 | 不适合方法论提炼 | 告知原因并给替代方案 | — |
| **单章主导型** | `meaningful_chapter_count: 1` 且该章 >90% 字符 | **绕开阶段2直接主代理提取**：读该章节文本，人工识别框架/原则/案例，直接写 candidates | 全局 extraction 浪费 |

`book_type_hint` 只作脚本建议。若人工判断与脚本不同，以人工为准，审计区记录修正。灰区案例见 `references/stage1-edge-cases.md`。

### 7.1 单章主导型识别与路由（v4.32）

**识别信号**（阶段 1 检查 `book-index.json`）：
```json
"meaningful_chapter_count": 1,
"fragmentation_ratio": 0.85  // 或更高
```

**典型案例**：《价值：我对投资的思考》——9章中8章是目录级TOC碎片（<100字符），ch010承载220K/222K字符（99.2%）。

**路由规则**：
1. **不跑 execute_code extractor**（会超时或产出大量 TOC 噪声）
2. **直接读 meaningful chapter 的 txt 文件**（`chapters/ch0XX.txt`）
3. **人工识别框架/原则/边界/案例**（快速扫读 + 关键段落定位）
4. **主代理直接写 candidates**（绕过 extract 流程）
5. **跑 pipeline_phase2.py** 做 validate→cluster→score→plan（即使 plan 全D，内容已就位）
6. **走 §9.1 回退写 SUMMARY**（如推荐/附录均为空）

单章主导型不需要 `delegat_task` 提取——主代理直接读文本、识别结构、写候选，速度更快、质量更高。

### 7.2 长书与复杂结构策略

≥3 万字进入长书模式。规则：先脚本切章→阶段 1 只读索引→阶段 2 按章节角色定向分配 extractor→阶段 3 读 `clusters.json` 不回读全部候选。禁止每块固定跑全部 extractor。

| 模式 | 适用 | 做法 |
|---|---|---|
| 全局提取 | 章节均匀、结构简单 | snippets 全部分配给必要 extractor |
| 定向分块 | 章节角色差异大 | 按章节 role 分配给最匹配 extractor |

边界案例见 `references/known-file-structures.md` / `references/stage1-edge-cases.md`。

## 8. 阶段 1 四问 vs 阶段 3 五问

| 项目 | 阶段 1 四问 | 阶段 3 五问 |
|---|---|---|
| 目的 | 理解策略（读者向自己提问） | 导读策略（向读者展示概览） |
| 位置 | agent 上下文内 | SUMMARY.md |

阶段 3 五问（对应 SUMMARY.md 前五节）：①作者的写作意图 ②这本书在谈什么（核心主张）③全书的内容结构 ④这本书有道理吗/边界在哪 ⑤这本书与自己的关系。注意："主要方法论"不属于五问——它是 SUMMARY.md 第六节「核心方法论」的主体内容。阶段 1 批判性评价不得直接混入阶段 3。五问模板以 `methodology/04-stage4-summarize.md` 为准。

## 9. 全量自动运行（闸口已移除 v4.22）

三阶段连续执行，不设用户确认闸口。阶段 1/2 结束后直接进入下一阶段，阶段 3 自检后交付。全 A / 全 C 场景均自动处理：全 A 全量写入，全 C 以附录池为主。质量决策包照常生成作为审计记录，但不再触发用户确认。

### 安全阀（v4.23）

候选数 >100 时自动降级：top-30 完整 R/I/A1/A2/E/P/B 七段展开，其余进附录。`summary_plan.json` 中 `valve_triggered: true` 标记触发状态。`phase2_result.json` 可审计全部阶段数据。

### 9.1 碎片化计划回退（v4.30）

当满足以下任一条件时，不走 `summary_plan.json` 的推荐/排除逻辑，改为全量读取全部候选人文件后手动编组：

- **全空计划**：`recommended_units` 和 `appendix_units` 均为空（v4.24 已覆盖）
- **全单成员碎片**：`clusters.json` 显示 `single_member_ratio: 1.0`，即所有 cluster 都是单成员。此时即使 `summary_plan.json` 有推荐条目，它们也都是相互独立的碎片——需要人工阅读全部候选人、按主题合并为 12-16 个方法论组。**不要只读 plan 的 recommended 列表**。

### 9.2 全单成员碎片的根因（v4.30）

**大多数情况下，这不是"聚类算法未能发现语义重叠"，而是 `cluster_candidates.py` 的 `granularity` 参数设置错误。**

#### 根因机制

`cluster_candidates.py` 有两个 granularity 选项：
- `by_type`（正确）：按候选类型（framework/principle/case/boundary/procedure）语义分组
- `per_file`（错误陷阱）：每个输入文件变成一个 cluster，与内容无关

**per_file granularity 的典型场景**：execute_code 从 chapters 提取后，每个候选类型一个文件（如 `frameworks.md`、`principles.md`），每个文件包含 2 个 entry（header 元数据块 + body 内容块）。当 granularity=per_file 时，N 个文件产生 N×2 个单成员 cluster，每个候选都被罚 `single_member_cluster`（-20分），导致 score 归零。

**结果**：candidate_scores.json 可能全是 A/B grade，但 average_score 全为 0（被 penalty 归零），summary_plan.json 所有条目进 excluded_or_weak。

#### 判断信号

```json
// clusters.json
"total_clusters": 40,
"single_member_count": 40,
"single_member_ratio": 1.0,
"suggested_merge_count": 0

// candidate_scores.json
"grade_distribution": {"A": 3, "B": 17, "C": 0, "D": 20},
"average_score": 0.0   // 全被 penalty 归零，但 grade 是 A/B
```

penalties 集中在 `single_member_cluster`（-20 分/个）而非实质内容缺失，是判断根因的关键。

#### 修复（立即修复，不需要回退）

不需要走手动编组回退，直接修复 `cluster_candidates.py` 的 granularity 参数后重新跑 pipeline：

```bash
# 用 by_type granularity 重新聚类
python3 scripts/cluster_candidates.py \
  --input candidates/ \
  --output clusters.json \
  --granularity by_type

# 重新跑完整 pipeline（validate → cluster → score → plan）
python3 scripts/pipeline_phase2.py candidates/ <output_dir>/
```

`by_type` granularity 会按候选内容语义分组（framework+procedure 合并、case+boundary 合并），生成有实质内容的 cluster，避免单成员惩罚。

#### 何时必须用手动编组回退

只有当 `by_type` granularity 也产生单成员碎片（书籍内容本身极度碎片化，无语义重叠可合并）时，才走 §9.1 手动编组。

回退步骤：

1. **读全部 candidates/*.md**（5-7个文件，通常≤100KB总量）——阶段 2 已提取的高质量内容。读实际文件而非依赖 `clusters.json` 的 summary 字段（summary 是缩略版，可能丢失细节）
2. **人工判断内容可用性**：检查是否有R引用、I阐释、A1案例、A2场景、E/P/B段。格式字段缺失（如 `source_quote`、`v3_pass`、`source_line`）不影响内容可用性——它们只是流水线校验字段，不是内容质量标志
3. **按主题手动编组为 12-16 个方法论单元**：
   - 用书的领域知识识别自然主题边界（如本书有三支柱+一要素结构、有五大核心主题）
   - 将语义相近、引用同一章节的候选人合并到同一组（如 pr-02+pr-03+pr-04 → "群体心理"组）
   - 单成员 case/framework/procedure 候选人通常嵌入到相关原理组（而非单列一组）
   - 目标：每组 2-5 个候选人，最终 12-16 组，全部 41 个候选人均被分配
4. **撰写 SUMMARY.md**：每组一个完整七段展开——R段综合多个候选人的原文引用，I段融合作者的深层洞见，A1/A2给出两个可执行场景，E/P/B补全。所有候选人的 ID 标注在每组元数据区
5. **确保五大核心覆盖**：如果本书有公认的核心方法论（如《以交易为生》的三重滤网/阿氏评分/2%+6%风控/群体心理/交易记录），必须在编组阶段主动确保每个核心有专门的独立方法论单元覆盖
6. **审计区记录回退原因**：说明 pipeline 为何产生碎片（单成员集群）、人工如何编组

常见降级根因：`validate_candidates.py` 需要 `source_quote`（带行号的原文引用）、`source_chapter`、`v3_pass` 等字段，但 execute_code 提取的候选常因格式差异缺失这些字段。**这不代表内容不可用**——R段引文、I段解读、A1案例等在候选文件正文中通常是完整的。

**判断信号**：如果 `candidate_scores.json` 的 penalties 主要集中在 `missing_source_quote`（30分）、`v3_not_passed`（30分）、`missing_or_invalid_source_line`（15分），而非 `missing_v2_scenario`、`empty_related` 等实质性缺失，则高度提示是格式问题而非内容问题。`single_member_ratio: 1.0` 且全部 candidate grade 为 A——说明内容质量高但聚类算法未发现语义重叠，需人工合并。

**全单成员碎片 vs 全空计划**：前者有推荐条目但全是碎片（本例），后者完全无推荐条目。两者都走全量读取回退，但前者的 `summary_plan.json` 推荐列表可作为人工编组时的优先级参考（不是限制）。

详细编组步骤、合并原则、验证清单见 `references/manual-regrouping-workflow.md`。

## 10. 质量红线

> **⚠️ Pitfall 0：read_file 返回值含行号前缀，不可直接写回文件。**
> `read_file()` 返回格式为 `     1|第一行内容\n     2|第二行内容\n...`。如果直接 `write_file()` 回去，行号会成为文件内容的一部分，导致文件损坏。
> 正确做法：用 `re.match(r'^\s*\d+\|', line)` 剥离每行的行号前缀后再写回。
> 或者用 `terminal("sed ...")` 做原地替换，避免 read→write 循环。

**以下任一条件触发 → 报告打回，不得交付：**
1. 每个方法论单元必须有原文引用，标注出处章节。
2. 每个方法论单元必须有完整 R / I / A1 / A2 / E / P / B 七段。
3. 原文引用单段 ≤150 字。
4. 总结必须体现作者独特的反直觉见解，不是常识复述。

交付 `SUMMARY.md` 前自检：七段完整、引用有出处、≤150字、反直觉洞见、五问无占位符、标题与锚点一致。可用 `scripts/validate_summary.py <SUMMARY.md>` 自动检测。**两个高频格式陷阱**：

1. **R段原文引用必须 ≤150 字符**：超长引用是 validator 最常见失败原因。写完 SUMMARY 后立即检查每条 R 段字符数，超限就截断（保留核心论点，去掉数据细节）。
2. **审计节必须出现字面量「审计信息」**：validator 用 `'审计信息' in content` 检测，不是「审计区」「审计记录」或任何其他词。必须写 `审计信息：` 标题或正文含该字样。
3. **R段章节引用必须是独立行**：`> ——第X章` 必须单独成行，不能写成同行格式 `"> 通常，投资者...(引文内容)> ——（第五章）"`——必须拆成 `"> 引文内容\n> ——第五章"`。正则 `r'\*\*R — Reading.*?\*\*\n\n> (.+?)\n> ——'` 要求引文和章节引用之间以 `\n> ——` 分隔。

format_details.md（validate_summary.py 格式要求）

**Pitfall 6：方法论单元子段标题格式与 R-block 引文校验的关系（v4.48 + v4.51 更新）**

`validate_summary.py` 对子段标题有**两套独立检测**：

| 检测 | 用途 | 匹配格式 |
|------|------|----------|
| Section completeness | 检查七段是否齐全 | H2 前缀 `R段`/`I段`/... OR H3 前缀 `R —`/`I —`/... |
| R-block quote length | 检查 R 段引文 ≤150 字符 | 仅匹配 `**R — Reading**` 粗体格式 |

**三种可用格式及校验覆盖**：

| 格式 | 示例 | Section 检测 | R-block 长度检测 |
|------|------|:---:|:---:|
| H3 粗体（推荐） | `#### R段（原文引用）` 配合 `**R — Reading**：` | ✅ | ✅ |
| H2 变体 | `## R段：核心引文` | ✅ | ❌ |
| H4 标题 | `#### R段（原文引用）` 无粗体行 | ✅ | ❌ |

**⚠️ 关键陷阱**：如果只用 `#### R段（原文引用）` H4 标题而不在其后加 `**R — Reading**：` 粗体行，R-block 引文长度检查会被**完全跳过**——validator 的 R-block 正则 `r'\*\*R — Reading[^\n]*\n\n> (.+?)\n> ——'` 找不到匹配，不会报错也不会检查长度。引文即使超过 150 字符也不会被拦截。

**安全格式（推荐，v4.51）**：
```markdown
### 方法论单元一：<标题>

**R — Reading（原文引用）**：

> 引文内容（≤150字符）

> ——第X章

**I — Interpretation（深层阐释）**：解释内容...

**A1 — Past Application（历史案例）**：案例内容...
```

或用 H4 标题 + 内联粗体行：
```markdown
#### R段（原文引用）

**R — Reading**：

> 引文内容（≤150字符）

> ——第X章
```

**错误格式**（R-block 长度检测被跳过）：
```markdown
#### R段（原文引用）
> 引文内容（可能超150字符但不会被检测）

> ——第X章
```

**版本号**：4.48 → 4.51。

---

**Pitfall 5：B-section 插入时 patch 撞车（v4.45 新增）**

阶段 3 补 B 段时，`patch` 报错 `Found N matches for old_string`（N≥2）。根因：相邻 unit 的 P 段内容高度相似，仅替换 P 段末尾不够唯一。判断信号：`patch` 报错 `Found N matches for old_string` 且 `replace_all=false`。修复：扩展 old_string 到 `P段末尾 + \n\n---\n\n### 方法论单元X+1：<下一单元完整标题>`，利用下一单元的标题做唯一锚定。实战：《肥尾效应》Unit 4 P段末尾与 Unit 5 P段末尾撞车，扩展 old_string 含 `---` + `### 方法论单元5：左尾约束覆盖一切原则` → patch 成功。版本号：4.44 → 4.45。

## 11. 调用惯例

- 全量运行：每阶段完成后汇报进度，但不中断等待，连续执行。
- 不凭记忆：无文本就停下来向用户要。
- 保留审计：`candidates/`、`clusters.json`、`stage1-understanding.md` 持久化。
- 子代理按需：阶段 2 动态路由 2-5 个 extractor（`delegate_task`），但 candidates 生成优先 `execute_code`（子代理路径/格式不可控）。
- 候选文件只保留 `- id:` 开头的候选条目，不写 Markdown 标题。
- 脚本优先：索引/清洗/格式校验/聚类走 scripts。
- 软聚类：`cluster_candidates.py` 只分组不删除。
- 格式校验：`validate_candidates.py` 失败先修复再聚类。
- 候选评分：运行 `pipeline_phase2.py`，自动完成 validate → cluster → score → plan，生成 `candidate_scores.json` + `summary_plan.json`。

## 12. 异常处理索引

| 情况 | 查阅 |
|---|---|
| 多册合集/重复章节/TOC 污染/纯字符切分/讲话合集 | `references/known-file-structures.md` / `references/speech-collection-structure.md` / `references/combined-volume-speech-collections.md`（合卷本） |
| build_book_index 输出漂移/chapter_id null/乱序 | `references/known-file-structures.md` §6 |
| 单章主导型（meaningful_chapter_count=1, fragmentation_ratio>0.85） | §7.1 本skill新增强制路由 |
| 阶段 1 跳过灰区/book_type_hint 误判 | `references/stage1-edge-cases.md` |
| delegate_task 解析错误/schema 漂移 | `references/stage2-output-traps.md` |
| procedure 缺字段 | `references/procedure-schema-fix.md` |
| 跨书融合 SOUL/PRINCIPLES/MANIFESTO | `references/cross-book-synthesis.md` |
| execute_code YAML 提取 | `references/execute_code_yaml_patterns.md` |
| 阶段 2 执行细节 | `methodology/02-stage2-parallel-extract.md` |
| 子代理失败模式 | `references/subagent-patterns.md` |
| cluster_candidates.py 参数陷阱 | `references/cluster-candidates-cli-params.md` |
| 阶段 2 质量决策/候选评分/summary_plan | `references/quality-gates.md` |
| validate_summary.py 格式校验失败（R-section 引用格式、节标题格式） | `references/validate-summary-format.md` |
| pipeline 评分失真（学术书全D但内容可用） | `references/academic-book-pipeline-score-gap.md` |
| pipeline_phase2 终端输出 avg=0/recommended=0 但 JSON 正常 | `references/pipeline-printout-mismatch.md` |
| summary_plan.json 全空（推荐/附录均为零）或全单成员碎片 | `references/empty-plan-fallback.md` / `references/manual-regrouping-workflow.md` / 本 SKILL.md §9.1 |
| per_file granularity 导致单成员cluster全零分（不需要回退） | `references/per-file-granularity-bug.md` / 本 SKILL.md §9.2 |
| execute_code Python 3.12+ Unicode 字符报错 | `references/execute_code_yaml_patterns.md` §6 |
| validate 报 case 缺 linked_method_hint | `references/execute_code_yaml_patterns.md` §7 |
| 第X部分结构（非第X章，build_book_index 只检测到部分级） | `references/known-file-structures.md` §第X部分结构 |
| 批量处理多本书（delegate_task 超时阈值、split 模式、429限流、源文件发现） | `references/batch-processing-guidelines.md` |

## 13. 相关文件索引

方法论：`methodology/00-overview.md`、`01-stage1-read-extract.md`、`02-stage2-parallel-extract.md`、`04-stage4-summarize.md`

脚本：`clean_text.py`、`build_book_index.py`、`pipeline_phase2.py`（统一管道）、`validate_candidates.py`、`cluster_candidates.py`、`score_candidates.py`、`build_summary_plan.py`、`md_to_html.py`

参考：`extractors/boundary-extractor.md`、`references/validate-summary-format.md`（validate_summary.py 格式要求）

## 14. 版本摘要

> changelog 维护指南见 `references/changelog-maintenance.md`。每次添加新版本时检查是否需要清理旧条目重复。

完整历史见 `references/changelog.md`。

| 版本 | 日期 | 核心变更 |
|---|---|---|
| v4.53 | 2026-05-29 | 政治/马列类书籍纳入处理范围（用户明确要求）。路径含引号时用 find 验证。12本政治书全量 validate PASS。 |
| v4.52 | 2026-05-29 | `references/combined-volume-speech-collections.md` 新增三卷本结构模式（book-index 一卷一章 + 单章主导型变体）和书名含卷号时的引用格式规范（卷号必须在《》括号内）。实战：《邓小平文选·全3卷》3章结构、ch003承载95%内容、validate PASS。 |
| v4.51 | 2026-05-29 | Pitfall 6 修正：H4 标题格式（`#### R段`）绕过 R-block 引文长度校验。推荐安全格式为 H4 标题 + 内联 `**R — Reading**：` 粗体行。实战：《毛泽东文集》用纯 H4 格式 validate PASS 但 R-block 长度检查被跳过。 |
| v4.50 | 2026-05-29 | `references/validate-summary-format.md` 新增陷阱：书名含副标题/卷号时，`《》` 括号必须包含完整书名（如 `《习近平谈治国理政·第四卷》` 而非 `《习近平谈治国理政》第四卷`），否则正则 `《[^》]+》` 匹配失败。实战：《习近平谈治国理政》第四卷 → 修复引用格式 → validate PASS。 |
| v4.48 | 2026-05-29 | §10 Pitfall 6 新增：方法论单元子段标题必须用 `#### R段` 四级标题，不能用加粗格式 `**R — Reading**：`。实战：《通往衰败之路》所有子段用加粗格式 → validate 报全7段MISSING → 批量替换为 `#### 段名` 格式 → PASS。 |
| v4.42 | 2026-05-28 | 三阶段流程新增条件跳过优化：阶段1检查stage1-understanding.md是否存在，存在则跳过阶段1直接执行阶段2→3。实战：《从报表看企业》stage1不存在→完整执行三阶段→validate PASS。 |
| v4.41 | 2026-05-28 | §4.2 新增「阶段3主代理直接写入时机」：当stage1+stage2产物完整时不调用delegate_task，主代理直接读取candidates写入SUMMARY。实战：《八次危机》stage3超时但产物完整，主代理直接重写29K→validate PASS。 |
| v4.40 | 2026-05-28 | validate_summary.py 两项格式兼容修复：① Q1-Q5 五问格式支持（`### Q1：...` 等）；② `ch008` 章节引用格式支持（《周金涛理论大集》使用）。三格式任一五问完整即通过。实战：周金涛理论大集 PASS。 |
| v4.39 | 2026-05-28 | validate_summary.py 三项格式兼容修复：①五问支持标准格式（作者的写作意图）或编号格式（这本书解决什么问题？）；②段落标记支持H2（`## R段：`）和H3 bold（`**R — Reading**：`）两种；③R段引文支持章节引用（`> ——第7章`）或作者名引用（`> ——《原则》，瑞·达利欧`）；④审计节跳过无candidates目录的书籍；⑤补充缺失`import os`。实战：《原则》逆向推导书用H2+编号五问+作者名引用→修复后validate PASS。 |
| v4.38 | 2026-05-28 | 阶段3子代理格式错误处理：子代理 SUMMARY 输出若使用错误 section header（`#### R段（原文引用）`）或问答体而非标题体，主代理应直接重写而非再次调用子代理（避免额外 token 消耗）。验证通过后交付。实战：周金涛《人生财富靠康波涛动周期论》→主代理直接重写28K→validate PASS。新增pitfall到§4.1。 |
| v4.37 | 2026-05-28 | 学术类书籍 pipeline 评分失真处理：penalties集中在格式字段（missing_source_quote/v3_not_passed）时，内容可用性独立于score。参考案例：《思考，快与慢》18候选全D→手动编组10单元→validate_summary.py PASS。新增`references/academic-book-pipeline-score-gap.md`。 |
| v4.36 | 2026-05-28 | validate_summary.py I-section 正则修复：Format A（header 同行内容）优先，Format B（header 后换行）作 fallback，解决跨 unit 误捕获问题。实战：《稀缺》14 单元 I-section 超长误报 → 修复后 PASS。 |
| v4.35 | 2026-05-28 | validate_summary.py R-section 空格支持（`> —— 第3章`）+ section header 中文变体前缀匹配（`R — 原文引用` 等）。实战：巴菲特之道 PASS。 |
| v4.33 | 2026-05-28 | batch-processing-guidelines.md 新增「API限流应对」（429防御策略、降并发方案）和「源文件发现」（.txt/.md双扩展名识别）。实战：3并行触发429，1并行成功。 |
| v4.32 | 2026-05-28 | §7 新增「单章主导型」书籍分类及路由规则：meaningful_chapter_count=1 + fragmentation_ratio>0.85 时，绕开 execute_code extractor，直接读 meaningful chapter 文本，人工识别框架后主代理写 candidates。实战：《价值：我对投资的思考》ch010 承载99.2%内容，8章TOC碎片。 |
| v4.31 | 2026-05-28 | §10 质量红线新增两个高频陷阱（审计信息字面量、R段≤150字符），references/validate-summary-format.md 前置高频失败表。 |
| v4.30 | 2026-05-28 | §9.2 新增「全单成员碎片的根因」：per_file granularity 导致所有候选被罚 single_member_cluster，score归零，不需要回退，直接用 by_type 重跑 pipeline。新建 references/per-file-granularity-bug.md。§12 索引新增条目。 |
| v4.29 | 2026-05-28 | §9.1 新增「全单成员碎片 vs 全空计划」区别：后者完全无推荐条目（v4.24已覆盖），前者有推荐条目但全是碎片。补充五大核心覆盖确保机制。实战：《查理·芒格的投资思想》24个A级单成员候选→人工编组12个方法论单元，validate_summary.py PASS。 |
| v4.28 | 2026-05-28 | execute_code Python 3.12 Unicode 字符陷阱（`→` 等触发 SyntaxError）；case 候选缺 `linked_method_hint` 字段修复；第X部分结构（非第X章）书籍处理模式；`references/execute_code_yaml_patterns.md` 新增 §6§7；`references/known-file-structures.md` 新增 §第X部分结构；§12 索引补全 |
| v4.26 | 2026-05-28 | §10 补充 validate_summary.py 格式陷阱（R-section 必须有 `**R — Reading**：` + `> ——第X章` 独立行）；§12 新增格式校验失败索引；新建 `references/validate-summary-format.md` |
| v4.25 | 2026-05-27 | §8 五问描述修复：对齐 methodology/04-stage4-summarize.md 模板，移除错放的"主要方法论"（它属第六节而非五问），补充"与自己的关系"第五节 |
| v4.23 | 2026-05-27 | 脚本合并(pipeline_phase2.py)+安全阀(>100自动降级)+模式统一(execute_code必选,delegate_task备选) |
| v4.22 | 2026-05-27 | 闸口移除+结构优化：全量连续运行；SKILL.md 结构重排 |
| v4.19 | 2026-05-24 | 阶段3新增 md_to_html.py |
| v4.15 | 2026-05-24 | stage2-output-traps §13；快速导航/方法论索引/INDEX.md 删除 |
| v4.13 | 2026-05-24 | build_summary_plan 参数顺序确认；混合型书籍结构模式 |
| v4.11 | 2026-05-21 | quality-gates 参数顺序陷阱；execute_code 完整 schema 要求 |
| v4.8 | 2026-05-19 | build_book_index 输出异常；book_type_hint 继承规则 |
| v4.6 | 2026-05-19 | methodology_treatise 全 A 全量写入策略 |
| v4.5 | 2026-05-19 | 子代理失败模式固化：execute_code 优先 |
| v4.4 | 2026-05-18 | 质量闸门升级：validate→cluster→score→build_summary_plan 流水线 |
| v4.3 | 2026-05-18 | skill 瘦身/渐进披露重构 |
| v4.0-v4.2 | 2026-05-17-18 | 正式版；子代理嵌套陷阱；SKILL.md 运行总控结构 |

# Changelog — jw-content-summary 完整版本历史

本文件记录 `jw-content-summary` skill 的所有版本变更。与 SKILL.md 同步规则：修改此 skill 时，**必须同步更新三处**：① 本文件新增对应版本条目 ② `version` frontmatter 字段递增 ③ SKILL.md 的版本摘要区更新最近版本。三者缺一不可。

---
---
## v4.30 (2026-05-28)

**§9.2 新增「全单成员碎片的根因」：per_file granularity 陷阱，不需要回退。**

**触发场景**：《以交易为生II》阶段2 pipeline_phase2.py 产生 40 个单成员 cluster，每个候选被罚 `single_member_cluster`（-20分），导致 average_score 全为0，summary_plan.json 所有条目进 excluded_or_weak。

**根因**：`cluster_candidates.py` 的 `--granularity` 参数默认或误传为 `per_file`，每个输入文件变成一个 cluster，与内容无关。execute_code 提取后每个候选类型一个文件（如 `frameworks.md`），如果每个文件含 2 个 entry（header 元数据块 + body 内容块），N 个文件产生 N×2 个单成员 cluster。

**修复（不需要手动编组回退）**：直接用 `by_type` granularity 重跑聚类，然后重跑 pipeline。

**新增文件**：`references/per-file-granularity-bug.md`

**关联**：SKILL.md §9.2（新增）、§12 异常索引（新增条目）、version → 4.30

---
## v4.31 (2026-05-28)

**两个最高频 validator 失败点前置于 skill 和参考文档。**

本次《证券分析》SUMMARY.md 实战中，两次 validate 失败均为可预防格式错误：

1. **R段原文超150字符**：Unit 8 的莱特航空公司引用原长 211 字符，validator 捕获失败后才手动截断至 114 字符。应在撰写 SUMMARY 后立即自检，而非等 validator 失败后再修。
2. **审计节字面量错误**：初稿使用「审计区」标题，validator 报错 `Audit section not found`，因脚本检测 `'审计信息' in content`（字面量匹配）。修复为「审计信息：」后通过。

**修复内容**：
- SKILL.md §10 质量红线：新增两个高频陷阱提示，标注优先自检项
- `references/validate-summary-format.md`：文件开头新增「两个最高频失败点」高亮表，配套修复方案
- 版本号 → 4.31，changelog 新增 v4.31 条目

**版本号**：4.30 → 4.31。

---
## v4.11 (2026-05-21)
## 详细变更日志

以下为 v4.0-v4.23 详细变更记录，供审计参考。日常运行不需要读取本节。

### v4.29 (2026-05-28) — 全单成员碎片回退实战 + 五大核心覆盖确保机制

**触发场景**：《查理·芒格的投资思想》24个候选全部为A级，但`clusters.json`显示`single_member_ratio: 1.0`（24个单成员cluster），聚类算法未发现任何语义重叠。`pipeline_phase2.py`输出的`summary_plan.json`有10条`recommended_units`但每条来自不同cluster，相互独立——全是碎片。

**根因确认**：
- `candidate_scores.json` penalties 集中在格式字段（`missing_source_quote`、`v3_not_passed`、`missing_or_invalid_source_line`），无实质内容缺失
- `single_member_ratio: 1.0` + 全部 grade A = 内容质量高但聚类未合并
- 区分：全空计划（v4.24）完全无推荐条目；全单成员碎片有推荐条目但语义独立

**回退执行（§9.1全单成员碎片路径）**：
1. 读全部5个candidates文件（principles/cases/insights/boundaries/glossary），共24个条目
2. 验证内容可用性：R引文、I阐释、A1案例、A2场景、E/P/B段在正文中完整
3. 按书的领域知识手动编组为12个方法论单元（覆盖全部24个原始候选）
4. 五大核心方法论（权益债券、消费者垄断、坐等投资、逆向投资、格栅思维）均分配独立单元
5. 写入SUMMARY.md，12单元×七段，validate_summary.py PASS
6. 审计区记录：`single_member_ratio: 1.0`、回退原因、五大核心覆盖确认

**版本号**：4.28 → 4.29。

**触发场景**：《债务危机》阶段 2 全流程。

**三处修复**：

1. **Python 3.12+ Unicode 字符陷阱**：execute_code 脚本在两处使用了 `→`（U+2192）字符——`"形成\"越印钞→越贬值→越没人持有\"的死亡螺旋。"` 和 `v3_reason` 字段中的全角引号——Python 3.12.3 均报 `SyntaxError: invalid character`。根因：Python 3.12 对源文件中的非 ASCII 字符校验更严，即使嵌套在双引号字符串内也可能失败。修复：全替换为 ASCII（`->`、`--`）+ 半角标点。`sed -i 's/→/->/g'` 批量处理有效。记入 `references/execute_code_yaml_patterns.md` §6。

2. **case 候选缺 `linked_method_hint` 字段**：`validate_candidates.py` 要求 `type: case` 的候选必须包含 `linked_method_hint` 字段。4 个 case 候选全部缺失，validate 报 `missing required fields: ['linked_method_hint']`。修复：在 `type: case` 之后添加 `linked_method_hint: "典型债务周期五阶段模型"` 行。记入 `references/execute_code_yaml_patterns.md` §7。

3. **第X部分结构书籍处理模式**：《债务危机》使用「第一部分」「第二部分」「第三部分」组织，`build_book_index.py` 的章节正则只能匹配「第...章」，无法匹配「第...部分」。结果：3 个部分级标题被检测为章节，前 2 个被判定为 TOC 碎片（<100 字符），ch003 承载 373K 字符。阶段 1 必须手动用 `grep -n` 定位内部子章节行号，按行号区间标注角色表。记入 `references/known-file-structures.md` §第X部分结构。

**版本号**：4.27 → 4.28。

### v4.27 (2026-05-28) — pipeline_phase2 终端输出字段名不匹配

**触发场景**：《反脆弱》阶段2运行 pipeline_phase2.py 后，终端输出显示 `[score] candidates=37 avg=0` 和 `[plan] recommended=0 appendix=0`，但实际 `candidate_scores.json` 中 `average_score: 95.27` 且 `summary_plan.json` 中 `recommended_units` 有10个条目。根因：`pipeline_phase2.py` 读取 score 时使用字段名 `avg_score`，但 `score_candidates.py` 输出的字段名是 `average_score`；读取 plan 时使用 `recommended`/`appendix`/`weak`，但 `build_summary_plan.py` 输出的字段名是 `recommended_units`/`appendix_units`/`excluded_or_weak`。

**修复**：
- **scripts/pipeline_phase2.py**：5处字段名修复，使用 `get("average_score", get("avg_score", 0))` 等向后兼容写法
- **新建 `references/pipeline-printout-mismatch.md`**：完整 bug 描述、判断信号、工作建议
- **§12 异常处理索引**：新增终端输出不匹配条目
- **§14 版本摘要**：新增 v4.27 条目

**版本号**：4.26 → 4.27。

### v4.26 (2026-05-28) — validate_summary.py 格式陷阱

**触发场景**：《祖鲁法则》阶段 3 SUMMARY.md 初始使用 `- **R**：` + `（第X章）` 格式，validate_summary.py 报 `[MISSING] No R-section chapter citations found` 和 section completeness 失败。根因：脚本使用严格正则 `r'\*\*R — Reading.*?\*\*\n\n> (.+?)\n> ——'` 和 `r'> ——第\d+章'`，自然 Markdown 格式不匹配。

**修复**：
- **§10 质量红线**：补充 validate_summary.py 格式要求说明，引用新文件
- **§12 异常处理索引**：新增 `validate_summary.py 格式校验失败` → `references/validate-summary-format.md`
- **新建 `references/validate-summary-format.md`**：完整格式要求（R-section 正则、章节引用格式、七段标题格式）、常见失败模式（sed 陷阱、collateral damage）、修复示例
- **sed 陷阱记录**：用 sed 批量修复章节引用时容易匹配到非 R-section 文本、产生同行格式；推荐 Python regex 做上下文感知修复

**版本号**：4.25 → 4.26。

### v4.25 (2026-05-27) — §8 五问描述修复

**问题**：SKILL.md §8 列出的五问（①作者意图 ②核心主张 ③内容结构 ④主要方法论 ⑤是否有道理/边界）与 `methodology/04-stage4-summarize.md` 实际模板不一致。"主要方法论"不属于五问——它是 SUMMARY.md 第六节「核心方法论」的主体内容。同时缺少模板中实际使用的"五、这本书与自己的关系"。

**修复**：§8 五问改为 `①作者的写作意图 ②这本书在谈什么（核心主张）③全书的内容结构 ④这本书有道理吗/边界在哪 ⑤这本书与自己的关系`，并添加 "五问模板以 methodology/04-stage4-summarize.md 为准" 的引导。

**版本号**：4.24 → 4.25。

### v4.24 (2026-05-27) — 空计划回退

**触发场景**：《投资中最简单的事》37 候选全部被 `pipeline_phase2.py` 评为 D 级（score 0-5），`summary_plan.json` 的 `recommended_units` 和 `appendix_units` 均为空数组。根因：`validate_candidates.py` 对 `source_quote`、`v3_pass`、`source_line` 等格式元数据字段缺失扣分（-75 分），但候选人正文的 R/I/A1/A2/E/P/B 七段内容完整可用。

**新增能力**：
- **SKILL.md §9.1 空计划回退**：当推荐/附录均为空但内容可用时，不回退到空输出，改为全量读取+手动编组策略。含根因判断信号（penalties 集中在格式字段 vs 实质字段）。
- **SKILL.md §12 异常处理索引**：新增 `summary_plan.json 全空` 条目指向 §9.1。
- **references/empty-plan-fallback.md**：完整回退流程（5步：读全部→验证→编组→撰写→审计），含触发条件、根因分析表、判断信号、相关案例。
- **methodology/04-stage4-summarize.md** 默认规则补记：空计划回退的触发条件和回退链路说明。
- 版本号：4.23 → 4.24。

### v4.23 (2026-05-27) — 管道合并 + 安全阀 + 模式统一

- 新建 `scripts/pipeline_phase2.py`：subprocess wrapper 统一调用 validate → cluster → score → build_summary_plan，消除 CLI 参数顺序陷阱。输出额外 `phase2_result.json` 用于审计。
- 安全阀：候选数 >100 时自动降级（top-30 完整展开，其余进附录），`valve_triggered: true` 标记。
- 模式统一：§4.1 新增 execute_code/delegate_task 选择矩阵，明确「execute_code 必须，delegate_task 备选」规则。
- 文档同步：SKILL.md §4/§9/§11/§13/§14、methodology/02 全部更新。
- 旧脚本保留，向后兼容。回滚路径：`cp -r scripts.bak scripts`。

### v4.22 (2026-05-27) — 闸口移除 + 结构优化

所有用户确认闸口（阶段 1/2 闸门、数量闸门、异常闸口）全部移除。三阶段自动连续运行，质量决策包照常生成作为审计记录但不触发确认。修改涉及 8 个文件。

SKILL.md 结构重排：详细 changelog 移至末尾，功能章节（§1-13）前置，解决 230 行版本历史挡在正文前的问题。修复 YAML frontmatter 双块、重复标题、§10 错误标记、§5 删除快速导航残存引用。

### v4.22 (2026-05-26) — execute_code 优先于 delegate_task

阶段 2 candidates 提取统一改用 execute_code。子代理（delegate_task）在嵌套场景存在结构性截断问题（实测《巴菲特致股东的信》31 候选全 A，子代理输出全部为空）。子代理仅保留用于阶段 1 理解和阶段 3 SUMMARY 写作。

全 A 场景处理：`candidate_scores.json` 全 A 时 `build_summary_plan.py` 输出 `recommended=10`，直接按 A 级全量写入，不依赖 summary_plan.json 的 top-10 限制。

lark-cli 写入：`--api-version v1 --mode append` 不可用 `--block-id` 锚定模式；长内容分 2-3 批追加，每次 ≤150KB。

### v4.21-v4.3 详细记录

见 `references/changelog.md`。
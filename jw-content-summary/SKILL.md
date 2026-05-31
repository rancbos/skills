---
name: jw-content-summary
description: 将一本书或长文蒸馏为可实操的方法论单元（R/I/A1/A2/E/P/B 七段），含压力测试和关联方法论。适用于"帮我总结这本书""帮我看看这本书讲了啥""拆解方法论""提炼核心框架""summarize this book""这本书值不值得读""这篇文章的核心观点""帮我拆解一下这篇文章""拆解研报""深度阅读""distill the methodology""帮我写读书笔记""读后感""这本书讲了什么""帮我拆解这本书"等场景。不适用于虚构作品。
agent_created: true
version: 4.68
---


> 完整版本历史（v4.0-v4.68）见 `references/changelog.md`。下方仅保留最近 10 个版本。

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
- 阶段 2：优先 `execute_code` 直接从 chapters 文本提取（子代理仅保留阶段 1 理解分析和阶段 3 SUMMARY 写作）。按 §6 书籍类型表选择 2-5 种候选类型（framework/principle/case/boundary/procedure/glossary/insight）提取，不固定全跑。
- 阶段 2 后运行 `python3 scripts/pipeline_phase2.py <candidates_dir> <output_dir>`，一次生成 `clusters.json` + `candidate_scores.json` + `summary_plan.json`（替代旧 4 脚本分步调用，消除 CLI 参数顺序陷阱）。
- 阶段 3 以 `summary_plan.json` 为主，不重复读全部 candidates 正文。阶段 1 四问（理解策略，agent 内部）与阶段 3 五问（导读策略，写入 SUMMARY）目的不同，不得混用——详见 `methodology/04-stage4-summarize.md`。

### 4.1 阶段 2 提取方式选择

| 场景 | 方式 | 原因 |
|------|------|------|
| 标准书籍（<50 章） | `execute_code` | 确定性输出，格式可控 |
| 超大书籍（>50 章） | `execute_code`（分批） | 分 2-3 批运行，每批 return YAML |
| 章节结构复杂（混合型） | `execute_code` + REGEX | 先 REGEX 切分边界，再 execute_code 提取 |
| `execute_code` 超时（>5min） | `delegate_task`（备选 fallback） | 仅作回退方案，需额外 validation |
| 阶段 1 理解分析 | `delegate_task` | 读取结构文件，风险低 |
| 阶段 3 SUMMARY 写作 | **主代理直接写入**（delegate_task 超时率 ~100%，不推荐） | 主代理上下文已有 candidates，直接写入更快更可靠。delegate_task 仅在主代理上下文窗口不足时考虑。**Pitfall**：子代理若输出格式错误（如错误 section header `#### R段（原文引用）`、问答体五问、双层标题重复），主代理应**直接重写**而非再次调用子代理。 |

### 4.2 阶段 3 主代理直接写入时机（v4.49）

**经验规律（新增）**：delegate_task 在阶段 3 SUMMARY 写作中**一致超时 600s**，无论并发数量（1-3并行均触达）。当前 session 多次确认：薛兆丰经济学讲义（116候选全D）、当代中国政府与政治（candidates空）均因 delegate_task 超时未完成。**阶段 3 强烈优先主代理直接写入**，不要等子代理超时再回退。

**触发条件（需同时满足）**：
1. `stage1-understanding.md` 存在
2. `candidates/` 目录存在且有内容（或 stage1 足够支撑手工编组）
3. `summary_plan.json` 存在（含推荐/附录条目）——即使全D级，只要正文七段完整可用

**不需要调用 delegate_task 的场景**：
- stage1+stage2 完整，stage3 超时后重试 → 主代理直接写入
- stage3 validate 失败（格式错误）→ 主代理直接重写
- 全单成员碎片 §7.3 回退，手动编组后主代理写入
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

### 4.3 阶段 2.5 连接扫描（v4.54 新增）

> 来源：deep-learning skill 的 Luhmann Scan。阶段 2 提取 candidates 后，反向扫描潜在连接。

**时机**：阶段 2 candidates 生成后、`pipeline_phase2.py` 运行前。

**流程**：对每个提取出的 candidate，执行三项扫描：

1. **前置依赖**：要理解这个概念，还需要书中的哪些其他概念？
   - 例：提取了"安全边际"，前置依赖是"内在价值"和"市场先生"
   
2. **潜在连接**：这个概念和书中哪些其他概念有关？
   - 例："安全边际"与"能力圈"是互补关系，与"追涨杀跌"是对立关系

3. **方法论发现**：这个概念是否附带可执行的方法（how）？
   - 例：书中提到"安全边际=内在价值×70%"，这是一个可执行的计算方法

**输出**：在 candidate 的元数据中增加 `luhmann_connections` 字段（避免与 extractor 的 `related` 字段冲突）：

```yaml
- id: pr-01
  title: 安全边际
  luhmann_connections:
    requires: ["fw-01 内在价值", "pr-02 市场先生"]
    relates_to: ["pr-03 能力圈", "bd-01 追涨杀跌"]
    enables_method: ["pc-01 安全边际计算公式"]
```

**注意**：连接扫描是轻量级的，不需要额外调用 extractor。主代理读取 candidates 后直接标注，**写回对应的 `candidates/*.md` 文件的 YAML frontmatter 中**（如 `principles.md` 中对应候选的 `id:` 行下方追加 `luhmann_connections:` 块）。如果 candidates 目录不存在，将 luhmann_connections 直接写入 SUMMARY.md 对应方法论单元的元数据区。

## 5. 输出结构

> 生产文件统一输出到源文件所在目录：`<源文件.txt所在目录>/<书名>/`

```text
<书名>/
├── SUMMARY.md                # 最终产出
├── cleaned_text.txt          # 预处理（可选保留）
├── preprocess/               # book-index.json + chapters/ + snippets/（可选保留）
├── stage1-understanding.md   # 阶段1（可选保留）
├── candidates/               # 阶段2（可选保留，审计用）
└── clusters.json / candidate_scores.json / summary_plan.json  # pipeline（可选保留，审计用）
```

核心产出只有 `SUMMARY.md`。其余文件为中间产物，可选保留用于审计和回滚，不强制输出。

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

### 6.1 单章主导型识别与路由（v4.32）

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
6. **走 §7.3 回退写 SUMMARY**（如推荐/附录均为空）

单章主导型不需要 `delegate_task` 提取——主代理直接读文本、识别结构、写候选，速度更快、质量更高。

### 6.2 长书与复杂结构策略

≥3 万字进入长书模式（经验值：3 万字约 10+ 章，单次 execute_code 处理容易超时或丢失上下文）。规则：先脚本切章→阶段 1 只读索引→阶段 2 按章节角色定向分配 extractor→阶段 3 读 `clusters.json` 不回读全部候选。禁止每块固定跑全部 extractor。

| 模式 | 适用 | 做法 |
|---|---|---|
| 全局提取 | 章节均匀、结构简单 | snippets 全部分配给必要 extractor |
| 定向分块 | 章节角色差异大 | 按章节 role 分配给最匹配 extractor |

边界案例见 `references/known-file-structures.md` / `references/stage1-edge-cases.md`。

## 7. 全量自动运行（闸口已移除 v4.22）

三阶段连续执行，不设用户确认闸口。阶段 1/2 结束后直接进入下一阶段，阶段 3 自检后交付。全 A / 全 C 场景均自动处理：全 A 全量写入，全 C 以附录池为主。质量决策包照常生成作为审计记录，但不再触发用户确认。

### 质量门控（v4.62 更新）

**纯质量门控，不设数量上限**：只评判方法论应不应该输出，不限制输出数量。

- A/B 级 + 平均分 ≥65 → `recommended_units`（完整 R/I/A1/A2/E/P/B 七段展开）
- B/C 级 → `appendix_units`（简写或附录）
- D 级/低分 → `excluded_or_weak`（不输出）

`summary_plan.json` 记录推荐/附录/排除三类决策。`phase2_result.json` 可审计全部阶段数据。

### 7.3 碎片化计划回退（v4.30）

**先检查 §7.4 granularity 问题**——大多数全单成员碎片是 `per_file` granularity 导致的，不需要手动编组。只有 §7.4 修复后仍然碎片化时，才走以下回退流程。

当满足以下任一条件时，不走 `summary_plan.json` 的推荐/排除逻辑，改为全量读取全部候选人文件后手动编组：

- **全空计划**：`recommended_units` 和 `appendix_units` 均为空（v4.24 已覆盖）
- **全单成员碎片**：`clusters.json` 显示 `single_member_ratio: 1.0`，即所有 cluster 都是单成员。此时即使 `summary_plan.json` 有推荐条目，它们也都是相互独立的碎片——需要人工阅读全部候选人、按主题合并为 12-16 个方法论组。**不要只读 plan 的 recommended 列表**。

详细编组步骤、合并原则、验证清单见 `references/manual-regrouping-workflow.md`。

### 7.4 全单成员碎片的根因（v4.30）

**大多数情况下，这不是"聚类算法未能发现语义重叠"，而是 `cluster_candidates.py` 的 `granularity` 参数设置错误。**

`cluster_candidates.py` 有两个 granularity 选项：
- `by_type`（正确）：按候选类型语义分组
- `per_file`（错误陷阱）：每个输入文件变成一个 cluster，与内容无关

**默认阈值**：0.35（v4.63 从 0.58 降低）。经验值——原 0.58 对信件汇编/案例集类书籍太高（candidates 间 title 独特、keywords 无重叠，最高相似度仅 0.1）。0.35 允许 keyword_overlap 0.5 或 title_similarity 0.6 即可合并。方法论专著/学术书可在调用时传 0.58 保持精度。

**判断信号**：`clusters.json` 中 `single_member_ratio: 1.0` + `candidate_scores.json` 中 penalties 集中在 `single_member_cluster`（-20 分/个）而非实质内容缺失。

**修复**：直接用 `by_type` granularity 重新跑 pipeline，不需要手动编组。详见 `references/per-file-granularity-bug.md`。

## 8. 质量红线

> **⚠️ Pitfall 0：read_file 返回值含行号前缀，不可直接写回文件。**
> `read_file()` 返回格式为 `     1|第一行内容\n     2|第二行内容\n...`。如果直接 `write_file()` 回去，行号会成为文件内容的一部分，导致文件损坏。
> 正确做法：用 `re.match(r'^\s*\d+\|', line)` 剥离每行的行号前缀后再写回。
> 或者用 `terminal("sed ...")` 做原地替换，避免 read→write 循环。

**以下任一条件触发 → 报告打回，不得交付：**
1. 每个方法论单元必须有原文引用，标注出处章节。`[validator: R-block 引文 + 章节引用正则]`
2. 每个方法论单元必须有完整 R / I / A1 / A2 / E / P / B 七段。`[validator: section completeness 检测]`
3. 原文引用单段 ≤150 字（经验阈值：150 字约 2-3 句话，足够呈现一个核心论点；超过此长度通常包含多个论点或背景铺垫，应拆分或精简）。`[validator: R-block quote length 检测]`
4. 总结必须体现作者独特的反直觉见解，不是常识复述。`[人工判断，validator 不覆盖]`

交付 `SUMMARY.md` 前自检：七段完整、引用有出处、≤150字、反直觉洞见、五问无占位符、标题与锚点一致。可用 `scripts/validate_summary.py <SUMMARY.md>` 自动检测。**两个高频格式陷阱**：

1. **R段原文引用必须 ≤150 字符**：超长引用是 validator 最常见失败原因。写完 SUMMARY 后立即检查每条 R 段字符数，超限就截断（保留核心论点，去掉数据细节）。
2. **审计节必须出现字面量「审计信息」**：validator 用 `'审计信息' in content` 检测，不是「审计区」「审计记录」或任何其他词。必须写 `审计信息：` 标题或正文含该字样。
3. **R段章节引用必须是独立行**：`> ——第X章` 必须单独成行，不能写成同行格式 `"> 通常，投资者...(引文内容)> ——（第五章）"`——必须拆成 `"> 引文内容\n> ——第五章"`。正则 `r'\*\*R — Reading.*?\*\*\n\n> (.+?)\n> ——'` 要求引文和章节引用之间以 `\n> ——` 分隔。

**⚠️ Pitfall 7（v4.62-v4.63）：粗体格式正则 + source_line 年份格式 + R-section 年份引用。**

三个层面的格式兼容问题，均在巴菲特致股东的信实战中发现：

(a) `validate_candidates.py`、`cluster_candidates.py`、`score_candidates.py` 的 `re.split()` 正则只匹配 `- id:` 不匹配 `- **id**:` 粗体格式，导致 pipeline 只处理部分候选。修复：正则添加 `\\*{0,2}` 支持。

(b) `validate_candidates.py` 和 `score_candidates.py` 的 `source_line` 验证只接受正整数。信件合集的描述性引用（"1984年致股东信"、"ch017"、"第三章"）全部报 `invalid_source_line`。修复：验证函数扩展支持年份、章节名、中文描述。

(c) `validate_summary.py` 的 R-section 章节引用正则只匹配"第X章"格式，不匹配"第1965年信"格式。修复：新增 `r_year_citations` 正则。

详见 `references/bold-format-regex-pitfall.md` 和 `references/letter-compilation-pitfalls.md`。

格式细节（正则、H2/H3/H4 标题变体、chXXX 引用格式、sed 陷阱等）见 `references/validate-summary-format.md`。两个高频实现陷阱：

**⚠️ Pitfall 6（v4.51）**：只用 `#### R段` H4 标题而不加 `**R — Reading**：` 粗体行，R-block 引文长度检查会被**完全跳过**。安全格式：H4 标题 + 内联粗体行。详见 `references/validate-summary-format.md` §H4 标题变体。

**⚠️ Pitfall 5（v4.45）**：B-section 插入时 `patch` 报 `Found N matches`，因相邻 unit P 段相似。修复：扩展 old_string 含下一单元标题做唯一锚定。详见 `references/validate-summary-format.md`。

## 9. 调用惯例

- 全量运行：每阶段完成后汇报进度，但不中断等待，连续执行。
- 不凭记忆：无文本就停下来向用户要。
- 保留审计：`candidates/`、`clusters.json`、`stage1-understanding.md` 持久化。
- 子代理按需：阶段 2 动态路由 2-5 个 extractor（`delegate_task`），但 candidates 生成优先 `execute_code`（子代理路径/格式不可控）。
- 候选文件只保留 `- id:` 开头的候选条目，不写 Markdown 标题。
- 脚本优先：索引/清洗/格式校验/聚类走 scripts。
- 软聚类：`cluster_candidates.py` 只分组不删除。
- 格式校验：`validate_candidates.py` 失败先修复再聚类。
- 候选评分：运行 `pipeline_phase2.py`，自动完成 validate → cluster → score → plan，生成 `candidate_scores.json` + `summary_plan.json`。

## 10. 异常处理索引

| 情况 | 查阅 |
|---|---|
| 多册合集/重复章节/TOC 污染/纯字符切分/讲话合集 | `references/known-file-structures.md` / `references/speech-collection-structure.md` / `references/combined-volume-speech-collections.md`（合卷本） |
| build_book_index 输出漂移/chapter_id null/乱序 | `references/known-file-structures.md` §6 |
| 单章主导型（meaningful_chapter_count=1, fragmentation_ratio>0.85） | §6.1 单章主导型识别与路由 |
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
| summary_plan.json 全空（推荐/附录均为零）或全单成员碎片 | `references/empty-plan-fallback.md` / `references/manual-regrouping-workflow.md` / 本 SKILL.md §7.3 |
| per_file granularity 导致单成员cluster全零分（不需要回退） | `references/per-file-granularity-bug.md` / 本 SKILL.md §7.4 |
| execute_code Python 3.12+ Unicode 字符报错 | `references/execute_code_yaml_patterns.md` §6 |
| validate 报 case 缺 linked_method_hint | `references/execute_code_yaml_patterns.md` §7 |
| 第X部分结构（非第X章，build_book_index 只检测到部分级） | `references/known-file-structures.md` §第X部分结构 |
| 批量处理多本书（delegate_task 超时阈值、split 模式、429限流、源文件发现） | `references/batch-processing-guidelines.md` |
| Token优化（SKILL.md瘦身、索引精简、阶段2嵌入） | `references/token-optimization-patterns.md` |
| book-index.json 截断验证（first_paragraphs=200, last_paragraphs删除） | `references/book-index-truncation-validation.md` |
| 信件汇编类书籍（source_line年份格式、聚类不合并、R-section年份引用） | `references/letter-compilation-pitfalls.md` |

## 11. 相关文件索引

方法论：`methodology/00-overview.md`、`01-stage1-read-extract.md`、`02-stage2-parallel-extract.md`、`04-stage4-summarize.md`

脚本：`clean_text.py`、`build_book_index.py`、`pipeline_phase2.py`（统一管道）、`validate_candidates.py`、`cluster_candidates.py`、`score_candidates.py`、`build_summary_plan.py`

参考：`extractors/boundary-extractor.md`、`references/validate-summary-format.md`（validate_summary.py 格式要求）、`references/cognitive-depth-patterns.md`（v4.54 认知深度增强模式来源与设计决策）、`references/token-optimization-patterns.md`（v4.68 Token 优化模式）

## 12. 版本摘要

> changelog 维护指南见 `references/changelog-maintenance.md`。每次添加新版本时检查是否需要清理旧条目重复。

完整历史见 `references/changelog.md`。下方仅保留最近 10 个版本。

| 版本 | 日期 | 核心变更 |
|---|---|---|
| v4.68 | 2026-05-31 | book-index.json 精简验证固化：巴菲特书 pipeline 验证（62 candidates, avg=89.52, 61 recommended），first_paragraphs 截断 200 字符 + last_paragraphs 删除 = 零质量损失，book-index 255KB→151KB（-40.6%）。 |
| v4.67 | 2026-05-31 | Token优化续：changelog.md去重（539→467行）、SKILL.md版本表裁至10条、methodology/04删除过时Top 10节、阶段2嵌入措辞强化。 |
| v4.66 | 2026-05-31 | Token优化：SKILL.md changelog移出（546→334行）、book-index.json索引精简（118→76KB）、阶段2嵌入强制化。详见 `references/token-optimization-patterns.md`。 |
| v4.65 | 2026-05-31 | 精简输出：删除SUMMARY.html，核心产出只有SUMMARY.md，删除md_to_html.py引用。 |
| v4.64 | 2026-05-31 | 移除数量上限：删除Top 10限制和安全阀，纯质量门控（A/B+avg≥65→recommended）。 |
| v4.63 | 2026-05-31 | 信件汇编全链路修复：source_line验证扩展（年份/章节名/中文描述）、R-section年份引用正则、聚类阈值0.58→0.35、dry-run聚类预览、execute_code分批策略文档。 |
| v4.62 | 2026-05-31 | Pitfall 7：三个脚本粗体格式正则bug修复（pipeline 9/62→62/62）、信件合集年份引用格式陷阱、新增 bold-format-regex-pitfall.md。 |
| v4.60 | 2026-06-01 | 审计修复：§4.1 模糊阈值→明确引用§6、§8孤立节合并到§4、§10 Pitfall 6外移到references、description+4触发词、章节编号重排消除断层。 |
| v4.59 | 2026-05-31 | skill-creator 9 维审计：阈值注释、触发词、行数瘦身 544→479。 |
| v4.58 | 2026-05-31 | 结构性清理：SKILL.md 899→544 行（changelog 移至 references）、删除 CHANGELOG.md/scripts.bak/5个领域脚本、extractors 标注历史参考、overview.md 版本引用改为"当前版本"、旧架构 extractor 引用更新。 |
| v4.57 | 2026-05-31 | 9 维标准化审计修复 P0×2+P1×4+P2×2：luhmann_connections 写入路径、已读书籍路径、脚本阈值注释、description 触发词优化、5 个过时文件清理、质量自检标签、§9.1/§9.2 逻辑冲突修复、模板写入时机标注。 |
| v4.56 | 2026-05-31 | 全面审计修复 P0×3+P1×5：validate_summary.py 修复 all_prefixes 未定义+count_chinese_chars 改名+新增 v4.54 节检查；validate_candidates.py 修复 connections ALIASES 冲突；pipeline_phase2.py 路径改为 __file__；cluster_candidates.py 接入 detect_granularity；overview.md 版本对齐；connections→luhmann_connections 语义统一。 |


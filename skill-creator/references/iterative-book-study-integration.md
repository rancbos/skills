# Iterative Book-Study-then-Integrate Workflow

When enriching a skill with knowledge from reference books/documents, use this systematic multi-round workflow. Each round produces a prioritized proposal, then executes all items in parallel.

## When to Use

- User asks to "研究这本书" (study this book) to supplement an existing skill
- Skill needs domain knowledge enrichment from external reference materials
- Reference materials are large (5000+ lines) and cannot be fully integrated in one pass

## Workflow (per round)

### Phase 1: Coverage Audit + Research

1. **Read the current skill** — load SKILL.md + all references/ to know what's already covered
2. **Coverage density audit** — before extracting, compute per-book coverage:
   ```bash
   # Count concepts per author in investment-theory.md
   for author in "张磊" "段永平" "格雷厄姆" "林奇" "费雪"; do
     count=$(grep -c "$author" references/investment-theory.md)
     lines=$(wc -l < "books/${author}*.txt" 2>/dev/null || echo 0)
     density=$(echo "scale=2; $count * 1000 / $lines" | bc)
     echo "$author: $count concepts, $lines lines, density=$density/千行"
   done
   ```
   Density < 0.5/千行 = under-extracted, prioritize for deep dive. Density = 0 = completely uncovered, top priority.
3. **Systematic book search** — use `search_files` with keywords (判断、标准、信号、陷阱、风险、案例、估值、行业、异常、操纵) to find uncovered concepts
4. **Deep reading** — for each hit, read surrounding context (±100 lines) to understand the full concept
5. **Deduplicate** — cross-check against existing content; skip anything already covered
6. **Output** — structured list of N new concepts, each with: name, source chapter, core logic, formula, judgment criteria, relationship to existing content, suggested embedding location

### Phase 2: Proposal

Present to user:
- **Prioritized tiers** (🔴 high / 🟡 medium / ⚪ low) based on analytical value
- **Estimated scope** (SKILL.md +X lines, references +Y lines, template +Z lines)
- **Execution plan** (parallel delegation strategy)

Wait for user confirmation. Common patterns:
- "先给方案" → present proposal only
- "全量执行" → execute all items
- "分批次" → execute tier by tier

### Phase 3: Execution (parallel)

Use `delegate_task` with **up to 3 parallel leaf subagents** (hard limit: `delegation.max_concurrent_children` defaults to 3, configurable in config.yaml). For 4+ book batches, split into sequential delegate_task calls of 3 each. Example: 5 books → batch 1 (3 subagents) + batch 2 (2 subagents).

**Temp file naming convention**: Each parallel subagent writes to a unique temp file (NOT in the main references/ directory to avoid accidental inclusion in skill exports). After all subagents complete, merge sequentially into the main reference file, then delete all temp files. Two approaches:

- **Preferred (isolated)**: Write to `/tmp/route-a.md`, then merge:
  ```
  cat /tmp/route-*.md >> references/investment-theory.md (with section headers)
  rm -f /tmp/route-*.md
  ```
- **Direct (when subagent needs to verify output)**: Write to `references/path-a-topic.md`, then append to main file, then delete. Use when the subagent needs to read back its own output for verification. Clean up immediately after merge.

**Alternative (legacy)**: Writing to `references/_new-{topic}.md` also works but clutters the skill directory and risks accidental inclusion in skill exports.

**Subagent 1: SKILL.md modifications**
- Read current file to confirm insertion points
- Apply N patches sequentially (top to bottom to avoid line drift)
- Each patch: unique `old_string` + `new_string` at the correct location

**Subagent 2: references/ additions**
- Read file end to confirm last section
- Append all new chapters in a single large patch at the end

**After both complete** (sequential):
1. Update template (if applicable) — add new indicators/checks
2. Bump version in SKILL.md frontmatter + title + changelog + template
3. Verify consistency — `search_files` with a regex covering all new concept names across all three files

### Phase 4: Verification

```
search_files(output_mode="count", pattern="<regex covering all N new concepts>")
```

Confirm all N concepts appear in all 3 files (SKILL.md, references, template). Then check line counts:
```
wc -l SKILL.md references/*.md templates/*.md
```

## Multi-Round Study (Angle Rotation)

When the user says "继续研究" on the same source material, the first round's keyword-based search is exhausted. **Change the analysis angle entirely** each round.

### Three-Round+ Pattern (validated on Buffett+Munger 7 books, 196K lines → 5 rounds, 55 concepts)

| Round | Search Strategy | What to Extract | Typical Yield |
|-------|----------------|-----------------|---------------|
| 1st | Concept keywords (公式、标准、框架、风险) | Named concepts, formulas, frameworks | 15-20 concepts |
| 2nd | **5-dimension rotation** (below) | Cases, numbers, disciplines, lessons, counterintuitive | 10-15 concepts |
| 3rd | **Domain-specific deep dive** (below) | Industry logic, valuation details, timing, allocation, macro | 8-12 concepts |
| 4th | **Case-study extraction** (below) | Deep insights from long narratives, composite metaphors, author-specific analogies | 8-10 concepts |
| 5th+ | **Gap analysis against existing coverage** (below) | "Assumed covered" concepts, superficially-mentioned terms needing expansion | 5-10 concepts |

**Coverage trajectory** (实测数据 from Buffett+Munger): Round 1 → ~70%, Round 2 → ~90%, Round 3 → ~95%, Round 4 → ~97%, Round 5 → ~99%. After Round 5, marginal returns drop sharply — recommend stopping.

### Second-Round 5-Dimension Search

1. **具体案例** (specific company analysis): How the author analyzed specific companies (e.g., Buffett on Coca-Cola, Munger on Daily Journal)
2. **具体数字标准** (numeric thresholds): ROE benchmarks, debt ratios, margin requirements with actual numbers
3. **投资纪律/禁忌** (investment disciplines): What the author explicitly says "I don't do X"
4. **错误教训** (mistakes/lessons): Author-acknowledged failures and what they learned
5. **反直觉观点** (counterintuitive insights): Views that contradict mainstream investing wisdom

### Third-Round Domain Deep Dive

When Round 2 exhausts the 5-dimension search, shift to **domain-specific** analysis:

1. **行业分析逻辑** (industry analysis): How the author analyzes specific industries (insurance, banking, consumer, tech)
2. **估值细节** (valuation specifics): DCF parameter choices, PE/PB usage details, margin of safety calculations
3. **买入/卖出时机** (timing): When to buy (crisis, undervaluation signals), when to sell (fundamental change, better opportunity)
4. **资产配置原则** (allocation): Cash reserves, stock/bond ratios, concentration rules
5. **宏观观点** (macro): How the author views inflation, interest rates, economic cycles

### Fourth-Round Case-Study Extraction

When Round 3 exhausts domain-specific searches, shift to **extracting insights from long narratives**:

1. **完整公司分析案例** (full company case studies): Author's detailed analysis of specific companies — look for passages >2000 words analyzing one company
2. **组合比喻/类比** (composite metaphors): Author's unique analogies that combine multiple concepts (e.g., "经济城堡+护城河+骑士")
3. **历史叙事中的投资原则** (investment principles embedded in historical narratives): Lessons from market history, bubble analysis, crisis retrospectives
4. **对话/问答中的隐藏观点** (insights from Q&A): Shareholder meeting Q&A often contains insights not in formal letters

**Search technique**: Instead of keyword search, look for **named entities** (company names, person names) followed by long analysis passages. The insight is in the narrative, not in a keyword.

### Fifth-Round+ Gap Analysis

When all source-material search strategies are exhausted, switch to **coverage gap analysis**:

```
Step 1: Extract all concept terms from the skill
  grep -oP '[\\u4e00-\\u9fff]{4,15}' SKILL.md | sort -u > skill_terms.txt

Step 2: For each term, check source material depth
  for term in $(cat skill_terms.txt); do
    source_count=$(grep -c "$term" books/*.txt | awk -F: '{s+=$NF}END{print s}')
    skill_count=$(grep -c "$term" SKILL.md)
    if [ "$source_count" -gt 50 ] && [ "$skill_count" -lt 3 ]; then
      echo "GAP: $term (source=$source_count, skill=$skill_count)"
    fi
  done

Step 3: For identified gaps, read ±200 lines in source to assess depth
Step 4: Prioritize based on analytical value, not frequency
```

This catches "common knowledge" concepts that appear 50+ times in source material but only get a 1-line mention in the skill — they deserve expanded treatment.

### Multi-Author Cross-Check

When studying books by multiple authors (e.g., Buffett + Munger):
- Scan each author's books independently in parallel
- After both complete, cross-check: which concepts overlap? which are unique?
- Prioritize unique contributions from each author over overlapping ones

### Output Format

- Round 1: Group by priority tier (🔴高/🟡中/⚪低)
- Round 2: Group by type (案例/标准/纪律/教训/反直觉)
- Round 3: Group by domain (行业/估值/时机/配置/宏观)

### Round 4+: "Assumed Covered" Detection

After 3 rounds of keyword-based search, the obvious concepts are exhausted. Rounds 4+ require a fundamentally different strategy: **gap analysis against existing coverage** rather than searching the source material.

**Why Round 3 isn't always the end**: The three-round stopping rule assumes coverage > 95% means exhaustion. In practice, some high-value concepts slip through because:
1. **"Common knowledge" blind spot**: Concepts appearing 50+ times in source material (e.g., "市场先生" 62次) get assumed as already covered, but the skill may only have a 1-line mention
2. **Implicit case-study concepts**: Deep analysis embedded in a 10,000+ word company case study (e.g., Singleton's capital allocation) — the individual keywords are generic, but the combined insight is unique
3. **Composite metaphors**: Author uses A+B+C together as one concept (e.g., "经济城堡+护城河+骑士"), but each word separately appears in the skill from different contexts

**Round 4+ Workflow (grep-based gap analysis)**:

```
Step 1: Build concept candidate list from source material
  grep -c "<phrase>" books/*.txt  →  filter to frequency > 5

Step 2: Cross-check against existing skill coverage
  grep -c "<phrase>" SKILL.md references/*.md  →  identify zero/near-zero hits

Step 3: Filter to genuinely uncovered (not just superficially mentioned)
  For each zero-hit concept, read ±50 lines in source to confirm depth
  Check if a RELATED concept already covers the same ground

Step 4: Categorize by gap type
  Type A: "高频但未展开" — mentioned in skill but no detailed treatment
  Type B: "案例内嵌" — buried inside a long case study narrative
  Type C: "组合概念" — individual words covered but author's specific combination not captured
```

**Detection signals** (any one warrants another round):
- Grep finds concepts with 10+ occurrences in source but 0 in SKILL.md
- Source material contains full case studies (>5000 words) with no skill coverage
- Author's unique metaphor/analogy not captured (e.g., "经济城堡" appears 1x in skill vs 4+ detailed passages in source)

**Stopping Rule (revised)**: After each round, compute coverage AND check gap-type distribution. Stop when:
- Coverage > 95% AND most new findings are 🟡中/⚪低 priority, OR
- Round 4+ yields < 5 concepts (true exhaustion), OR
- Gap analysis reveals mostly Type A (superficial mentions that can be expanded inline, no new concepts)

Don't force additional rounds when diminishing returns are clear. But also don't stop prematurely at Round 3 if gap analysis reveals substantial uncovered depth.

## Key Pitfalls

1. **Line drift in sequential patches**: Always patch top-to-bottom. If a patch fails because the `old_string` was shifted by a prior patch, re-read the file and adjust.

2. **Parallel SKILL.md + references works**: The two files are independent — parallel subagents won't conflict. But template + version updates must be sequential (after both complete).

3. **Changelog deduplication**: When adding a new round's changelog entry, keep all prior rounds' entries. Each entry should list the key concepts added, not just "updated".

4. **Concept naming consistency**: Use the same Chinese term across all three files. If the book uses "营运资本管理四维度分析法", use that exact term everywhere.

5. **Research diminishing returns**: After 3-4 rounds on the same source material, new findings become increasingly niche. Alert the user when concepts become "一般优先级" dominated — the source may be exhausted.

6. **Second-round repetition risk**: If the second round finds the same concepts as the first, the search strategy didn't change. Verify at least 80% of second-round findings are genuinely new before presenting the proposal.

7. **Completion verification after interruption**: If execution is interrupted (loop, timeout, session end), ALWAYS verify what was actually written before proceeding. Grep for each planned concept name in the target files. Do NOT assume "planned = completed". A common failure mode: the agent plans N concepts, enters a verification loop, but the actual file writes never happened. The fix is simple: `grep -c "<concept>" SKILL.md` for every concept — zero hits means it wasn't written.

8. **Source-to-skill gap analysis is bidirectional**: Don't just search the source for concepts to add. Also search the skill for concepts that MIGHT be in the source but aren't. Pattern: `grep -oP '[\\u4e00-\\u9fff]{4,15}' SKILL.md | sort -u` to extract all Chinese terms from the skill, then grep each against the source material to find terms that appear in the skill but could be enriched from the source.

9. **Orphaned temp files after merge**: After merging temp files into `references/investment-theory.md`, ALWAYS delete them. Check with `ls /tmp/route-*.md`. Common failure: subagent creates temp files, merge happens, but cleanup is forgotten — leaves orphaned files that confuse future sessions. Add explicit cleanup step to the merge workflow.

15. **Python dict key collision in scoring scripts**: When a Python script stores both numeric scores and string notes in the same dict (e.g., `result["scores"]["1.1_商业模式"] = 15` and `result["scores"]["1.1_商业模式_note"] = "⚠️待确认"`), calling `sum(result["scores"].values())` will crash with `TypeError` because it tries to add strings. **Fix**: always separate into two dicts — `result["scores"]` (numeric only) and `result["notes"]` (strings only). The `sum()` call only operates on the scores dict.

16. **`patch` escape-drift with backslash-quote content**: The `patch` tool fails with "Escape-drift detected" when `old_string` contains `\"` (backslash-quote) that doesn't match the actual file content. This happens when the patch tool auto-escapes quotes in the JSON parameter but the file contains unescaped quotes. **Workaround**: use `read_file` + string replacement in `execute_code` instead of `patch` for files containing Chinese quotation marks or mixed quote styles. If using `patch`, avoid `old_string` values that contain `\"` — restructure the match to use surrounding context instead.

17. **Score range zombie zones**: After multiple rounds of auditing a scoring system, check whether any score ranges in the conclusion matrix are practically unreachable. Pattern: if Step 0-2 exclude companies below threshold X, and the conclusion matrix has a range "<X", that range is a "zombie zone" — mathematically possible but never triggered. Fix: merge zombie ranges with adjacent ranges to create a simpler, more practical matrix.

10. **`patch` tool parameter is `path` not `file_path`**: The `patch` tool uses `path` as its required parameter name, NOT `file_path`. Using `file_path` causes a silent "path required" error. This is a common mistake when switching between `skill_manage(file_path=...)` (which uses `file_path`) and `patch(path=...)`. Always double-check:
    - `patch(mode='replace', path='...', old_string='...', new_string='...')` ✓
    - `patch(mode='replace', file_path='...', ...)` ✗ → "path required" error
    
    After 2 consecutive "path required" errors, stop and verify the parameter name before retrying.

11. **Subagent timeout with large book sets**: 11+ books × deep reading = guaranteed timeout at 600s even with parallel subagents. Solution: split into 3-5 parallel batches of 2-4 books each. Each subagent should read first 2000 lines + last 500 lines of each book (not full text) for initial concept identification, then deep-read only the relevant chapters. If a single book is >10,000 lines (e.g., 段永平 20,940行), give it its own dedicated subagent.

12. **SKILL.md line budget enforcement**: After each integration round, `wc -l SKILL.md`. Target is ≤950 lines for investment analysis skills. If over target, move newly-added detailed explanations to references/ and replace with 1-line summaries. Common mistake: adding 3-4 paragraph concept explanations directly into SKILL.md instead of references/.

13. **Three-way version consistency**: When bumping versions, update ALL THREE locations in a single batch:
    - `SKILL.md` frontmatter `version:` field
    - `SKILL.md` title line (`# ... vX.Y.Z`)
    - `templates/company-analysis-report.md` version line at bottom
    - `references/version-history.md` changelog entry
    
    Common failure: updating SKILL.md but forgetting the template, leaving template at old version. Always verify with:
    ```bash
    grep 'version:' SKILL.md | head -1
    grep 'v3\.' SKILL.md | head -1  
    grep '版本' templates/*.md | tail -1
    ```

14. **Template sync when adding new concepts**: New concepts added to SKILL.md may require template updates:
    - **Scoring range changes** (e.g., Step 3 sub-items all /25分) → update template's `### X.X ... [X]/Y分` headers
    - **Checklist additions** (e.g., 12-item 终检清单) → ensure template has ALL items, not a subset
    - **New validation questions** (e.g., 7-question 反验证) → add to template's corresponding section
    - **New risk warnings** (e.g., 逆向检查<-20) → add to template's 风险警示 section
    - Always diff SKILL.md vs template for the same section after adding concepts.

15. **One-line reference format for SKILL.md**: When adding concepts from books to SKILL.md, use this exact format (keeps line count low):
    ```
    **概念名**（作者）：一句话定义。详见 `references/investment-theory.md` §N。
    ```
    NOT multi-paragraph explanations. The detailed content goes in references/investment-theory.md only.

18. **SKILL.md reference compression when over line limit**: When SKILL.md exceeds its soft limit (e.g., 1000 lines) and new references must be added, **compress existing verbose references while adding new ones** to maintain net-zero line growth. This is different from Step Compression (moving content to references/) — it's about merging multiple single-line §-references into fewer grouped lines.

    **Pattern**: Identify clusters of related references that each have their own line, then merge them into single lines with combined §-references:
    ```
    # BEFORE (4 lines, 4 separate references):
    **反脆弱投资组合构建法**（塔勒布）：85-90%国债/现金/黄金...。详见 `references/investment-theory.md` §199。
    **尾部风险对冲策略**（塔勒布）：4种方法...。详见 `references/investment-theory.md` §200。
    **"足够"概念**（豪泽尔）：幸福=拥有-期待...。详见 `references/investment-theory.md` §209。
    **合理性优先于理性**（豪泽尔）：能长期坚持...。详见 `references/investment-theory.md` §210。

    # AFTER (2 lines, same 4 concepts + 2 new):
    **反脆弱杠铃+组合构建+尾部对冲**（塔勒布）：85-90%极安全+10-15%极投机→凸性组合+A股适配。详见 `references/investment-theory.md` §162, §199-§200, §267-§268。
    **行为金融四概念**（豪泽尔）："足够"风险边界/合理性优先/尾部事件主导/悲观偏见。详见 `references/investment-theory.md` §209-§212。
    ```

    **When to use**:
    - SKILL.md > soft limit AND new references must be added
    - Multiple existing references cover the same author/topic with separate lines
    - The individual references are one-line summaries (not detailed explanations)

    **Compression strategies**:
    - **Author grouping**: Merge references from same author into one line with §-ranges (e.g., `§209-§212`)
    - **Topic grouping**: Merge references on same topic from different §-sections (e.g., `§163, §186-§187`)
    - **Concept enumeration**: List individual concept names separated by `/` in the merged line

    **Verification**: After compression, run `wc -l SKILL.md` to confirm net change is near zero. Also `grep -c '§[0-9]' SKILL.md` to confirm all §-references are still present.

    **Real-world example** (jw-company-analysis v3.27.0): Compressed 13 lines of existing references while adding 16 new ones, net change +4 lines. Compression matrix:
    | Location | Before | After | Saved |
    |----------|--------|-------|-------|
    | Step 0.3 灰犀牛 | 3 lines | 1 line | -2 |
    | Step 5 塔勒布 | 4 lines | 1 line | -3 |
    | Step 5 豪泽尔 | 4 lines | 1 line | -3 |
    | Step 5 特维德 | 6 lines | 1 line | -5 |
    | **Total saved** | | | **-13** |
    | New references added | | | +16 |
    | **Net** | | | **+4** |

## Example: Six-Round Integration (jw-company-analysis + Zhang Xinmin books)

| Round | Concepts | Version | Focus |
|-------|----------|---------|-------|
| 1 | 6 | v2.4.0 | Base frameworks |
| 2 | 6 | v2.5.0 | Quantitative tools |
| 3 | 24 | v2.6.0 | Full coverage |
| 4 | 22 | v2.7.0 | Deep methodology + paradigm shifts |
| 5 | 22 | v2.8.0 | DuPont limitations + valuation + explosion zones |
| 6 | 20 | v2.9.0 | Working capital + group management + impairment mechanics |

Total: 100 concepts, ~3800 lines added across 6 rounds.

### Phase 5: Post-Expansion Audit (mandatory after all rounds)

After completing ALL rounds of integration, run this audit before delivering to user:

1. **Duplicate version entries**: `grep "vX.Y.Z" SKILL.md` — if a version appears twice, delete the duplicate
2. **Formula vs table consistency**: Compare weight/scoring tables with any inline formula text — they must match exactly
3. **Template/flow structure sync**: Compare the "output structure" section in SKILL.md with the actual template file's section order — they must match
4. **SKILL.md bloat check**: `wc -l SKILL.md` — if >800 lines, move detailed concept explanations to references/ (keep only 1-line summaries + links in SKILL.md)
5. **Overlapping frameworks**: Grep for similar framework names — if two frameworks cover the same ground, merge them
6. **Three-way version consistency**: Verify version matches in SKILL.md frontmatter, SKILL.md title, and template footer:
   ```bash
   grep 'version:' SKILL.md | head -1
   grep '# .*v[0-9]' SKILL.md | head -1
   grep '版本' templates/*.md | tail -1
   ```
   All three must show the same version number.
7. **Template scoring range sync**: For each Step's sub-items, verify template `### X.X ... [X]/Y分` matches SKILL.md's `### X.X ... (0-Y分)` ranges. Common drift: template has `/30分` while SKILL.md says `0-25分`.
8. **Checklist completeness**: If SKILL.md has an N-item checklist, verify the template has exactly N items (not N-1 or N-2). Common failure: template gets a subset during slimming.

**Why this matters**: Each round of parallel subagent edits can introduce inconsistencies (duplicate entries, formula drift, template misalignment). The verification in Phase 4 only checks "did all concepts land in all files" — it doesn't check structural integrity. This audit catches the structural issues that accumulate across rounds.

## Template for Proposal

```markdown
## 张新民财报分析法 第N轮补充方案

研究发现 **X项未覆盖概念**。

### 🔴 高优先级（Y项）
| # | 概念 | 核心逻辑 | 建议位置 |
|---|------|---------|---------|
| 1 | ... | ... | Step X.X |

### 🟡 中优先级（Z项）
...

### ⚪ 一般优先级（W项）
...

**要全量执行（X项一次到位），还是分批次来？**
```

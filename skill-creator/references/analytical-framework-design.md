# Analytical Framework Skill Design Patterns

Lessons from building jw-maoism (毛泽东思想智慧长者) — an analytical framework skill with 8 core models, 6 auxiliary models, a 7-step analysis flow, and supporting reference files. Iterated through 6 versions.

## Architecture Patterns

### 1. Hierarchical Model Structure (Not Flat)

**Anti-pattern**: Listing 10-14 models as equal peers. Users can't hold that many in working memory, and the model doesn't know which to reach for first.

**Pattern**: Organize into 5-6 "big methods" (思维大法), each with 2-3 sub-tools. Example:

```
矛盾分析法 (big method)
  ├── 穿透表象 (sub-tool)
  ├── 利益结构分析 (sub-tool)
  └── 异化思维 (sub-tool)
```

This reduces cognitive load and creates natural "reach for this first, then drill down" behavior.

### 2. Explicit Model-to-Flow Mapping

**Anti-pattern**: Having a model library AND a step-by-step flow as two independent structures. The model picks models by instinct, often missing the right one.

**Pattern**: Each flow step explicitly states which models to invoke:

```
第二步：矛盾重构与分析
  调用模型：矛盾分析法、统一战线（分清各方利益）、穿透表象
```

This forces systematic model usage rather than ad-hoc selection.

### 3. Auxiliary Models Need Full Structure

**Anti-pattern**: Auxiliary models get 2-3 lines while core models get 15-20 lines. The model treats them as afterthoughts and never uses them.

**Pattern**: Every model (core or auxiliary) gets the same structural treatment:
- Quote + source
- Core operations (numbered list)
- Enhancement from other thinkers
- Limitations (always include — teaches intellectual humility)

### 4. Domain-Specific "Judgment" Dimension

**Anti-pattern**: Only teaching analysis methods (how to decompose) without teaching judgment (how to decide under uncertainty).

**Pattern**: Include explicit judgment principles specific to the domain:
- "抓住不变的东西比追逐变化更重要"
- "大势比细节重要"
- "看一个人的行动比听他的话更重要"
- "在信息不完整时如何做出判断" (not just "ask for more info")

### 5. "Timing Sense" in Action Plans

**Anti-pattern**: Action plans say "what to do" but not "when to act" or "when to stop."

**Pattern**: Add timing indicators:
- When to accelerate
- When to wait
- When to retreat
- Observable signals that indicate timing shifts

### 6. Contradiction Reframing (Stated vs Actual Problem)

**High-value pattern**: Users often state a symptom as the problem, not the root cause. Include a "reframing framework" that teaches the model to question the user's premise.

**Implementation**: Not a fixed lookup table (doesn't generalize), but a method:
1. Ask "what does the user think the problem is?"
2. Ask "what would the problem look like from the root cause's perspective?"
3. If they differ, reframe before analyzing

### 7. Problem Type → Model Selection

**Caution**: Mapping tables ("decision-type → use model X") are useful starting points but become rigid. Real problems are often mixed types.

**Pattern**: Make the mapping a "suggestion" not a "rule." The model should first understand the problem's essence, then select models — not classify first, then apply.

### 8. Anti-Patterns Section

**High-value addition**: List 5-8 common analysis mistakes specific to the framework:
- "把所有问题都往框架里套" (forcing all problems into the framework)
- "引用原文太多变成语录堆砌" (quote-heavy, analysis-light)
- "建议太宏观没有具体动作" (vague advice)
- "过度使用角色口吻变成说教" (persona overdone)

### 9. Self-Check Scaling by Complexity

**Anti-pattern**: 12-item self-check list applied to every analysis. Overkill for simple problems, wastes tokens.

**Pattern**: Scale self-checks by complexity:
- Simple: 3 core checks (main contradiction? actionable advice? not platitude?)
- Medium: 5 checks
- Complex: 7-8 checks

### 10. Reference Files Need Usage Guidance

**Anti-pattern**: Listing reference files without saying when to read them. The model either reads all of them (wasteful) or none of them (ignores depth).

**Pattern**: Each reference file gets an explicit trigger condition:
- "分析涉及经济/投资问题时，读 capital-tools.md"
- "分析涉及邓小平思想时，读 deng-models.md"

## Pattern: Book-Based Knowledge Stratification

When building an analytical framework skill from a library of books (e.g., 20+ investment/philosophy books), don't treat all books equally. Stratify into three tiers and extract at different depths:

| Tier | Criteria | Extraction Depth | Example |
|------|----------|-----------------|---------|
| ⭐⭐⭐ Full framework | Books that define the skill's core methodology | Extract complete frameworks, checklists, decision trees, scoring rubrics | 巴菲特致股东的信 → 选股四原则+所有者收益公式 |
| ⭐⭐ Key principles | Books that supplement the core with specific techniques | Extract 3-5 key principles per book, map to specific analysis steps | 彼得林奇 → 六类公司分类+PEG估值 |
| ⭐ Supplementary | Books that provide context, examples, or adjacent perspectives | Extract 1-2 signature ideas per book, use as references/cross-checks | 周金涛 → 康波周期定位信号 |

**Implementation**:
1. List all books with their primary contribution dimension (e.g., "valuation", "management quality", "cycle awareness")
2. Map each book to specific analysis steps in the framework
3. For ⭐⭐⭐ books, create dedicated `references/<book-name>.md` files with full extracted frameworks
4. For ⭐⭐ books, embed key principles inline in the relevant SKILL.md steps
5. For ⭐ books, list in a `references/investor-wisdom-cards.md` speed-reference file

**Anti-pattern**: Extracting every book at the same depth. This bloats SKILL.md to 5000+ lines and dilutes the core framework. The skill's identity should come from 2-3 ⭐⭐⭐ books, not from averaging 20 books.

## Pattern: Cross-Skill Resource Sharing

When creating a complementary skill (e.g., `jw-company-analysis` alongside `jw-stock-value-analyzer`), explicitly design which resources are shared vs unique:

| Resource Type | Share When | Keep Separate When |
|--------------|-----------|-------------------|
| Data fetching scripts | Same data sources needed | Different markets/sources |
| Quality/red-flag checks | Same validation rules | Different risk models |
| Decision logs | Same user tracking both analyses | Different decision types |
| Data verification protocols | Same data quality standards | — (almost always share) |
| Analysis frameworks | — (never share — that's the differentiator) | Different methodology |

**Implementation**: In the new skill's SKILL.md, add a "Shared Resources" section listing exact paths to borrowed files. This prevents duplicate maintenance and ensures consistency.

**Naming convention**: Complementary skills should use parallel naming (e.g., `jw-stock-value-analyzer` + `jw-company-analysis`) so the user can see they belong to the same family.

## Pattern: Weighted Module Structure

For multi-dimensional analysis frameworks, assign explicit percentage weights to each module. This serves two purposes:
1. Guides the model on where to spend analysis effort
2. Produces a transparent composite score

```
综合得分 = 企业质量×35% + 财务健康×20% + 产业链×10% + 估值×25% + 逆向调整×10%
```

**Rules**:
- Weights should sum to 100%
- No single module should exceed 40% (over-dominance)
- "Adjustment" modules (contrarian, pricing power) can be additive ±% rather than weighted
- Include a "one-vote veto" list separate from the weighted score — certain red flags override any composite score

**Anti-pattern**: Equal weights across all modules. This implies all dimensions matter equally, which is rarely true and removes the framework's perspective.

## Pattern: Data Source Layering by Market

When the analysis framework covers multiple markets (A-share, HK, US), design explicit data source chains per market:

```
A股: jw-investment-data/fetch_market_data.py (主) → web search (备)
港股: fetch_stock_data.py/yfinance (主) → AkShare (备) → web search (兜底)
美股: fetch_stock_data.py/yfinance (主) → web search (备)
宏观: jw-investment-data/fetch_macro.py (主) → jin10 MCP (备)
```

**Key principle**: Never use the same script for all markets blindly. Each market has quirks (A-share uses AkShare, HK uses yfinance, index codes ≠ stock codes). Document the chain explicitly in SKILL.md Step 1.

## Reference File Organization

For analytical framework skills, organize references by thinker/source:
- `references/thinker-a-models.md` — thinker A's core models
- `references/thinker-b-models.md` — thinker B's core models
- `references/domain-tools.md` — domain-specific analytical tools
- `references/life-wisdom.md` — quotes and wisdom for persona warmth
- `references/anti-patterns.md` — common mistakes and how to avoid them

## Token Budget Guidance

- SKILL.md main body: 400-550 lines (beyond this, models stop reading carefully). 522 lines tested OK for a mature skill with 5 big methods + flow + anti-patterns.
- Each reference file: 150-400 lines
- Total reference budget: 6-10 files, ~2000-4000 lines total
- Models below 200 lines feel thin; above 600 lines get truncated in practice

## Pattern: Comprehensive Audit After Stable Version

When a skill reaches a stable version (e.g., after v5-v6 iterations), run a full audit before declaring done. Look for:

1. **Orphaned references**: Files in `references/` not listed in SKILL.md's reference table → model never reads them
2. **Misplaced files**: Development artifacts (changelogs, logs) in `references/` → wasteful token loading
3. **Stale evals**: Test cases from earlier versions that don't cover new features → false confidence
4. **Naming inconsistencies**: Section names changed in SKILL.md but not in reference files (e.g., "附加维度" vs "应用维度")
5. **Count mismatches**: Changelog says "3→5→10" but actual is "3→6→9" → documentation rot
6. **Content overlap**: Two files covering the same topic with slightly different content → merge or deduplicate

Fix all issues in one batch, not incrementally. This is the "comprehensive audit" pattern — diagnose everything first, then fix.

### Content-Level Optimization (Beyond File-Level)

The 6 items above are file-level issues. Deeper optimization requires content-level analysis:

7. **Duplicate sections**: Same checklist/table appearing in multiple places within SKILL.md (e.g., quality checklist in Step 5 AND at end of file). Detection: search for repeated list items or table rows.
8. **Invalid references**: SKILL.md references files that don't exist (e.g., `references/schema.json` listed but never created). Detection: `grep` for all `references/*.md` and `scripts/*.py` paths, verify each exists.
9. **Cross-file consistency**: Lists in SKILL.md diverge from those in scripts/ (e.g., forbidden words list in SKILL.md has 15 items, quality_check.py has 16). Detection: compare key lists between SKILL.md and validation scripts.
10. **Scattered guidance**: Same guidance (word counts, comparison dimensions) spread across 3+ sections instead of consolidated into one reference table. Detection: search for repeated numeric ranges or repeated "原则" statements.
11. **Vague standards**: Criteria like "信息不够就补搜" without quantifiable thresholds. Detection: look for "足够"/"不够" without numbers, "适当"/"合理" without ranges.
12. **Tool usability**: Scripts with awkward interfaces (requiring JSON on command line instead of from file). Detection: review scripts/ for `--data '{...}'` patterns.
13. **Verbose delivery paths**: Decision trees that could be compressed to tables. Detection: look for `├─`/`└─` code blocks or 3+ "方案X" subsections.

**Execution pattern**: When user says "全量优化", fix ALL issues (1-13) in one batch. Order: delete duplicates first (reduces file size), then remove invalid references, then unify cross-file consistency, then consolidate scattered guidance, then add quantifiable thresholds, then improve scripts, then compress verbose flows.

## Pattern: Scoring System Design for Multi-Dimensional Frameworks

When building a weighted scoring system (e.g., 5 dimensions each 100 points, weighted to a composite score), watch for these design pitfalls:

### Pitfall 1: Safety Valve Overflow

If one sub-item has a much larger score range than others (e.g., -50 for psychology checks vs -10 for risk categories), it dominates the safety valve mechanism, making other dimensions' scores meaningless.

**Fix**: Separate subjective checks (investor psychology) from objective risk dimensions. Subjective checks get their own "pause and reflect" mechanism rather than participating in the safety valve score.

### Pitfall 2: Threshold Calibration

Exclusion/downgrade thresholds should be set at the "poor" level, not "average." Setting a moat threshold at 10/25 means only "wide + stable" passes — too strict for most industries where "medium + stable" is normal.

**Rule of thumb**: Threshold for downgrade should be at the 20th percentile of expected scores, not the 50th.

### Pitfall 3: Sub-Dimension Weight Drift

When Step A uses 40/30/30 distribution and Step B uses 25/25/25/25, the implicit weight of each sub-dimension differs. If this is intentional, document the design rationale. If unintentional, unify.

### Pitfall 4: Uneven Score Bands

Score bands like 28-35/21-27/11-20/0-10 (widths 7/6/10/11) are hard to calibrate. Use uniform bands: 25-30/18-24/10-17/0-9 (widths 6/7/8/9) or similar.

### Pitfall 5: Subject/Object Confusion

"Risk analysis" that includes both company risks (objective) and investor psychology (subjective) confuses the model. Separate into distinct modules with clear labels about what participates in scoring.

## Pattern: Industry Calibration for Multi-Sector Frameworks

When an analytical framework covers multiple industries, add calibration coefficients at key steps:

| Industry | Calibration Approach | Key Adjustments |
|----------|---------------------|-----------------|
| State-Owned Enterprises | Bonus points for management stability; shift from "strategic autonomy" to "policy execution" | Management +10pt, governance add "policy stability" dimension |
| Financial | Replace DCF with PB/DDM; replace cash flow metrics with provision coverage / capital adequacy | Valuation method swap, financial metric substitution |
| Cyclical | Replace linear CAGR with "cycle average + current position"; add "cycle position" as key variable | Growth logic rewrite, add cycle-aware scoring |
| Technology | Relax ROE threshold to >8% (high R&D); widen moat assessment window to 5 years | Threshold relaxation, time horizon extension |

**Implementation pattern**: Add `> **XX行业校准**：` blockquotes at the end of relevant steps. Calibration adds bonus points (with cap) to reflect industry-specific realities.

**Anti-pattern**: Applying the same scoring rubric to all industries equally. This systematically disadvantages certain sectors (e.g., SOEs score low on management incentives by design).

For persona-driven skills, include an explicit "do NOT say X, say Y instead" table in the output spec section. This prevents the model from falling into common AI-speak patterns that break the persona.

Example:
```markdown
| 禁用 | 替代 |
|------|------|
| "这个问题很复杂，需要多方面考虑" | 直接给出判断 |
| "两种可能都有道理" | 赌一个方向，说清楚为什么 |
| "建议你根据自身情况决定" | 给出具体建议 |
| "作为AI，我无法……" | 以角色身份直接回答 |
```

Place this near the end of SKILL.md, in the output spec section — not at the top where it wastes prime context.

## Pattern: Reference Table Completeness

Every file in `references/` should have a row in SKILL.md's reference table with a trigger condition. If a file exists but isn't listed, the model won't know to read it. If a file is listed without a trigger condition, the model won't know when to read it.

Audit check: `ls references/` and compare against the table. Any file missing a row = bug.

## Pattern: Book Content Integration Workflow

When enriching an analytical framework skill with content from books (e.g., adding Zhang Xinmin's financial analysis methods to `jw-company-analysis`), follow this systematic workflow:

### Phase 1: Gap Analysis

1. **List all already-covered concepts** — search SKILL.md + references/ for existing frameworks, formulas, judgment criteria
2. **Search books for uncovered content** — grep for keywords: 比率、指标、公式、计算、判断、标准、信号、风险、质量、战略、框架、分析、方法
3. **Produce a structured gap list** with per-item fields:
   - Concept name
   - Source book + chapter
   - Core logic (1-2 sentences)
   - Calculation formula (if any)
   - Judgment criteria
   - Relationship to existing content (new / supplement / deepen)
   - Suggested embedding location

### Phase 2: Priority Triage

Organize findings into three tiers:

| Tier | Criteria | Example |
|------|----------|---------|
| 🔴 High | Core analytical framework, changes how analysis is done | 四大动力量化分析、综合分析四步法 |
| 🟡 Medium | Important supplement, enhances analysis precision | 毛利率×存货周转组合信号、现金流充分性五步法 |
| ⚪ General | Detail refinement, nice-to-have | 固定资产周转率用原值、应收账款周转率正确计算 |

### Phase 3: Proposal Before Execution

Present the gap list to the user with:
- Number of items per tier
- Estimated line count changes per file
- Recommended execution approach (batch vs incremental)

**User preference (jw)**: When user says "全量执行" or "依次优化", execute ALL items at once — do NOT suggest batching into smaller chunks. The user wants comprehensive, one-shot execution.

### Phase 4: Parallel Execution

Execute modifications across all three files simultaneously:

```
delegate_task_batch([
  {goal: "SKILL.md modifications", toolsets: ["file"]},
  {goal: "references/ new chapters", toolsets: ["file"]}
])
# Then sequentially:
  template_updates()
  version_bump()
  consistency_verification()
```

**Key insight**: SKILL.md and references/ can be modified in parallel (no file conflict). Template updates depend on both being done first (to confirm exact content), so run sequentially after.

### Phase 5: Three-File Consistency Verification

After all modifications, verify consistency:
1. Search all three files for every new concept name
2. Confirm each concept appears in SKILL.md + references/ + template
3. Verify version numbers match across SKILL.md and template
4. Count total lines per file and report changes

### Pattern: Multi-Round Iterative Deepening

When integrating book content into a skill, a single pass rarely covers everything. Plan for 3-5 rounds, each going deeper:

| Round | Focus | Typical Yield |
|-------|-------|---------------|
| 1 | Basic frameworks, core formulas | 5-8 concepts |
| 2 | Quantitative tools, judgment criteria | 5-8 concepts |
| 3 | Full coverage of remaining surface content | 15-25 concepts |
| 4 | Deep methodology, paradigm shifts, "why" behind the "what" | 15-25 concepts |
| 5 | Edge cases, special accounting, governance, valuation nuance | 15-25 concepts |

**Why multiple rounds**: Each round's integration changes the baseline — concepts that seemed irrelevant in round 1 become connectable after round 3 adds context. The agent must re-read the books with the UPDATED coverage list each time.

**Diminishing returns signal**: When a round yields <10 concepts and they're all ⚪ general priority, the book is effectively exhausted for this skill.

**Real-world example**: jw-company-analysis went through 5 rounds of Zhang Xinmin book integration:
- v2.4.0 (round 1): 6 basic concepts
- v2.5.0 (round 2): 6 quantitative tools
- v2.6.0 (round 3): 24 full-coverage concepts
- v2.7.0 (round 4): 22 deep methodology concepts
- v2.8.0 (round 5): 22 edge cases and governance
- Total: 80 concepts across 5 rounds

### Pitfall: read_file Line Number Prefixes

`read_file` returns content with line number prefixes like `     1|content`. Writing this back to a file directly will corrupt it with embedded line numbers. This is especially dangerous when:
- Rebuilding index files from read_file output
- Copying content between files via write_file
- Patching files after reading with offset/limit

**Safe patterns**:
1. Use `patch` tool (strips line numbers automatically)
2. Use `terminal` with `sed`/`cp` for file operations
3. In Python scripts, strip with regex `r'^\s*\d+\|'` before write_file

### Anti-patterns

- **Incremental batching when user wants full execution**: User says "全量" → do everything, don't suggest "let's do high priority first"
- **Missing template sync**: Adding concepts to SKILL.md + references but forgetting to add corresponding template sections → inconsistency
- **Skipping gap analysis**: Adding content that already exists → duplication and confusion
- **Not checking existing coverage**: Adding a concept that's already covered under a different name → redundancy
- **Sequential file modifications**: Modifying SKILL.md and references one after another when they could run in parallel → 2x slower
- **Single-pass book research**: Stopping after one round of book reading when the user expects iterative deepening. Each round should re-read with the UPDATED coverage list to find what's still missing.

### Version Number Convention

After each round of book content integration:
- Patch version (v2.5.0 → v2.6.0) for content additions
- Minor version (v2.x.0 → v3.0.0) for structural changes
- Update changelog with: version, date, summary of changes
- Sync version across SKILL.md title + template footer + changelog table

## Pattern: Framework Fusion (Merging New Framework into Existing Skill)

When a user provides a new analytical framework (e.g., "企业研究框架2") and asks to merge it into an existing skill, follow this 5-phase workflow:

### Phase 1: Backup

Always backup before structural changes:
```bash
cp -r ~/.hermes/skills/<skill-name> ~/.hermes/skills/<skill-name-backup-YYYYMMDD>
```

### Phase 2: Structural Mapping

Create a side-by-side mapping table:

| New Framework Module | Existing Step | Gap |
|---------------------|--------------|-----|
| Module A | Step X | Covered |
| Module B | (none) | **NEW** |
| Module C | Step Y (partial) | **EXPAND** |

Identify three categories:
- **Covered**: New framework maps to existing step → no change needed
- **Expand**: Existing step partially covers → need to merge new content
- **New**: No existing coverage → need to create new step

### Phase 3: Decision Points

For each structural decision (weight allocation, step placement, scoring integration), present options with trade-offs and ask user to confirm BEFORE executing. Key decisions:

1. **Weight distribution**: Sum must = 100%. If it doesn't, present calibration options.
2. **New module placement**: Independent step vs. sub-dimension of existing step?
3. **Scoring integration**: Does the new module participate in weighted scoring or serve as auxiliary (safety valve / timing signal)?
4. **Sub-item structure**: How many sub-items per module? Balance detail vs. token budget.
5. **Cross-references**: How do existing exclusion checks / downgrade triggers map to new structure?

**Anti-pattern**: Executing the fusion before confirming decisions with user → rework.

### Phase 4: Execution

For large files (800+ lines), `execute_code` may be blocked. Fallback pattern:
1. `write_file` for the first chunk (frontmatter + overview + first few steps)
2. `terminal cat >> file << 'EOF'` for subsequent chunks

Each chunk should be self-contained (complete sections, not mid-sentence breaks) to avoid partial-write corruption.

### Phase 5: Consistency Verification

After writing, verify:
1. **Weight sum**: Grep for weight percentages, confirm sum = 100%
2. **Step numbering**: `grep -oP 'Step \d+' | sort -u` — confirm no gaps or duplicates
3. **Cross-references**: Exclusion checks in execution overview match actual step locations
4. **Report template**: Chapter count matches step count
5. **Checkpoint naming**: If the skill uses checkpoint files (step0_data.json, step1_quality.json, etc.), verify checkpoint names match new step numbers. **Pitfall**: Pre-execution scripts often hardcode old step names — these must be updated too.

### Pitfall: Checkpoint Naming Drift After Step Restructure

When renumbering steps (e.g., old Step 1 → new Step 3), checkpoint file names and pre-execution script output names become stale. This causes:
- Agent looking for `step3_quality.json` but script generates `step1_quality.json`
- Checkpoint recovery failing silently (reads wrong file)

**Fix**: After restructure, update:
1. `pre_analysis.py` output file names
2. `checkpoint-schema.md` step references
3. SKILL.md checkpoint mechanism description
4. Any `checkpoint.json` `last_step` values

**Detection**: Grep for `step\d+_` patterns in scripts/ directory after any step renumbering.

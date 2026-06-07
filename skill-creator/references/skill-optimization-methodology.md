# Skill Optimization Methodology

Systematic approach for post-creation skill optimization. Use when user says "全量优化", "深度审计", "研究这个skill有没有优化空间".

## Phase 1: Issue Detection

Scan the skill for these 7 categories of issues:

### 1. Content Duplication
Same content appearing in multiple places. Common patterns:
- Quality checklist appears both inline and at end of file
- "Forbidden zones" repeated in writing style section
- Summary/description duplicated across sections
- **Same §reference in two different Steps** (e.g., §172 in both Step 0.5 and Step 5.2 with slightly different wording)

**Detection**: Search for near-identical paragraphs, repeated lists, same table appearing twice. Also: `grep -o '§[0-9]\+' SKILL.md | sort | uniq -c | sort -rn | head -10` to find §refs used most — then check if the top hits appear in semantically wrong sections.

### 2. Invalid References
SKILL.md references files that don't exist in the skill directory.

**Detection**: `grep -o 'references/[a-z-]*.md' SKILL.md` then verify each file exists. **Also check the reverse**: files that exist in references/ but are never referenced in SKILL.md (orphaned files). `ls references/*.md | xargs -I{} basename {}` vs `grep -o 'references/[a-z-]*.md' SKILL.md | sort -u` — the diff shows orphaned files. Orphaned files from research SOPs or intermediate drafts should be deleted; orphaned reference files with substantive content should either be linked from SKILL.md or merged into investment-theory.md.

### 3. Cross-File Consistency
Lists or definitions in SKILL.md diverge from those in scripts/ or references/.

**Detection**: Compare forbidden word lists, required sections, dimension tables between SKILL.md and quality_check.py (or similar validation scripts).

### 4. Scattered Guidance
Same guidance (e.g., word count ranges, comparison dimensions) spread across multiple sections instead of consolidated.

**Detection**: Search for repeated tables, repeated numeric ranges, repeated "原则" statements.

### 5. Vague Standards
Criteria like "信息不够就补搜" without quantifiable thresholds.

**Detection**: Look for:
- "足够" / "不够" without numbers
- "适当" / "合理" without ranges
- Checklist items without pass/fail criteria

### 6. Tool Usability Issues
Scripts with awkward interfaces (e.g., requiring JSON on command line instead of from file).

**Detection**: Review scripts/ for `--data '{...}'` patterns that should support file input.

### 7. Verbose Delivery Paths
Decision trees or multi-step flows that could be compressed to tables.

**Detection**: Look for code blocks with `├─` / `└─` decision trees, or 3+ "方案X" subsections.

## Phase 2: Prioritization

| Priority | Category | Rationale |
|----------|----------|-----------|
| P0 | Content Duplication | Wastes tokens, confuses execution |
| P0 | Invalid References | Causes tool call failures |
| P1 | Cross-File Consistency | Validation doesn't match instructions |
| P1 | Scattered Guidance | Forces back-and-forth during execution |
| P1 | Vague Standards | Unstable quality across runs |
| P2 | Tool Usability | Friction but not blocking |
| P2 | Verbose Delivery | Token waste but functional |

## Phase 3: Execution

**User preference (jw)**: When user says "全量优化", execute ALL issues in one batch. Do NOT suggest "let's do P0 first".

Execution order (within the batch):
1. Delete duplicate content (reduces file size first)
2. Remove invalid references
3. Unify cross-file consistency (SKILL.md first, then scripts)
4. Consolidate scattered guidance into single reference table
5. Add quantifiable thresholds to vague standards
6. Improve script interfaces
7. Compress verbose flows

## Multi-Round Deep Audit Methodology

For skills >800 lines with 20+ issues, a single-pass audit misses patterns that only become visible from different angles. Use a **4-round perspective-specific approach**:

| Round | Perspective | Focus | Typical Yield |
|-------|------------|-------|---------------|
| 1 | Structural correctness | File references, step numbering, weight consistency, cross-file sync | 10-20 issues |
| 2 | Scoring math + execution efficiency | Formula overflow, subjective thresholds, industry calibration, parallel opportunities | 5-15 issues |
| 3 | Analysis quality + practical effectiveness | Quantitative anchors, comparison tables, sell signals, self-check completeness | 5-12 issues |
| 4 | Content structure + execution logic | Token waste, step dependencies, data redundancy, template simplification | 10-17 issues |

**Key insight**: Each round uses a different lens, so issues found in Round 3 are genuinely invisible from Round 1's perspective. Don't stop after Round 1 even if it found 20 issues.

**Stopping signal**: When a round produces 0 new P0/P1 issues, the audit is complete.

**User preference (jw)**: "全量修改" means fix ALL issues from the current round before presenting results. Do not batch across rounds.

## Phase 4: Verification

After all changes:
1. `wc -l` on all files — confirm reduction
2. `grep` for each removed item — confirm deleted
3. `grep` for each new feature — confirm added
4. Run any scripts with `--help` — confirm they work
5. Search for remaining duplicates — confirm clean

## Output Format

Report the optimization as a summary table:

```
## 优化总结

### 删除的冗余内容
| 优化项 | 删除行数 | 说明 |
|--------|---------|------|

### 新增的实用内容
| 优化项 | 新增行数 | 说明 |
|--------|---------|------|

### 统一的内容
| 优化项 | 说明 |
|--------|------|

### 文件对比
| 文件 | 优化前 | 优化后 | 变化 |
|------|--------|--------|------|
```

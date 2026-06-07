# Multi-Round Audit Pattern

> Source: jw-content-summary v4.54→v4.59 audit (6 rounds, 33 fixes).

## Why Multiple Rounds?

Each round catches a different class of issue. A single audit pass is insufficient because:

| Round | Focus | Typical Finds |
|-------|-------|---------------|
| 1 | Functional bugs (P0) | Undefined variables, type conflicts, runtime crashes |
| 2 | Code-level (P1) | Hardcoded paths, unused functions, naming mismatches |
| 3 | Structural | Redundant files, orphaned sections, SKILL.md bloat |
| 4 | Documentation | Missing threshold rationale, vague triggers, unmapped checklists |
| 5 | Trigger accuracy | Missing casual phrasings, near-miss negatives |

## When to Stop

Stop when the latest round produces only P2 or lower issues with no functional impact. Signs of diminishing returns:
- Issues are purely cosmetic (formatting, wording)
- All script compilations pass
- SKILL.md is under target line count
- Validator runs clean on real test data

## SKILL.md Line Budget

Target: less than 500 lines. Common bloat sources and fixes:

| Source | Fix |
|--------|-----|
| Changelog with 20+ entries | Keep last 10, full history in references/changelog.md |
| Inline troubleshooting guides | Move to references/, keep 1-line pointer |
| Detailed step-by-step fallback flows | Move to references/, keep trigger condition + pointer |

## Pitfall: Ignoring Loaded Skills

If the user invokes /pua or any other skill, load it first before proceeding. The user loaded it for a reason - they want the output format and behavioral protocol it defines. Skipping it is a process failure, not a time-saver.

## "全量修" Workflow Pattern

When the user says "全量修" or "全量修复", they mean: fix ALL issues from the audit in one batch, do NOT propose incremental patches or ask for confirmation between fixes. This is a user preference for batch execution over iterative confirmation.

**Execution pattern**:
1. Complete the full audit first, produce categorized report (P0/P1/P2/P3)
2. When user says "全量修" → immediately start fixing ALL items, no confirmation needed
3. Fix P0 first (blocking), then P1 (quality), then P2 (maintenance), then P3 (cosmetic)
4. Parallelize where possible (template fixes and SKILL.md fixes can run in parallel via delegate_task)
5. End with a verification pass (grep for consistency checks)

**Anti-pattern**: Asking "需要我开始修复吗？建议从 P0 开始" when user already said "全量修". The user's instruction IS the confirmation.

**When to still confirm**: Only for irreversible operations (deleting files, removing entire sections) or when the audit reveals issues that have multiple valid fix strategies (e.g., "move to references" vs "delete entirely").

## Investment Skill Three-Round Audit Pattern

For complex analytical skills (like jw-company-analysis), a three-round audit pattern has been validated across multiple sessions:

| Round | Focus | Typical Finds |
|-------|-------|---------------|
| 1 | **Structural** | SKILL.md bloat (theory inline vs references), Step numbering conflicts, flow chart vs actual steps mismatch, template chapter numbering ≠ Step numbering |
| 2 | **Consistency** | Template scoring ranges ≠ SKILL.md scoring ranges, checklist item counts mismatch (template 7 vs SKILL.md 12), version number drift across files, "第X节" vs "§X" format inconsistency |
| 3 | **Quality** | Missing ESG scoring rules, Step 5 score range overflow, checkpoint failure no fallback, description step count wrong, orphaned reference files |

**Key insight**: Round 1 catches the big structural issues (600+ lines to move). Round 2 catches the sync issues between SKILL.md and template that Round 1's refactoring introduced. Round 3 catches the edge cases that only surface after the first two rounds are clean.

**Stopping after Round 3**: If Round 3 produces only P3 (cosmetic) issues, the skill is ready. Don't force a Round 4 — diminishing returns.

**Exception — Round 4+ still productive**: If the user explicitly asks for another round ("研究这个skill...分析...给出修改建议" repeated), Round 4 can still find significant issues that earlier rounds miss:
- **Scoring math validation**: Conclusion matrix ranges not matching actual score distributions (found in jw-company-analysis Round 3)
- **Scoring range asymmetry**: Score system labeled "±50" but actual range is -50 to +20 (found in jw-company-analysis Round 4)
- **Step compression**: Single Step 2× the size of others, needs "📚人类参考" compression (found in jw-company-analysis Round 4)
- **Agent execution feasibility**: 73 "详见" references pointing to 5000+ line files that agents won't read
- **Reference classification**: No distinction between "agent must-read" vs "human reference" content
- **Pre-execution script default scores**: Hardcoded defaults that agents accept without qualitative analysis
- **Template [X] placeholder density**: >100 placeholders in one step section = agent will miss items

**Exception — Round 5 patterns** (jw-company-analysis v3.19→v3.20, 13 fixes):
- **Pre-execution script sum crash**: scores/notes mixed in same dict → `sum()` on strings crashes. Script never ran successfully but passed all static checks. Lesson: **actually run the script once** during audit.
- **Conclusion matrix zombie ranges**: 6 tiers→4 because lower tiers unreachable after screening steps. Check by estimating minimum possible score after all pre-filters.
- **Scoring value residual references**: After fixing ±50→-50到+20, grep found 3-5 residual "±50" / "±5分" / "85-95" in other paragraphs. Always grep all variants after a numeric fix.

**Key insight**: Rounds 1-3 focus on human-readable quality. Round 4+ focuses on agent-executable quality — can an LLM agent actually follow this skill in 8-15 minutes? This is a different class of issue that only surfaces when someone asks "can this actually be executed?"

For Round 4+ audit patterns, see `references/agent-execution-feasibility-audit.md`.

### Version Naming for Multi-Round Refactoring

When multiple audit rounds happen in one session:
- Round 1: v3.10.0 (major refactoring)
- Round 2: v3.10.1 (consistency fixes)
- Round 3: v3.10.2 (edge case fixes)
- Book research: v3.11.0+ (new content)

Don't bump major version for audit fixes — those are patches, not features.

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

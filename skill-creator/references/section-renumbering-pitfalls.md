# Section Renumbering Pitfalls (after deleting a section)

When auditing a skill and removing a thin/orphaned section, subsequent section numbers create gaps. Renumbering seems simple but has hidden traps.

## The Problem

Skill SKILL.md uses `## N. Title` numbering. Deleting §8 means §9-§14 become orphaned (gap at 8). Renumbering §9→§8 etc. seems trivial, but:

1. **Subsection collision**: §6 has subsections §7.1/§7.2 (a pre-existing inconsistency). After renumbering §9→§7, new subsections §9.1→§7.1 COLLIDE with existing §7.1 under §6. Must rename to §6.1/§6.2 and §7.3/§7.4 respectively.

2. **Cross-reference cascade**: Functional references like "见 §9.1" in body text must update. Changelog entries referencing old numbers (historical) should NOT be updated.

3. **Table references**: Exception handling tables, version summary tables all contain `§N.M` references that need updating.

## Procedure

1. **Before deleting**: list ALL `§N.M` references in the file, classify as `functional` (body text) vs `historical` (changelog)
2. **Delete the section**, note the gap
3. **Renumber top-level**: §(gap+1)→§gap, §(gap+2)→§(gap+1), etc.
4. **Check subsection ownership**: which parent does each subsection ACTUALLY belong to? Fix numbering to match parent (e.g., §7.1 under §6 → §6.1)
5. **Update functional cross-references only** — leave changelog entries as-is
6. **Verify**: `grep -n "^## [0-9]"` shows sequential, `grep -n "^### [0-9]"` shows no duplicates

## Example (jw-content-summary v4.60)

Deleted §8 (阶段1四问 vs 阶段3五问, ~10 lines, merged into §4). Then:

| Original | After delete | Issue | Fix |
|----------|-------------|-------|-----|
| §9 全量自动运行 | §7 | OK | — |
| §10 质量红线 | §8 | OK | — |
| §7.1 单章主导型 (under §6) | still §7.1 | COLLISION with new §7 | → §6.1 |
| §7.2 长书策略 (under §6) | still §7.2 | COLLISION with new §7 | → §6.2 |
| §9.1 碎片化回退 (under §9) | §7.1 | COLLISION with §6.1 | → §7.3 |
| §9.2 全单碎片 (under §9) | §7.2 | COLLISION with §6.2 | → §7.4 |

Cross-references updated (6 functional), changelog left as-is (5 historical).

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

## Advanced: Step Reordering (merge + move + renumber)

When refactoring a skill with a complete step reordering (not just deleting one section), the complexity increases significantly. Example: jw-company-analysis v2.1.0 refactor.

### Scenario
- Merge Step 0.0/0/0.5/1 → new Step 0
- Renumber Step 2→1, Step 3→2, Step 4→3, Step 6→4, Step 7→5
- Move Step 6 (technical analysis) from between Step 3 and Step 4 to between Step 5 and Step 7
- Renumber all subsections (2.1→1.1, 3.1→2.1, etc.)

### Procedure

1. **Create full renumbering map first** — before any edits, write out:
   ```
   Old → New
   Step 0.0/0/0.5/1 → Step 0 (merge)
   Step 2 → Step 1
   Step 3 → Step 2
   Step 4 → Step 3
   Step 6 → Step 4 (move required!)
   Step 7 → Step 5
   Step 5 → Step 6 (move required!)
   Step 8 → Step 7
   Step 9 → Step 8
   ```

2. **Merge/consolidate first** — do the merge edits before any renumbering. This simplifies the file and reduces the number of sections to renumber.

3. **Renumber top-level sections incrementally** — use `patch` for each `## Step N:` header. Do them in order to avoid confusion.

4. **Renumber subsections** — after top-level renumbering, update all `### N.M` subsections. Use `search_files` to find all subsection references before starting.

5. **Move sections using head/tail** — when a section needs to move to a different position:
   ```bash
   # Remove the section from its current position
   head -N SKILL.md > part1.md
   tail -n +M SKILL.md > part2.md
   cat part1.md part2.md > SKILL_new.md
   mv SKILL_new.md SKILL.md

   # Insert at new position using patch
   ```
   Where N = line before the section starts, M = line after the section ends.

6. **Update cross-references** — search for all `Step N` references in body text and update them. Key places:
   - Weight tables
   - "详见 Step N" references
   - Output template structures
   - Pitfall/workaround sections

7. **Verify final order** — `grep -n "## Step"` should show sequential numbering with no gaps.

### Pitfalls specific to reordering
- **Forgetting to move a section**: If Step 6 needs to move before Step 7 but after Step 5, you must physically move it in the file. Just renumbering the header won't change its position.
- **Cross-reference updates in moved sections**: When moving a section, its internal references to other steps (e.g., "详见 Step 4") may need updating if those steps were also renumbered.
- **Weight table consistency**: The unified weight table at the top must match the actual step numbers after reordering. Update it LAST, after all steps are in their final positions.

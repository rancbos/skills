# Skill Maintenance Patterns

Patterns for keeping skills healthy over time — changelog integrity, token optimization, and structural hygiene.

## 1. Changelog Deduplication

**Problem**: Changelog files accumulate duplicate version entries when:
- A changelog is migrated from SKILL.md to `references/changelog.md` (migration appends without dedup)
- Multiple patches happen in the same session and entries are added without checking for existing versions
- Two changelog blocks coexist (inline SKILL.md + references/ file)

**Detection**: Run `grep "^## v" changelog.md | sort | uniq -d` — any output means duplicates exist.

**Fix** (Python):

```python
import re

sections = re.split(r'(^## v[\d.]+.*$)', raw_content, flags=re.MULTILINE)
version_dict = {}

for i in range(1, len(sections), 2):
    ver_header = sections[i].strip()
    ver_body = sections[i+1].strip() if i+1 < len(sections) else ""
    m = re.match(r'## (v[\d.]+)', ver_header)
    if m:
        ver_num = m.group(1)
        version_dict[ver_num] = (ver_header, ver_body)  # last occurrence wins

# Rebuild: header + sorted versions (newest first)
```

**Prevention**: When appending a new changelog entry, always check if the version already exists: `grep "^## v$NEW_VER" changelog.md`.

## 2. Token Optimization for Large Skills

When a skill's SKILL.md approaches or exceeds 500 lines, every line costs input tokens on every invocation. Optimize by moving low-value content out of SKILL.md:

| Content type | Location | Rationale |
|---|---|---|
| Changelog (>10 entries) | `references/changelog.md` | History doesn't guide execution |
| Detailed format specs | `references/validate-*.md` | Only needed when validating |
| Pitfall details (>5 lines) | `references/pitfall-*.md` | Only needed when that pitfall is hit |
| Version table (>10 rows) | Keep only recent 10 | Old versions in references/ |

**SKILL.md should contain**: trigger conditions, main workflow, quality gates, pitfall SHORT descriptions (1-2 lines + pointer to references/).

**SKILL.md should NOT contain**: full changelog, detailed error transcripts, complete format specifications, verbose version history.

## 3. Version Table Hygiene

Maintain a hard cap of 10-12 entries in any inline version table. When adding a new entry:
1. Add the new row at the top
2. Remove the oldest entry(s) beyond the cap
3. The removed entries are still in `references/changelog.md`

## 4. Orphaned Feature References

When a feature is removed (e.g., "Top 10 limit"), audit ALL files for references to it:
- SKILL.md body
- methodology/ files
- references/ files
- scripts/ comments
- The changelog entry describing the removal is fine to keep

**Detection**: `grep -r "removed_feature_name" skill-directory/` after each removal.

## 5. Section Renumbering After Deletion

When deleting a section, subsequent section numbers create gaps. Always renumber and verify no collision with existing subsections. See `references/section-renumbering-pitfalls.md` for the full procedure.

## 6. Validation-First Hardening

When optimizing data structures (truncating fields, removing columns, changing defaults), don't just apply the change and hope. Prove it's safe first:

1. **Snapshot the old**: create a copy of the pre-optimization data (`book-index-old.json`, `old-config.yaml`, etc.)
2. **Run both**: execute the downstream pipeline with both old and new data
3. **Compare outputs**: candidates count, scores, pass rates — whatever metrics the pipeline produces
4. **Assert zero delta**: if outputs differ, the optimization has side effects — investigate before committing
5. **Document the verification**: add validation data (numbers, pass/fail) to the code's docstring or a reference file so future maintainers know why the threshold was chosen

This pattern applies to any truncation, caching, or data reduction change. The key insight: **optimization without validation is gambling with quality**.

Example (jw-content-summary v4.68): `first_paragraphs` truncated to 200 chars + `last_paragraphs` deleted → pipeline comparison: 62 candidates, avg_score=89.52, 61 recommended, 1 appendix — identical to pre-optimization.

## 7. Post-Major-Expansion Audit Checklist

After systematically adding content to a skill (e.g., studying a book across 6 rounds, adding 100+ concepts), run this checklist BEFORE delivering the update:

| # | Check | How | Fix |
|---|-------|-----|-----|
| 1 | Duplicate version entries | `grep "vX.Y.Z" SKILL.md \| sort \| uniq -d` | Delete duplicates |
| 2 | Formula vs table consistency | Compare weight table with scoring formula text | Align formula to table |
| 3 | Template/flow structure sync | Compare output structure section with actual template file | Update whichever is stale |
| 4 | SKILL.md line count | `wc -l SKILL.md` — target <800 lines | Move detailed concepts to references/ |
| 5 | Two overlapping frameworks | Grep for similar framework names (e.g., "四步法" AND "三步法") | Merge into one |
| 6 | Internal section organization | Check if largest section has logical grouping | Add sub-grouping headers |

**Root cause of most issues**: Multiple subagents editing the same file across rounds without a consistency pass. The fix is always: audit after the last round, not after each round.

**SKILL.md bloat pattern**: When adding knowledge from books/sources, the default behavior is to dump explanations inline. Instead: SKILL.md gets a one-line summary + reference link; references/ gets the full explanation. Rule of thumb: if a concept explanation exceeds 3 lines, it belongs in references/.

## 8. Version Annotation Staleness

When a skill's version number changes, inline version references go stale. Distinct from section renumbering (§5) — this is about version strings, not section numbers.

**Common stale references**:
- `references/foo.md（v4.66 Token 优化模式）` → file updated to v4.68 but annotation still says v4.66
- `> 完整版本历史（v4.0-v4.66）见...` → current version is v4.68
- Changelog entry that says "版本号：4.65 → 4.66" but the actual version is now 4.68

**Detection after version bump**:
```bash
# Find all inline version references that might be stale
grep -rn "v4\.$OLD_VER" SKILL.md methodology/ references/
```

**Fix**: Update all inline version references to match the current version. The version annotation in `references/*.md` headers and `SKILL.md` prose should always reflect the current state, not the state when the file was first written.

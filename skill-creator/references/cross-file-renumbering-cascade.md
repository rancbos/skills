# Cross-File Renumbering Cascade

When SKILL.md undergoes section renumbering (merging, reordering, or shifting steps), ALL dependent files must be updated. This is the most common source of audit failures after large refactors.

## The Problem

A skill has multiple file types that reference step numbers:
- **SKILL.md** — the source of truth
- **Rubric files** (`references/scoring-rubric-*.md`) — detailed scoring criteria, each with section headers like `## 2.1 市场空间`
- **Calibration file** (`references/special-entities-calibration.md`) — rules referencing `Step 4.2`, `Step 5.3`, etc.
- **Checkpoint schema** (`references/checkpoint-schema.md`) — JSON structure with `step5_industry.json` filenames and `agent在Step 2评分` comments
- **Report template** — output format referencing step numbers

After SKILL.md renumbering, these files retain old numbers, causing agent confusion.

## Detection

After any renumbering, run these grep commands across ALL files:

```bash
# Find all Step N references
grep -rn 'Step [0-9]' references/

# Find section headers (## N.M format — doesn't match "Step N" grep)
grep -rn '^## [0-9]\.[0-9]' references/scoring-rubric-*.md

# Find JSON filename references
grep -rn 'step[0-9]_.*\.json' references/checkpoint-schema.md
```

## Fix: Temporary Placeholder Technique

Direct sed replacement fails because of cascading (replacing 4→5 then 5→6 corrupts the first change). Use temporary placeholders:

```bash
# Step 1: Replace old numbers with unique placeholders
sed -i 's/Step 4\.2/TEMP_52/g' file.md
sed -i 's/Step 5\.2/TEMP_62/g' file.md
# ... for all mappings

# Step 2: Replace placeholders with new numbers
sed -i 's/TEMP_52/Step 5.2/g' file.md
sed -i 's/TEMP_62/Step 6.2/g' file.md
# ... for all mappings
```

## Case Study: jw-company-analysis v4.1.0→v4.1.3

SKILL.md was renumbered (Step 2 merged into Step 1, all subsequent steps shifted). Three rounds of auditing were needed:

**Round 2** caught: weight table, formula, report template, output filenames in SKILL.md
**Round 3** caught: body text residuals, sub-section header mismatches
**Round 4** caught: ALL rubric/calibration/checkpoint files still using old numbers

8 files needed updates. The rubric files had `## 2.1` section headers that didn't match `Step 4` grep patterns — required separate `grep -P '^\#+ [0-9]'` detection.

## Prevention

After ANY section renumbering in SKILL.md:
1. Create the full old→new mapping table
2. grep ALL files for old numbers (not just SKILL.md)
3. Use temporary placeholders for sed
4. Verify with `grep -oP 'Step \d+'` across all files
5. Verify section headers with `grep -P '^\#+ [0-9]'` across rubric files

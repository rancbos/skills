# Investment Skill Formula Consistency Audit

When auditing investment/analysis skills that use weighted scoring, check these specific consistency patterns:

## 1. Sub-dimension Score vs Total Formula Mismatch

**Pattern**: A sub-step declares its max score in the heading (e.g., "0-25分") but the parent total formula uses a different number (e.g., `6.3(30)`).

**Detection**:
```bash
grep -n "满分.*分\|0-[0-9]*分" SKILL.md
grep -n "总分.*=.*×\|总分 = " SKILL.md
# Cross-check: do the formula components match the declarations?
```

**Case study**: jw-company-analysis v4.0.2 — Step 6.3 declared "0-25分" but total formula said `6.3(30)`. Correct total was 95, not 100.

## 2. Template Formula vs SKILL.md Logic Drift

**Pattern**: Template files edited independently → formulas drift. Most common: template includes components SKILL.md explicitly excludes.

**Detection**:
```bash
grep -n "总分.*=" templates/*.md
grep -n "总分.*=" SKILL.md
```

**Case study**: jw-company-analysis template Step 7 included "误判" in safety valve formula, but SKILL.md said "7.5 不参与安全阀".

**Fix**: After any SKILL.md refactoring that changes formula components, grep ALL templates for the old formula.

## 3. Conclusion Matrix Format Drift

**Pattern**: SKILL.md uses `>= 85` but template uses `≥85`. Both work for humans but grep-based checks miss mismatches.

**Fix**: Standardize on ASCII `>=` over Unicode `≥`.

## 4. Section Header Format Inconsistency

**Pattern**: Most steps use `## Step N：Title` but one uses `### N.Title`.

**Detection**: `grep -n "^## Step\|^### [0-9]" SKILL.md`

## 5. Absolute Threshold Calibration Gaps

**Pattern**: Hardcoded thresholds without data/time period basis.

**Fix**: Add calibration notes: "基于X数据Y年统计".

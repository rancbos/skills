# Skill Audit Checklist

When reviewing an existing skill for quality, use this checklist systematically. Each category has specific signals to look for and concrete fixes.

## 1. Logical Conflicts

**Signal**: Two sections give contradictory advice for the same situation.

**How to detect**:
- Two steps both claim to handle the same concept (e.g., "market state" and "emotion cycle" both define "退潮")
- Both steps give different position recommendations for overlapping states
- Decision trees in different steps produce conflicting outputs for the same inputs

**Fix**: Merge overlapping steps. Use intersection logic when two dimensions both apply: take the overlapping (conservative) range of their recommendations.

## 2. Step Ordering Issues

**Signal**: A step that depends on information from a later step is positioned before it.

**How to detect**:
- Step N gives advice that would be invalidated by Step N+K's classification
- A "judgment" step needs inputs that haven't been computed yet
- Users would need to backtrack to revise earlier conclusions

**Fix**: Move dependency-heavy steps earlier. Steps that synthesize multiple inputs should come after all their inputs are computed.

## 3. Absolute Thresholds Without Relatives

**Signal**: Decision trees use only absolute numbers ("> 50", "> 2万亿") without context.

**How to detect**:
- Thresholds are hardcoded with no mention of "compared to yesterday" or "relative to recent average"
- Same absolute number means different things in different market environments
- No guidance on what to do when a value is near the threshold

**Fix**: Add relative indicators ("较前日变化", "近5日均值"). Note that absolute thresholds need periodic recalibration.

## 4. Missing Data Sources

**Signal**: The skill references data categories but doesn't specify how to get them.

**How to detect**:
- Step says "check X" but doesn't say where X comes from
- Dependencies listed in §3 don't cover all data needed in the flow
- No fallback strategy when a data source is unavailable

**Fix**: For each data point, specify: source tool, expected format, and degradation behavior when missing.

## 5. Vague Thresholds in Dependent Steps

**Signal**: A step says "if X is high" without defining "high".

**How to detect**:
- Qualitative terms ("significant", "extreme", "moderate") without numeric anchors
- Terms like "外资加仓" without defining the threshold (e.g., "> 50亿 net inflow")
- "轮动过快" without specifying what "too fast" means

**Fix**: Add concrete thresholds. For continuous values, specify the breakpoint. For relative judgments, specify the comparison basis.

## 6. Orphaned Sections

**Signal**: Sections that are too thin to stand alone, or that duplicate content elsewhere.

**How to detect**:
- A section has < 10 lines and no unique content
- Two sections cover the same topic from slightly different angles
- An appendix section could be folded into the main flow

**Fix**: Merge thin sections into adjacent ones. For template/appendix sections, add "when to use this" guidance that ties them to the main flow.

## 7. Self-Check Without Mapping

**Signal**: A checklist at the end that doesn't reference which step each item corresponds to.

**How to detect**:
- Checklist items are generic ("did you write X?") without pointing to the step that produces X
- Some items are process-level ("avoid empty words") mixed with output-level ("write position size")

**Fix**: Annotate each checklist item with the step number it validates. Separate output checks from process checks.

## 8. Template/Flow Disconnect

**Signal**: Templates (盘前/盘后) exist but don't explain when or how they integrate with the main analysis flow.

**How to detect**:
- Template section says "use this format" but doesn't say "run steps 1-4 first, then fill in this template"
- Template output fields don't map to specific analysis steps
- No guidance on which steps to skip vs. run for a "quick" template fill

**Fix**: Add "使用时机" and "执行顺序" to each template. Map template fields to analysis steps.

## 9. Description Triggering

**Signal**: The skill description is too narrow, missing common phrasings users would actually use.

**How to detect**:
- Description only covers formal terms ("大势研判") but not casual queries ("今天大盘怎么看")
- No mention of action-oriented triggers ("该加仓还是减仓")
- Missing scenario triggers ("盘后复盘", "盘前判断")

**Fix**: Add 5-10 realistic user phrasings to the description. Include both formal and casual language.

## Process

1. Read the full SKILL.md
2. Check each category above in order
3. For each issue found, note: category, location (section/line), severity (高/中/低)
4. Fix high-severity issues first
5. Verify the fix doesn't introduce new conflicts
6. Bump version number

**When deleting a section**: subsequent section numbers create gaps. Renumber and check for subsection collision (e.g., §7.1/§7.2 under §6 will collide with new §7 after deleting §8). See `references/section-renumbering-pitfalls.md` for the full procedure.

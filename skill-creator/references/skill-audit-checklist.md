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

### 8b. Template Checklist Drift

A specific subtype of template/flow disconnect: the SKILL.md defines a checklist (e.g., "建仓终检清单 12项") and the template has a copy of the same checklist, but the wording, criteria, or item count diverged over incremental edits.

**Detection technique**: Extract checklist items from both SKILL.md and template (grep for `| ①` or similar numbered-row patterns). Compare item count, item names, **and criteria text**. If SKILL.md says "能力圈：我能理解这家企业？" but template says "能力圈理解", that's drift — the template lost specificity. **Subtler case**: item count matches but thresholds differ (SKILL.md: "优秀企业>30%" vs template: "A股>30%") — use `grep -oP '⑤.*?\|'` to extract and compare the "通过标准" column content, not just item count.

**Fix**: SKILL.md is the source of truth. Update the template's checklist to match SKILL.md exactly (same item names, same criteria, same thresholds).

## 9. Description Triggering

**Signal**: The skill description is too narrow, missing common phrasings users would actually use.

**How to detect**:
- Description only covers formal terms ("大势研判") but not casual queries ("今天大盘怎么看")
- No mention of action-oriented triggers ("该加仓还是减仓")
- Missing scenario triggers ("盘后复盘", "盘前判断")

**Fix**: Add 5-10 realistic user phrasings to the description. Include both formal and casual language.

## 10. Terminology Definition Gaps

**Signal**: Domain-specific terms are used throughout the skill without ever defining them.

**How to detect**:
- A term appears in decision trees, tables, and checklists but has no "定义" or "术语" section
- Different readers could interpret the same term differently (e.g., "首板晋级率" — is the denominator total 首板 or only successfully-sealed 首板?)
- Related terms are used interchangeably without distinction (e.g., "连板晋级率" vs "首板晋级率")
- A term appears in output templates or checklists but was never formally defined (e.g., "炸板率" used in templates but missing from the terminology block)

**Fix**: Add a terminology block (blockquote or definition list) near the first occurrence of each domain term. Include the formula and what counts as the denominator. Place it before the first decision tree that uses the term. When adding definitions, check ALL output templates and checklists for undefined terms — the templates are often where undefined terms hide because they're written last and copied verbatim.

## 11. Absolute/Relative Threshold Contradiction

**Signal**: The skill states a principle like "use relative values, not absolute thresholds" but then has absolute numbers scattered in decision trees or judgment criteria.

**How to detect**:
- A section header or preamble says "使用相对值" or "不依赖绝对阈值"
- But inline thresholds use hardcoded numbers ("> 50亿", "3次以上", "2万亿") without a relative comparison basis
- The absolute number loses meaning as market scale changes over time

**Fix**: For each absolute threshold, either (a) convert to a relative form ("较近20日均值的2倍", "近6个月月均的N倍") or (b) explicitly note that the number needs periodic recalibration and add a comment explaining its current basis.

## 12. Residual Language After Repositioning

**Signal**: A skill's purpose has shifted (e.g., from "investment guidance" to "market understanding"), but domain-specific language from the old positioning lingers in subsections.

**How to detect**:
- Grep for terms from the OLD positioning (e.g., "仓位", "止盈", "止损", "加仓", "减仓", "操作建议") after the skill has been repositioned
- Section titles or table headers still use old framing (e.g., "操作建议" when the skill now focuses on "走势理解")
- The "最终原则" or "总结" section restates old goals that contradict the new description
- **Cross-reference format definitions**: When a skill defines a format in one place (e.g., "一句话结论的写法") and uses it in a template elsewhere, the two can drift. Compare the format definition against every template that claims to follow it. Look for synonyms that slipped in (e.g., "策略偏" vs "特征偏") — these are the hardest to catch because they feel interchangeable to a casual reader but carry different connotations.

**Fix**: After any repositioning change, do a full-text grep for 5-10 key terms from the old positioning. Replace with neutral equivalents that match the new purpose. Pay special attention to: section headers, table column names, checklist items, and the final principles section.

### 12b. Template Wording Drift

A specific subtype of residual language: the skill's core positioning shifts, but template output fields retain old framing. This is particularly insidious because templates are copy-pasted by the model, so the old language propagates into every output even if the rest of the skill is correct.

**Detection technique**: After any repositioning, compare each template's column headers, field names, and placeholder text against the current description's key terms. If the description says "走势理解" but a template column says "操作建议", that's a hit.

## 13. Threshold Calibration Metadata

**Signal**: Absolute thresholds remain in the skill (because they can't be converted to relative), but there's no indication of when or why to recalibrate them.

**How to detect**:
- A hardcoded number ("> 3%", "< 10%") has no comment about what market condition it's calibrated to
- The number would become meaningless if market volatility or scale changed significantly
- No "last calibrated" note or review trigger

**Fix**: For each absolute threshold that must remain, add a parenthetical note explaining: (a) what it's calibrated to (e.g., "based on current A-share daily volatility"), (b) a review trigger (e.g., "recalibrate if market volatility changes significantly"). This turns a silent assumption into an explicit one.

### 12c. Version Drift Across Files

A specific form of inconsistency: the skill's version number appears in multiple locations (SKILL.md frontmatter, SKILL.md title/H1, template version field, checkpoint-schema version, script headers) and they get out of sync during edits.

**Detection technique**: Grep for the version pattern (e.g., `v\d+\.\d+\.\d+`) across SKILL.md and all template/checkpoint-schema files. Compare each hit against the frontmatter version (source of truth). Common drift: frontmatter bumped to v4.0.3 but title still says v4.0.2.

**Fix**: Identify all locations where the version appears, then update each to match frontmatter. After fixing, grep again to confirm no residual old versions.

## 14. Cross-Skill Dependency References

**Signal**: SKILL.md references scripts or files from another skill using relative paths (e.g., `scripts/fetch_market_data.py`) as if they're part of the local skill.

**How to detect**:
- SKILL.md contains `scripts/` or `references/` paths that don't exist in the skill's own directory
- Paths like `~/.hermes/skills/<other-skill>/scripts/...` are hardcoded in the SKILL.md body
- The skill's `linked_files` doesn't list the referenced files (because they belong to another skill)

**Fix**: Replace relative paths with descriptive references. Instead of `python scripts/fetch_market_data.py`, write: "调用 jw-investment-data skill 的 `fetch_market_data.py` 脚本（详见该 skill 的 scripts/ 目录）". Keep the call syntax inline but make it clear the script is external. This prevents confusion when the skill is shared, renamed, or the external dependency moves.

## 15. Template File Integrity

**Signal**: Template files have been corrupted by `read_file` output being written back — every line starts with `N|` prefix (e.g., `1|# Title`, `2|`, `3|> text`).

**How to detect**:
- `head -5 templates/*.md` shows lines starting with digits followed by `|`
- `grep -c '^[0-9]*|' templates/*.md` returns a count matching total line count
- **Pitfall**: `grep '^[0-9]*|'` also matches markdown table pipes (`| col |`). Always verify with `head -5` — if lines start with `#` or text (not `N|`), it's a false positive from table syntax, not corruption.
- This corruption is **invisible in `skill_view` output** (which itself adds line numbers), making it the hardest issue to spot without raw file inspection

**Fix**: Strip prefixes with `python3 -c "import re; c=open(f).read(); open(f,'w').write(re.sub(r'^(\d+)\|','',c,flags=re.MULTILINE))"`, then verify with `head -5`.

**Prevention**: Never pipe `read_file` output directly into `write_file`. Always strip `NUM|` prefixes first. Applies to any file, not just templates.

## Audit Workflow

Before diving into the 15 categories, do a quick structural pass:

0. **Check template file integrity** (Category 15): `head -5 templates/*.md` — if any line starts with `N|`, the template is corrupted. Fix BEFORE proceeding with other categories, as corrupted templates will produce false positives in other checks.
1. **Grep for positioning keywords** (Category 12): If the skill has been repositioned, grep for 5-10 terms from the old positioning first. This catches the most common and hardest-to-spot issues.
2. **Check templates against current positioning** (Category 12b): Read each template section and compare field names/column headers against the current description's key terms.
3. **Search for vague threshold language** (Category 5): Grep for "显著", "极端", "适度", "过大", "过快", "持续" without numeric anchors nearby.
4. **Check relative-principle vs inline-threshold consistency** (Category 11): If a section header says "使用相对值" or "不依赖绝对阈值", scan the section body for any hardcoded numbers.
5. **Verify terminology completeness** (Category 10): For each domain term used in decision trees or checklists, verify it has a definition before its first use. Pay special attention to output templates — they often contain undefined terms because they're written last.
6. **Check remaining absolute values for calibration notes** (Category 13): Any hardcoded number that survived the relative-value conversion should have a calibration comment.
7. **Check cross-skill dependency references** (Category 14): Grep for `scripts/` and `references/` paths in SKILL.md. For each, verify the file exists in the skill's own directory. If it doesn't, it's likely an external dependency — flag it to use descriptive references instead of relative paths.
8. **Check version consistency** (Category 12c): Grep for version pattern across SKILL.md (frontmatter + title) and templates/. All hits should match the frontmatter version.
9. **Verify section numbering after any deletions**: If sections were deleted in prior edits, check for gaps and subsection collisions.

## Process

1. Read the full SKILL.md
2. Run the Audit Workflow above for quick structural detection
3. Check each category above in order
4. For each issue found, note: category, location (section/line), severity (高/中/低)
5. Fix high-severity issues first
6. Verify the fix doesn't introduce new conflicts
7. Bump version number and add changelog entry

**When deleting a section**: subsequent section numbers create gaps. Renumber and check for subsection collision (e.g., §7.1/§7.2 under §6 will collide with new §7 after deleting §8). See `references/section-renumbering-pitfalls.md` for the full procedure.

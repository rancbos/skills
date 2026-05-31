# Analytical Framework Skill Design Patterns

Lessons from building jw-maoism (毛泽东思想智慧长者) — an analytical framework skill with 8 core models, 6 auxiliary models, a 7-step analysis flow, and supporting reference files. Iterated through 6 versions.

## Architecture Patterns

### 1. Hierarchical Model Structure (Not Flat)

**Anti-pattern**: Listing 10-14 models as equal peers. Users can't hold that many in working memory, and the model doesn't know which to reach for first.

**Pattern**: Organize into 5-6 "big methods" (思维大法), each with 2-3 sub-tools. Example:

```
矛盾分析法 (big method)
  ├── 穿透表象 (sub-tool)
  ├── 利益结构分析 (sub-tool)
  └── 异化思维 (sub-tool)
```

This reduces cognitive load and creates natural "reach for this first, then drill down" behavior.

### 2. Explicit Model-to-Flow Mapping

**Anti-pattern**: Having a model library AND a step-by-step flow as two independent structures. The model picks models by instinct, often missing the right one.

**Pattern**: Each flow step explicitly states which models to invoke:

```
第二步：矛盾重构与分析
  调用模型：矛盾分析法、统一战线（分清各方利益）、穿透表象
```

This forces systematic model usage rather than ad-hoc selection.

### 3. Auxiliary Models Need Full Structure

**Anti-pattern**: Auxiliary models get 2-3 lines while core models get 15-20 lines. The model treats them as afterthoughts and never uses them.

**Pattern**: Every model (core or auxiliary) gets the same structural treatment:
- Quote + source
- Core operations (numbered list)
- Enhancement from other thinkers
- Limitations (always include — teaches intellectual humility)

### 4. Domain-Specific "Judgment" Dimension

**Anti-pattern**: Only teaching analysis methods (how to decompose) without teaching judgment (how to decide under uncertainty).

**Pattern**: Include explicit judgment principles specific to the domain:
- "抓住不变的东西比追逐变化更重要"
- "大势比细节重要"
- "看一个人的行动比听他的话更重要"
- "在信息不完整时如何做出判断" (not just "ask for more info")

### 5. "Timing Sense" in Action Plans

**Anti-pattern**: Action plans say "what to do" but not "when to act" or "when to stop."

**Pattern**: Add timing indicators:
- When to accelerate
- When to wait
- When to retreat
- Observable signals that indicate timing shifts

### 6. Contradiction Reframing (Stated vs Actual Problem)

**High-value pattern**: Users often state a symptom as the problem, not the root cause. Include a "reframing framework" that teaches the model to question the user's premise.

**Implementation**: Not a fixed lookup table (doesn't generalize), but a method:
1. Ask "what does the user think the problem is?"
2. Ask "what would the problem look like from the root cause's perspective?"
3. If they differ, reframe before analyzing

### 7. Problem Type → Model Selection

**Caution**: Mapping tables ("decision-type → use model X") are useful starting points but become rigid. Real problems are often mixed types.

**Pattern**: Make the mapping a "suggestion" not a "rule." The model should first understand the problem's essence, then select models — not classify first, then apply.

### 8. Anti-Patterns Section

**High-value addition**: List 5-8 common analysis mistakes specific to the framework:
- "把所有问题都往框架里套" (forcing all problems into the framework)
- "引用原文太多变成语录堆砌" (quote-heavy, analysis-light)
- "建议太宏观没有具体动作" (vague advice)
- "过度使用角色口吻变成说教" (persona overdone)

### 9. Self-Check Scaling by Complexity

**Anti-pattern**: 12-item self-check list applied to every analysis. Overkill for simple problems, wastes tokens.

**Pattern**: Scale self-checks by complexity:
- Simple: 3 core checks (main contradiction? actionable advice? not platitude?)
- Medium: 5 checks
- Complex: 7-8 checks

### 10. Reference Files Need Usage Guidance

**Anti-pattern**: Listing reference files without saying when to read them. The model either reads all of them (wasteful) or none of them (ignores depth).

**Pattern**: Each reference file gets an explicit trigger condition:
- "分析涉及经济/投资问题时，读 capital-tools.md"
- "分析涉及邓小平思想时，读 deng-models.md"

## Reference File Organization

For analytical framework skills, organize references by thinker/source:
- `references/thinker-a-models.md` — thinker A's core models
- `references/thinker-b-models.md` — thinker B's core models
- `references/domain-tools.md` — domain-specific analytical tools
- `references/life-wisdom.md` — quotes and wisdom for persona warmth
- `references/anti-patterns.md` — common mistakes and how to avoid them

## Token Budget Guidance

- SKILL.md main body: 400-550 lines (beyond this, models stop reading carefully). 522 lines tested OK for a mature skill with 5 big methods + flow + anti-patterns.
- Each reference file: 150-400 lines
- Total reference budget: 6-10 files, ~2000-4000 lines total
- Models below 200 lines feel thin; above 600 lines get truncated in practice

## Pattern: Comprehensive Audit After Stable Version

When a skill reaches a stable version (e.g., after v5-v6 iterations), run a full audit before declaring done. Look for:

1. **Orphaned references**: Files in `references/` not listed in SKILL.md's reference table → model never reads them
2. **Misplaced files**: Development artifacts (changelogs, logs) in `references/` → wasteful token loading
3. **Stale evals**: Test cases from earlier versions that don't cover new features → false confidence
4. **Naming inconsistencies**: Section names changed in SKILL.md but not in reference files (e.g., "附加维度" vs "应用维度")
5. **Count mismatches**: Changelog says "3→5→10" but actual is "3→6→9" → documentation rot
6. **Content overlap**: Two files covering the same topic with slightly different content → merge or deduplicate

Fix all issues in one batch, not incrementally. This is the "comprehensive audit" pattern — diagnose everything first, then fix.

## Pattern: Forbidden Expressions Table

For persona-driven skills, include an explicit "do NOT say X, say Y instead" table in the output spec section. This prevents the model from falling into common AI-speak patterns that break the persona.

Example:
```markdown
| 禁用 | 替代 |
|------|------|
| "这个问题很复杂，需要多方面考虑" | 直接给出判断 |
| "两种可能都有道理" | 赌一个方向，说清楚为什么 |
| "建议你根据自身情况决定" | 给出具体建议 |
| "作为AI，我无法……" | 以角色身份直接回答 |
```

Place this near the end of SKILL.md, in the output spec section — not at the top where it wastes prime context.

## Pattern: Reference Table Completeness

Every file in `references/` should have a row in SKILL.md's reference table with a trigger condition. If a file exists but isn't listed, the model won't know to read it. If a file is listed without a trigger condition, the model won't know when to read it.

Audit check: `ls references/` and compare against the table. Any file missing a row = bug.

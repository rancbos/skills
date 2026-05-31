# Eval-Driven Skill Improvement: Root Cause Diagnosis Patterns

When an eval fails, the root cause is almost always in the **skill definition**, not the model. This reference captures diagnostic patterns for common eval failure modes.

## Diagnosis Workflow

```
eval fails → classify failure type → locate root cause in SKILL.md → patch → re-run single eval → verify
```

Don't re-run all evals after a fix. Re-run only the failing eval to save tokens and time.

## Failure Type → Root Cause → Fix Pattern

### 1. Misclassification (model picks wrong category/branch)

**Symptom**: Model chooses "medium" when it should choose "complex", or takes wrong branch in decision tree.

**Root cause**: Soft criteria with overlapping boundaries. Model interprets the overlap in its favor (usually toward the simpler/cheaper path).

**Fix**: Add **hard rules** that override the soft criteria. Structure as "if ANY of these conditions → always choose X". Concrete examples:

```markdown
| Complexity | Characteristics | Steps |
|---|---|---|
| Simple | Single contradiction, sufficient info | 3 steps |
| Medium | 2-3 contradictions, need trend judgment | 5 steps |
| Complex | Multiple intertwined contradictions | 7 steps |

**Hard rules (override above):**
- Survival problems → always complex
- 3+ stakeholders in conflict → always complex
- Irreversible decisions with time pressure → always complex
```

Key insight: Models handle "if X then Y" rules much better than "X tends toward Y" soft criteria when the stakes of misclassification are high.

### 2. Missing Section (model skips a required part)

**Symptom**: Model produces good analysis but omits a section the skill defines (e.g., timing judgment, risk warnings, follow-up questions).

**Root cause**: The section is described as optional, or the trigger condition is vague ("when relevant"), or the section lacks a clear prompt that forces the model to generate it.

**Fix**: 
- Make it mandatory: "所有问题必做" (required for all problems)
- Add it to the self-check list
- Add an anti-pattern that flags its absence
- Link it to the complexity tier: "中等/复杂问题必做"

### 3. Format/Style Violation (right content, wrong form)

**Symptom**: Model gives good analysis but uses forbidden expressions, hedging language, or probability-distributed conclusions.

**Root cause**: The "禁用表达" (forbidden expressions) table exists but isn't reinforced enough. The model falls back to safe, hedge-y defaults under uncertainty.

**Fix**:
- Add the forbidden expressions to the **anti-patterns** section with explicit examples
- Add them to the **self-check** list as negative checks
- Provide the replacement pattern inline, not just in a separate table

### 4. Semantic Drift (model does X but calls it Y)

**Symptom**: Model uses the skill's vocabulary ("contradiction analysis") but applies it superficially (listing contradictions without identifying the primary one).

**Root cause**: The skill describes the concept but doesn't require the specific output format that proves understanding.

**Fix**: Require explicit output markers:
- "必须宣告：`当前的主要矛盾是：______`"
- "必须说：'我判断……'"
- "必须说：'如果……这个判断就会翻盘'"

These force the model to commit to a position rather than describe the framework.

### 5. Reference Not Loaded (model doesn't read supplementary files)

**Symptom**: Model produces good but shallow output, missing depth that exists in reference files.

**Root cause**: The reference file loading guidance is buried or conditional ("when needed"). Model defaults to not loading.

**Fix**: 
- Add explicit trigger conditions: "分析涉及经济问题时，读 `references/capital-tools.md`"
- In the flow steps, annotate which references to load: "**调用参考**：`references/xxx.md`"

## Skill Audit Checklist (before running evals)

When picking up an existing skill to evaluate or improve, run this quick consistency check first. Catches structural issues that waste eval tokens.

1. **Frontmatter vs body**: Does the `description` in YAML match what the SKILL.md body actually does? (Stale descriptions cause triggering failures)
2. **Reference files exist**: Do all files referenced in SKILL.md actually exist on disk? Do any files in `references/` NOT referenced in SKILL.md? (Orphan files waste discovery effort; missing files cause shallow output)
3. **evals.json schema**: Does every eval have an `expectations` array? (Without it, grading can't run — the viewer expects `text`, `passed`, `evidence` fields in grading.json)
4. **Changelog version**: Does the changelog cover the current version? (Version gaps indicate undocumented changes)
5. **Content deduplication**: Is the same content in both SKILL.md and a reference file? (Pick one canonical location; the other should be a pointer)

Fix any issues found before running evals — structural problems make eval results unreliable.

## Quick Self-Check Before Patching

1. **Is the fix generalizable?** Don't overfit to one eval case. The fix should help with all similar cases.
2. **Does the fix add token cost?** Every instruction in SKILL.md is loaded every time. Prefer reference files for detailed content.
3. **Does the fix conflict with existing instructions?** Check for contradictions with anti-patterns or other sections.
4. **Is the fix testable?** After patching, re-run the failing eval. If it passes, the fix works. If not, the root cause was wrong.

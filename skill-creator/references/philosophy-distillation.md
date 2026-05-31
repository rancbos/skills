# Philosophy Distillation Pattern

When creating a skill that distills wisdom from large text corpora (books, essays, speeches) into an actionable analysis framework, follow this pattern.

## Step 1: Survey Source Material

- Check /root/books/ or the relevant source directory
- List all relevant files with sizes (use `ls -lh`)
- For files > 1MB, plan strategic sampling rather than full reads
- Identify existing reference skills in /root/mydata/skills---/ that cover similar territory

## Step 2: Parallel Research with Subagents

Spawn 3 subagents in parallel, each covering one author/source:

```
delegate_task(tasks=[
  {goal: "Extract core mental models from [Author A]", context: "source paths, output path, extraction format"},
  {goal: "Extract core mental models from [Author B]", ...},
  {goal: "Extract core mental models from [Author C]", ...},
])
```

Each subagent should:
1. Read the first 100-200 lines to understand structure
2. Search for key methodology/philosophy terms
3. Read key passages in full
4. Output structured extraction:
   - 5-8 named thinking models (one-line definition + core principle + application + limitations)
   - 5-8 decision heuristics
   - Language style characteristics
   - How this thinker differs from/complements others

## Step 3: Synthesize into Skill

- Combine extracted models into a coherent framework
- Deduplicate overlapping concepts (e.g., "实事求是" appears in Mao, Deng, Xi — pick the richest version, note variations)
- Create a unified persona that embodies the combined wisdom
- Design an analysis flow that naturally draws on all sources

## Step 4: Test with Baseline Comparison

- Design 2-3 realistic test prompts covering different domains
- Run each prompt twice: with_skill and without_skill (baseline)
- Grade against assertions focused on:
  - Framework-specific elements (e.g., "uses contradiction analysis")
  - Quality of judgment (clear directional bet, not probability distribution)
  - Actionability of advice (specific timeframes, not vague directions)
  - Persona consistency (tone, metaphors, voice)

## Step 5: Comprehensive Audit

After the skill reaches a stable version, run a full audit:
1. Compare `ls references/` against the SKILL.md reference table — every file needs a row with a trigger condition
2. Check for misplaced files (changelogs, logs don't belong in references/)
3. Verify section naming is consistent across SKILL.md and all reference files
4. Check evals cover all new features (not just the original test cases)
5. Verify counts and numbers in changelog match actual content

Fix all issues in one batch.

## Step 6: Iterate

- Read feedback, identify gaps
- Expand reference files for depth
- Re-test

## Pitfalls

- **Don't just copy-paste quotes.** Extract operational frameworks that can be applied to any problem.
- **Don't make it academic.** The goal is a practical thinking tool, not a literature review.
- **Don't lose the persona.** The voice and character are as important as the frameworks.
- **Token budget:** With-skill runs cost ~2-3x tokens vs baseline due to SKILL.md loading. Keep SKILL.md under 550 lines; push depth to references/. A mature skill with 5 big methods + flow + anti-patterns can reach 522 lines and still work well — the key is that every line must earn its place.

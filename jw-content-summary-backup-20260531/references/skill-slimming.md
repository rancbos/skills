# Skill Slimming / Progressive Disclosure Refactor

Use this reference when `jw-content-summary` or another large workflow skill grows into a mixed “manual + changelog + troubleshooting archive”. The goal is to reduce runtime context without deleting capability.

## Main principle

Do not slim by removing functionality. Slim by separating runtime control from low-frequency detail:

- `SKILL.md`: high-frequency runtime control plane — triggers, inputs, core workflow, output contract, gates, quality bars, and pointers.
- `methodology/`: stage-by-stage execution details.
- `references/`: edge cases, session-derived traps, historical notes, provider quirks, examples, and long troubleshooting recipes.
- `scripts/`: deterministic probes, validators, converters, clustering, or other repeatable mechanics.

A good slimmed skill should answer: when to use it, how to run the main path, what must not go wrong, and where to look when a specific exception appears.

## Recommended sequence

1. Back up the full skill directory before editing.
2. Inventory current files and read the current `SKILL.md`.
3. Classify each section:
   - keep in `SKILL.md`: trigger, input requirements, workflow skeleton, output structure, gates, quality checklist, essential pitfalls.
   - move to `references/`: rare errors, concrete historical cases, long examples, detailed fixes, changelog history.
   - move to `methodology/`: detailed phase execution.
   - keep in `scripts/`: deterministic checks and transforms.
4. Create support files first, then replace long sections in `SKILL.md` with short pointers.
5. Remove duplicate or obsolete competing rules; keep one authoritative rule in `SKILL.md`.
6. Update version and changelog.
7. Verify frontmatter, referenced paths, support files, and line/byte counts.

## What to keep in SKILL.md

- Skill mission and boundaries.
- Trigger conditions and near-miss exclusions.
- Required inputs and “do not proceed without X” constraints.
- Main workflow table or concise step list.
- Output structure / file contract.
- User confirmation gates or quality gates.
- Red-line quality constraints.
- A compact exception index pointing to support files.
- A short version summary with link to full changelog.

## What to move out

- Long changelog tables.
- Session-specific fixes and error transcripts.
- Detailed examples that illustrate a rule but are not themselves the rule.
- Debugging recipes needed only when something fails.
- Alternate task modes that are adjacent but not the main class; either move to references or split to a sibling class-level skill if they become common.

## After slimming: upgrade gates, not prose

Once `SKILL.md` has already been reduced to a runtime control plane, do not keep squeezing the main file for marginal line-count wins. The next durable improvement is usually deterministic quality infrastructure:

- align validators with the latest extractor schema;
- expose quality signals as JSON rather than relying on agent judgment;
- upgrade clustering from title-only matching to multi-signal matching;
- generate a decision package before final writing;
- make the final stage consume a plan file instead of freely re-reading every candidate.

For `jw-content-summary`, this became the v4.4 quality-gate pattern: `validate_candidates.py` → `cluster_candidates.py` → `score_candidates.py` → `build_summary_plan.py`. Apply the same pattern to other large workflow skills when the main prompt is already lean but outputs still depend on subjective handoff quality.

## Verification checklist

- [ ] `SKILL.md` still has valid frontmatter and required `name` / `description`.
- [ ] Description is under validator limits.
- [ ] Version incremented when behavior or structure changed.
- [ ] Changelog updated.
- [ ] Every referenced `references/`, `methodology/`, `templates/`, or `scripts/` path exists.
- [ ] No two sections give conflicting rules for the same decision.
- [ ] Main workflow still preserves original user-visible behavior.
- [ ] Backup path is recorded in the final report.

## Reporting to the user

Report concrete before/after facts, not just intentions:

- backup path
- changed files
- new support files
- line/byte count change if measured
- version bump
- validation result
- what changed structurally and what did not change functionally

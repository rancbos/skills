---
name: skill-creator
description: Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy.
---

# Skill Creator

A skill for creating new skills and iteratively improving them.

At a high level, the process of creating a skill goes like this:

- Decide what you want the skill to do and roughly how it should do it
- Write a draft of the skill
- Create a few test prompts and run claude-with-access-to-the-skill on them
- Help the user evaluate the results both qualitatively and quantitatively
  - While the runs happen in the background, draft some quantitative evals if there aren't any (if there are some, you can either use as is or modify if you feel something needs to change about them). Then explain them to the user (or if they already existed, explain the ones that already exist)
  - Use the `eval-viewer/generate_review.py` script to show the user the results for them to look at, and also let them look at the quantitative metrics
- Rewrite the skill based on feedback from the user's evaluation of the results (and also if there are any glaring flaws that become apparent from the quantitative benchmarks)
- Repeat until you're satisfied
- Expand the test set and try again at larger scale

Your job when using this skill is to figure out where the user is in this process and then jump in and help them progress through these stages. So for instance, maybe they're like "I want to make a skill for X". You can help narrow down what they mean, write a draft, write the test cases, figure out how they want to evaluate, run all the prompts, and repeat.

On the other hand, maybe they already have a draft of the skill. In this case you can go straight to the eval/iterate part of the loop.

Of course, you should always be flexible and if the user is like "I don't need to run a bunch of evaluations, just vibe with me", you can do that instead.

Then after the skill is done (but again, the order is flexible), you can also run the skill description improver, which we have a whole separate script for, to optimize the triggering of the skill.

Cool? Cool.

## Renaming a Skill

There is no native `rename` action. The workaround is `delete(old, absorbed_into=new)` + `create(new)`. **Critical pitfall**: `absorbed_into` only transfers the SKILL.md content — linked files (scripts/, references/, templates/, assets/) are NOT copied. After renaming:

1. `skill_manage(action='create', name=new-name, content=<old SKILL.md with name field updated>)`
2. `skill_manage(action='delete', name=old-name, absorbed_into=new-name)`
3. Manually recreate or copy all support files (scripts/, references/, templates/) into the new skill directory
4. Verify with `skill_view(name=new-name)` that `linked_files` lists all expected files

## Auditing Existing Skills

When asked to review or audit an existing skill, use the systematic checklist in `references/skill-audit-checklist.md`.

## Merging a New Framework into an Existing Skill

When the user provides a new framework/outline to merge into an existing skill (e.g., "融合这个大纲到现有结构"), follow this structured workflow:

### Phase 1: Backup + Compare
1. **Backup first**: `cp -r <skill-dir> <skill-dir-backup-YYYYMMDD>` — always before any structural changes
2. **Load existing skill** via `skill_view` and read the user's new framework
3. **Create a mapping table**: for each item in the new framework, identify the corresponding existing section (or mark as "NEW")

### Phase 2: Propose Fusion
4. **Present the mapping** as a table showing: new framework item → existing section → delta (same/modified/new/conflict)
5. **Propose weight allocation** if the skill uses weighted scoring — make the first proposal yourself rather than asking the user to guess
6. **Identify decision points** that need user confirmation (weight splits, step ordering, scoring granularity)
7. **Let the user confirm** before executing — don't start modifying until the fusion plan is agreed

### Phase 3: Execute + Verify
8. **Execute in blocks** — write the merged SKILL.md in logical chunks (frontmatter+overview, then each major step)
9. **Sync all dependent files** — scripts, templates, references, checkpoint schemas must all reflect the new structure
10. **Run consistency verification** — grep for old step numbers, old weight values, old file names across ALL files

### Phase 4: Audit
11. **Run a full audit** using `references/skill-audit-checklist.md` — structural changes almost always introduce inconsistencies
12. **Batch-fix all issues** — collect all fixes, then apply as sequential `skill_manage(action='patch')` calls
13. **Final verification** — grep for residual old values across all files, verify weight totals sum to 100%

**Key pitfall**: After merging, the SKILL.md, checkpoint schema, report template, and pre-analysis script often have mismatched step numbers or weights because each was updated independently. Always verify all 4 files match at the end. It covers 14 categories of issues including: logical conflicts, step ordering, absolute thresholds, missing data sources, vague thresholds, orphaned sections, self-check mapping, template/flow disconnect, description triggering, terminology gaps, absolute/relative threshold contradictions, residual language after repositioning, threshold calibration metadata, and **template file integrity** (line number prefix corruption from `read_file` output).

**For deeper optimization** (user says "全量优化", "深度审计", "研究这个skill有没有优化空间"), also load `references/skill-optimization-methodology.md`. It covers 7 additional issue categories beyond the audit checklist: content duplication, invalid references, cross-file consistency, scattered guidance, vague standards, tool usability, and verbose delivery paths.

**Start with the Audit Workflow** at the bottom of the checklist — it's a quick grep-based structural pass that catches the most common issues before you go category by category. Key pattern: if the skill has been repositioned, grep for old-positioning keywords FIRST (Category 12), then check templates against current positioning (Category 12b). These are the hardest issues to spot by reading alone.

**Batch fix pattern**: When the audit finds 5+ issues, fix them as a series of `skill_manage(action='patch')` calls, each targeting one category. Order: fix logical conflicts first (they affect other fixes), then thresholds/definitions, then cosmetic issues (version bump, changelog). After all patches, verify the result with `skill_view` — look for broken table alignment, orphaned headers, or content that accidentally got duplicated.

**Large skill structural surgery pitfalls** (learned from jw-company-analysis multi-round audit):

1. **"Catch-all section" anti-pattern**: When a skill accumulates content over many rounds (e.g., 10+ book research iterations), one section often becomes a dumping ground for references that don't fit elsewhere. In jw-company-analysis, Step 5 (逆向检查) accumulated 60+ macro/cycle/monetary references that belonged in a separate macro context section. **Detection**: grep for the section with the most § references — if it has 3x more than any other section, it's likely a catch-all. **Fix**: Create a new dedicated section (e.g., "Step 0.5 宏观环境评估"), move references by theme (not one-by-one), add output format and execution guidance so the new section has a clear purpose.

2. **Cross-file Step renumbering cascade** (learned from jw-company-analysis v4.1.0→v4.1.3): When SKILL.md undergoes section renumbering (e.g., merging Step 2 into Step 1, shifting all subsequent numbers), the rubric files, calibration files, checkpoint-schema, and report template ALL retain the old numbering. **Detection**: After any renumbering, grep for old step numbers across ALL files in the skill directory, not just SKILL.md. **Fix**: Use sed with temporary placeholders to avoid cascading replacements (e.g., replace 4→TEMP_A, 5→TEMP_B, then TEMP_A→5, TEMP_B→6). Always verify with `grep -oP 'Step \d+'` across all files afterward. **Key pattern**: rubric files use section headers like `## 2.1 市场空间` which don't match `Step N` grep patterns — you must also grep for `^## [0-9]` to catch these.

3. **Multi-round audit diminishing returns**: After 3+ audit rounds on the same skill, each round catches progressively subtler issues. Round 1 catches structural problems (50%+ line reduction). Round 2 catches numbering/formatting inconsistencies. Round 3 catches cross-file drift. Round 4 catches orphaned references and version sync. **When to stop**: when grep-based consistency checks return zero hits across all files.

2. **read_file line number prefix corruption**: `read_file` returns content with `NUM|content` prefixes. If you `write_file` this back directly, the prefixes become permanent file content. **Detection**: `head -5 file.md` shows lines starting with numbers and pipes. **Fix**: `python3 -c "import re; content=open(f).read(); open(f,'w').write(re.sub(r'^(\d+)\|','',content,flags=re.MULTILINE))"`. Always verify with `head -5` after.

3. **Parallel delegate_task duplicate writes**: When multiple subagents append to the same file, they may each write the same block if they read the file at the same time (before either write landed). **Detection**: `grep -c "specific phrase" file` returns 2+. **Fix**: Use `patch(mode='replace')` with sufficient unique context to match only one instance. If the content appears 3+ times, strip line number prefixes first (pitfall #2), then the patch tool can match uniquely.

4. **📚引用膨胀 anti-pattern**: After 10+ rounds of book research, a skill accumulates 80+ `📚 详见 references/investment-theory.md §XX` lines, each carrying the full file path. This wastes 30+ characters per line and pushes SKILL.md over the 1000-line limit. **Detection**: `grep -c '📚.*详见.*references/' SKILL.md` returns 50+. **Fix**: Define path shorthand once (`📚§XX=investment-theory.md`), replace all occurrences with shorthand, then merge adjacent 📚 lines per sub-step into one consolidated reference line. See `references/skill-compression-techniques.md` for the full procedure.

**Post-refactoring template sync** (MANDATORY for skills with templates): After any major SKILL.md refactoring (>20% line change), execute template sync checks. See `references/investment-skill-template-drift.md` for the full checklist. Key items: scoring ranges, checklist counts, verification item counts, version number 10-location sync (SKILL.md frontmatter + title, template title + version field, checkpoint-schema title + JSON example, each rubric file frontmatter, calibration file frontmatter, maintenance-guide version reference). **Rubric/calibration files are the most commonly forgotten sync targets** — they have YAML frontmatter version fields that drift silently. After Step renumbering, also scan background theory files (investment-theory.md, macro-context.md, etc.) for old Step references — `grep -rn 'Step [0-9]' references/` catches these.

**Template conclusion matrix drift** (learned from jw-company-analysis v3.27.0→v3.28.0): Templates can accumulate extra rows over incremental edits (e.g., 6-row matrix in template vs 4-row matrix in SKILL.md). Always grep for the conclusion matrix in both SKILL.md and templates/ and verify row count matches. If they diverge, SKILL.md is the source of truth.

## Communicating with the user

The skill creator is liable to be used by people across a wide range of familiarity with coding jargon. If you haven't heard (and how could you, it's only very recently that it started), there's a trend now where the power of Claude is inspiring plumbers to open up their terminals, parents and grandparents to google "how to install npm". On the other hand, the bulk of users are probably fairly computer-literate.

So please pay attention to context cues to understand how to phrase your communication! In the default case, just to give you some idea:

- "evaluation" and "benchmark" are borderline, but OK
- for "JSON" and "assertion" you want to see serious cues from the user that they know what those things are before using them without explaining them

It's OK to briefly explain terms if you're in doubt, and feel free to clarify terms with a short definition if you're unsure if the user will understand them.

---

## Creating a skill

### Capture Intent

Start by understanding the user's intent. The current conversation might already contain a workflow the user wants to capture (e.g., they say "turn this into a skill"). If so, extract answers from the conversation history first — the tools used, the sequence of steps, corrections the user made, input/output formats observed. The user may need to fill the gaps, and should confirm before proceeding to the next step.

1. What should this skill enable Claude to do?
2. When should this skill trigger? (what user phrases/contexts)
3. What's the expected output format?
4. Should we set up test cases to verify the skill works? Skills with objectively verifiable outputs (file transforms, data extraction, code generation, fixed workflow steps) benefit from test cases. Skills with subjective outputs (writing style, art) often don't need them. Suggest the appropriate default based on the skill type, but let the user decide.

### Interview and Research

Proactively ask questions about edge cases, input/output formats, example files, success criteria, and dependencies. Wait to write test prompts until you've got this part ironed out.

Check available MCPs - if useful for research (searching docs, finding similar skills, looking up best practices), research in parallel via subagents if available, otherwise inline. Come prepared with context to reduce burden on the user.

### Write the SKILL.md

Based on the user interview, fill in these components:

- **name**: Skill identifier
- **description**: When to trigger, what it does. This is the primary triggering mechanism - include both what the skill does AND specific contexts for when to use it. All "when to use" info goes here, not in the body. Note: currently Claude has a tendency to "undertrigger" skills -- to not use them when they'd be useful. To combat this, please make the skill descriptions a little bit "pushy". So for instance, instead of "How to build a simple fast dashboard to display internal Anthropic data.", you might write "How to build a simple fast dashboard to display internal Anthropic data. Make sure to use this skill whenever the user mentions dashboards, data visualization, internal metrics, or wants to display any kind of company data, even if they don't explicitly ask for a 'dashboard.'"
- **compatibility**: Required tools, dependencies (optional, rarely needed)
- **the rest of the skill :)**

### Skill Writing Guide

#### Anatomy of a Skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description required)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/    - Executable code for deterministic/repetitive tasks
    ├── references/ - Docs loaded into context as needed
    └── assets/     - Files used in output (templates, icons, fonts)
```

#### Progressive Disclosure

Skills use a three-level loading system:
1. **Metadata** (name + description) - Always in context (~100 words)
2. **SKILL.md body** - In context whenever skill triggers (<500 lines ideal)
3. **Bundled resources** - As needed (unlimited, scripts can execute without loading)

These word counts are approximate and you can feel free to go longer if needed.

**Key patterns:**
- Keep SKILL.md under 500 lines; if you're approaching this limit, add an additional layer of hierarchy along with clear pointers about where the model using the skill should go next to follow up.
- Reference files clearly from SKILL.md with guidance on when to read them
- For large reference files (>300 lines), include a table of contents

**Domain organization**: When a skill supports multiple domains/frameworks, organize by variant:
```
cloud-deploy/
├── SKILL.md (workflow + selection)
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```
Claude reads only the relevant reference file.

#### Principle of Lack of Surprise

This goes without saying, but skills must not contain malware, exploit code, or any content that could compromise system security. A skill's contents should not surprise the user in their intent if described. Don't go along with requests to create misleading skills or skills designed to facilitate unauthorized access, data exfiltration, or other malicious activities. Things like a "roleplay as an XYZ" are OK though.

#### Writing Patterns

Prefer using the imperative form in instructions.

**Defining output formats** - You can do it like this:
```markdown
## Report structure
ALWAYS use this exact template:
# [Title]
## Executive summary
## Key findings
## Recommendations
```

**Examples pattern** - It's useful to include examples. You can format them like this (but if "Input" and "Output" are in the examples you might want to deviate a little):
```markdown
## Commit message format
**Example 1:**
Input: Added user authentication with JWT tokens
Output: feat(auth): implement JWT-based authentication
```

### Writing Style

Try to explain to the model why things are important in lieu of heavy-handed musty MUSTs. Use theory of mind and try to make the skill general and not super-narrow to specific examples. Start by writing a draft and then look at it with fresh eyes and improve it.

### Pitfall: Step Renumbering Cascading Drift

When a skill's step numbering is changed (e.g., Step 0-11 → Step 1-14 with skipped numbers), ALL dependent files must be updated — not just SKILL.md. In a jw-company-analysis audit, 31+ template step references, checkpoint-schema comments, scoring rubric sub-dimension numbers, and calibration file references were all pointing to old numbers after SKILL.md was renumbered.

**Key detection**: compare `grep -oP 'Step \d+' SKILL.md | sort -u` against the same in templates/, checkpoint-schema, and rubric files. Any mismatch means drift.

**Key fix**: use Python with temp placeholders (Step 3 → TEMP_6 → Step 6) to avoid cascading replacements (sed Step 3→6 then Step 6→9 corrupts the second replacement). Check both section headers (`## 2.1` → `## 5.1`) and inline references.

**Files to sync after renumbering**: templates, checkpoint-schema, scoring-rubric-*.md, special-entities-calibration.md, maintenance-guide.md, **background theory files** (investment-theory.md, macro-context.md, china-value-investing.md — these contain `Step N` references that point to old numbers). See `references/investment-skill-template-drift.md` patterns 13 and 16. Full detection: `grep -rn 'Step [0-9]' references/` after renumbering.

### Pitfall: 重写 SKILL.md 引入重复内容

**案例**：jw-hv-analysis 全量优化时，"质检清单"出现了两次（第五步内一次 + 文件末尾一次），还引用了不存在的 `references/schema.json`。用户重复提问同一问题 = 优化本身有问题。

### Pitfall: Deep book research requires parallel batching

When enriching a skill with knowledge from multiple books (5+), use delegate_task with batch mode:
- Max 2 parallel tasks per batch (3 risks HTTP 429 from concurrent large file reads)
- Each subagent should read 2-5 files max, not the entire library
- Structure: "Read books X,Y → extract quantitative content → write reference file"
- Failed batches (429) can be retried individually after other batches complete
- Always check existing references first to avoid redundant work

### Pitfall: skill_manage patch requires exact name

`skill_manage(action='patch', name='partial-name')` fails silently. Always use `skills_list()` to get the exact skill name before patching.

### Pitfall: patch mode with Unicode/emoji content

When using `skill_manage(action='patch')` on files containing emoji or CJK characters, the `old_string` must match EXACTLY — including whitespace and Unicode characters. If a patch fails with "hunk not found" on a line containing emoji (🔴, ✅, ⭐, etc.), the issue is likely character encoding mismatch between the old_string and the actual file content. **Fix**: use `read_file` to get the exact line, then copy the exact text (including emoji) into old_string. Do NOT approximate or substitute similar-looking characters.

**防护措施**：
1. 重写 SKILL.md 后，必须全文扫描确认无重复章节
2. 引用任何文件（references/、scripts/）前，确认文件存在
3. 质检脚本的检查项必须与 SKILL.md 指令严格对齐
4. 优化完成后用 `skill_view` 自查一遍完整内容

### Self-Audit After Creation (Recommended)

After writing the SKILL.md and all support files, **immediately audit the skill before delivering to the user**. This catches issues while context is fresh — far cheaper than having the user find them later.

**Process**:
1. **Check template integrity first** (Category 14): `head -5 templates/*.md` — fix any `N|` prefix corruption before proceeding
2. Load `references/skill-audit-checklist.md` and run through all 14 categories systematically
3. Focus on the most common first-draft issues: logical conflicts (category 1), absolute thresholds without industry context (3), missing data sources (4), vague thresholds (5), terminology gaps (10)
4. Fix all high-severity issues before delivering the first version
5. Bump version and add changelog entry for the fixes

**Why this matters**: In practice, newly created skills almost always have audit issues — weight contradictions between sections, undefined technical terms, hardcoded thresholds without industry context, orphaned code blocks that belong in references/. Catching these in a self-audit takes minutes; having the user discover them in a follow-up session wastes a full round-trip.

**Batch patching technique**: When a self-audit reveals 5+ issues, use sequential `skill_manage(action='patch')` calls to fix them one category at a time. Each patch should target a unique `old_string` to avoid ambiguity. After all patches, verify with `skill_view` that the file is coherent (no orphaned headers, no broken table alignment, version bumped).

### Test Cases

After writing the skill draft, come up with 2-3 realistic test prompts — the kind of thing a real user would actually say. Share them with the user: [you don't have to use this exact language] "Here are a few test cases I'd like to try. Do these look right, or do you want to add more?" Then run them.

Save test cases to `evals/evals.json`. Don't write assertions yet — just the prompts. You'll draft assertions in the next step while the runs are in progress.

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's task prompt",
      "expected_output": "Description of expected result",
      "files": []
    }
  ]
}
```

See `references/schemas.md` for the full schema (including the `assertions` field, which you'll add later).

## Running and evaluating test cases

This section is one continuous sequence — don't stop partway through. Do NOT use `/skill-test` or any other testing skill.

Put results in `<skill-name>-workspace/` as a sibling to the skill directory. Within the workspace, organize results by iteration (`iteration-1/`, `iteration-2/`, etc.) and within that, each test case gets a directory (`eval-0/`, `eval-1/`, etc.). Don't create all of this upfront — just create directories as you go.

### Step 1: Spawn all runs (with-skill AND baseline) in the same turn

For each test case, spawn two subagents in the same turn — one with the skill, one without. This is important: don't spawn the with-skill runs first and then come back for baselines later. Launch everything at once so it all finishes around the same time.

**With-skill run:**

```
Execute this task:
- Skill path: <path-to-skill>
- Task: <eval prompt>
- Input files: <eval files if any, or "none">
- Save outputs to: <workspace>/iteration-<N>/eval-<ID>/with_skill/outputs/
- Outputs to save: <what the user cares about — e.g., "the .docx file", "the final CSV">
```

**Baseline run** (same prompt, but the baseline depends on context):
- **Creating a new skill**: no skill at all. Same prompt, no skill path, save to `without_skill/outputs/`.
- **Improving an existing skill**: the old version. Before editing, snapshot the skill (`cp -r <skill-path> <workspace>/skill-snapshot/`), then point the baseline subagent at the snapshot. Save to `old_skill/outputs/`.

Write an `eval_metadata.json` for each test case (assertions can be empty for now). Give each eval a descriptive name based on what it's testing — not just "eval-0". Use this name for the directory too. If this iteration uses new or modified eval prompts, create these files for each new eval directory — don't assume they carry over from previous iterations.

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name-here",
  "prompt": "The user's task prompt",
  "assertions": []
}
```

### Step 2: While runs are in progress, draft assertions

Don't just wait for the runs to finish — you can use this time productively. Draft quantitative assertions for each test case and explain them to the user. If assertions already exist in `evals/evals.json`, review them and explain what they check.

Good assertions are objectively verifiable and have descriptive names — they should read clearly in the benchmark viewer so someone glancing at the results immediately understands what each one checks. Subjective skills (writing style, design quality) are better evaluated qualitatively — don't force assertions onto things that need human judgment.

Update the `eval_metadata.json` files and `evals/evals.json` with the assertions once drafted. Also explain to the user what they'll see in the viewer — both the qualitative outputs and the quantitative benchmark.

### Step 3: As runs complete, capture timing data

When each subagent task completes, you receive a notification containing `total_tokens` and `duration_ms`. Save this data immediately to `timing.json` in the run directory:

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

This is the only opportunity to capture this data — it comes through the task notification and isn't persisted elsewhere. Process each notification as it arrives rather than trying to batch them.

### Step 4: Grade, aggregate, and launch the viewer

Once all runs are done:

1. **Grade each run** — spawn a grader subagent (or grade inline) that reads `agents/grader.md` and evaluates each assertion against the outputs. Save results to `grading.json` in each run directory. The grading.json expectations array must use the fields `text`, `passed`, and `evidence` (not `name`/`met`/`details` or other variants) — the viewer depends on these exact field names. For assertions that can be checked programmatically, write and run a script rather than eyeballing it — scripts are faster, more reliable, and can be reused across iterations.

2. **Aggregate into benchmark** — run the aggregation script from the skill-creator directory:
   ```bash
   python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
   ```
   This produces `benchmark.json` and `benchmark.md` with pass_rate, time, and tokens for each configuration, with mean ± stddev and the delta. If generating benchmark.json manually, see `references/schemas.md` for the exact schema the viewer expects.
Put each with_skill version before its baseline counterpart.

3. **Do an analyst pass** — read the benchmark data and surface patterns the aggregate stats might hide. See `agents/analyzer.md` (the "Analyzing Benchmark Results" section) for what to look for — things like assertions that always pass regardless of skill (non-discriminating), high-variance evals (possibly flaky), and time/token tradeoffs.

4. **Launch the viewer** with both qualitative outputs and quantitative data:
   ```bash
   nohup python <skill-creator-path>/eval-viewer/generate_review.py \
     <workspace>/iteration-N \
     --skill-name "my-skill" \
     --benchmark <workspace>/iteration-N/benchmark.json \
     > /dev/null 2>&1 &
   VIEWER_PID=$!
   ```
   For iteration 2+, also pass `--previous-workspace <workspace>/iteration-<N-1>`.

   **Cowork / headless environments:** If `webbrowser.open()` is not available or the environment has no display, use `--static <output_path>` to write a standalone HTML file instead of starting a server. Feedback will be downloaded as a `feedback.json` file when the user clicks "Submit All Reviews". After download, copy `feedback.json` into the workspace directory for the next iteration to pick up.

Note: please use generate_review.py to create the viewer; there's no need to write custom HTML.

5. **Tell the user** something like: "I've opened the results in your browser. There are two tabs — 'Outputs' lets you click through each test case and leave feedback, 'Benchmark' shows the quantitative comparison. When you're done, come back here and let me know."

### What the user sees in the viewer

The "Outputs" tab shows one test case at a time:
- **Prompt**: the task that was given
- **Output**: the files the skill produced, rendered inline where possible
- **Previous Output** (iteration 2+): collapsed section showing last iteration's output
- **Formal Grades** (if grading was run): collapsed section showing assertion pass/fail
- **Feedback**: a textbox that auto-saves as they type
- **Previous Feedback** (iteration 2+): their comments from last time, shown below the textbox

The "Benchmark" tab shows the stats summary: pass rates, timing, and token usage for each configuration, with per-eval breakdowns and analyst observations.

Navigation is via prev/next buttons or arrow keys. When done, they click "Submit All Reviews" which saves all feedback to `feedback.json`.

### Step 5: Read the feedback

When the user tells you they're done, read `feedback.json`:

```json
{
  "reviews": [
    {"run_id": "eval-0-with_skill", "feedback": "the chart is missing axis labels", "timestamp": "..."},
    {"run_id": "eval-1-with_skill", "feedback": "", "timestamp": "..."},
    {"run_id": "eval-2-with_skill", "feedback": "perfect, love this", "timestamp": "..."}
  ],
  "status": "complete"
}
```

Empty feedback means the user thought it was fine. Focus your improvements on the test cases where the user had specific complaints.

Kill the viewer server when you're done with it:

```bash
kill $VIEWER_PID 2>/dev/null
```

---

## Improving the skill

This is the heart of the loop. You've run the test cases, the user has reviewed the results, and now you need to make the skill better based on their feedback.

### How to think about improvements

1. **Generalize from the feedback.** The big picture thing that's happening here is that we're trying to create skills that can be used a million times (maybe literally, maybe even more who knows) across many different prompts. Here you and the user are iterating on only a few examples over and over again because it helps move faster. The user knows these examples in and out and it's quick for them to assess new outputs. But if the skill you and the user are codeveloping works only for those examples, it's useless. Rather than put in fiddly overfitty changes, or oppressively constrictive MUSTs, if there's some stubborn issue, you might try branching out and using different metaphors, or recommending different patterns of working. It's relatively cheap to try and maybe you'll land on something great.

2. **Keep the prompt lean.** Remove things that aren't pulling their weight. Make sure to read the transcripts, not just the final outputs — if it looks like the skill is making the model waste a bunch of time doing things that are unproductive, you can try getting rid of the parts of the skill that are making it do that and seeing what happens.

3. **Explain the why.** Try hard to explain the **why** behind everything you're asking the model to do. Today's LLMs are *smart*. They have good theory of mind and when given a good harness can go beyond rote instructions and really make things happen. Even if the feedback from the user is terse or frustrated, try to actually understand the task and why the user is writing what they wrote, and what they actually wrote, and then transmit this understanding into the instructions. If you find yourself writing ALWAYS or NEVER in all caps, or using super rigid structures, that's a yellow flag — if possible, reframe and explain the reasoning so that the model understands why the thing you're asking for is important. That's a more humane, powerful, and effective approach.

4. **Look for repeated work across test cases.** Read the transcripts from the test runs and notice if the subagents all independently wrote similar helper scripts or took the same multi-step approach to something. If all 3 test cases resulted in the subagent writing a `create_docx.py` or a `build_chart.py`, that's a strong signal the skill should bundle that script. Write it once, put it in `scripts/`, and tell the skill to use it. This saves every future invocation from reinventing the wheel.

This task is pretty important (we are trying to create billions a year in economic value here!) and your thinking time is not the blocker; take your time and really mull things over. I'd suggest writing a draft revision and then looking at it anew and making improvements. Really do your best to get into the head of the user and understand what they want and need.

### The iteration loop

After improving the skill:

1. Apply your improvements to the skill
2. Rerun all test cases into a new `iteration-<N+1>/` directory, including baseline runs. If you're creating a new skill, the baseline is always `without_skill` (no skill) — that stays the same across iterations. If you're improving an existing skill, use your judgment on what makes sense as the baseline: the original version the user came in with, or the previous iteration.
3. Launch the reviewer with `--previous-workspace` pointing at the previous iteration
4. Wait for the user to review and tell you they're done
5. Read the new feedback, improve again, repeat

Keep going until:
- The user says they're happy
- The feedback is all empty (everything looks good)
- You're not making meaningful progress

---

## Advanced: Blind comparison

For situations where you want a more rigorous comparison between two versions of a skill (e.g., the user asks "is the new version actually better?"), there's a blind comparison system. Read `agents/comparator.md` and `agents/analyzer.md` for the details. The basic idea is: give two outputs to an independent agent without telling it which is which, and let it judge quality. Then analyze why the winner won.

This is optional, requires subagents, and most users won't need it. The human review loop is usually sufficient.

---

## Description Optimization

The description field in SKILL.md frontmatter is the primary mechanism that determines whether Claude invokes a skill. After creating or improving a skill, offer to optimize the description for better triggering accuracy.

### Step 1: Generate trigger eval queries

Create 20 eval queries — a mix of should-trigger and should-not-trigger. Save as JSON:

```json
[
  {"query": "the user prompt", "should_trigger": true},
  {"query": "another prompt", "should_trigger": false}
]
```

The queries must be realistic and something a Claude Code or Claude.ai user would actually type. Not abstract requests, but requests that are concrete and specific and have a good amount of detail. For instance, file paths, personal context about the user's job or situation, column names and values, company names, URLs. A little bit of backstory. Some might be in lowercase or contain abbreviations or typos or casual speech. Use a mix of different lengths, and focus on edge cases rather than making them clear-cut (the user will get a chance to sign off on them).

Bad: `"Format this data"`, `"Extract text from PDF"`, `"Create a chart"`

Good: `"ok so my boss just sent me this xlsx file (its in my downloads, called something like 'Q4 sales final FINAL v2.xlsx') and she wants me to add a column that shows the profit margin as a percentage. The revenue is in column C and costs are in column D i think"`

For the **should-trigger** queries (8-10), think about coverage. You want different phrasings of the same intent — some formal, some casual. Include cases where the user doesn't explicitly name the skill or file type but clearly needs it. Throw in some uncommon use cases and cases where this skill competes with another but should win.

For the **should-not-trigger** queries (8-10), the most valuable ones are the near-misses — queries that share keywords or concepts with the skill but actually need something different. Think adjacent domains, ambiguous phrasing where a naive keyword match would trigger but shouldn't, and cases where the query touches on something the skill does but in a context where another tool is more appropriate.

The key thing to avoid: don't make should-not-trigger queries obviously irrelevant. "Write a fibonacci function" as a negative test for a PDF skill is too easy — it doesn't test anything. The negative cases should be genuinely tricky.

### Step 2: Review with user

Present the eval set to the user for review using the HTML template:

1. Read the template from `assets/eval_review.html`
2. Replace the placeholders:
   - `__EVAL_DATA_PLACEHOLDER__` → the JSON array of eval items (no quotes around it — it's a JS variable assignment)
   - `__SKILL_NAME_PLACEHOLDER__` → the skill's name
   - `__SKILL_DESCRIPTION_PLACEHOLDER__` → the skill's current description
3. Write to a temp file (e.g., `/tmp/eval_review_<skill-name>.html`) and open it: `open /tmp/eval_review_<skill-name>.html`
4. The user can edit queries, toggle should-trigger, add/remove entries, then click "Export Eval Set"
5. The file downloads to `~/Downloads/eval_set.json` — check the Downloads folder for the most recent version in case there are multiple (e.g., `eval_set (1).json`)

This step matters — bad eval queries lead to bad descriptions.

### Step 3: Run the optimization loop

Tell the user: "This will take some time — I'll run the optimization loop in the background and check on it periodically."

Save the eval set to the workspace, then run in the background:

```bash
python -m scripts.run_loop \
  --eval-set <path-to-trigger-eval.json> \
  --skill-path <path-to-skill> \
  --model <model-id-powering-this-session> \
  --max-iterations 5 \
  --verbose
```

Use the model ID from your system prompt (the one powering the current session) so the triggering test matches what the user actually experiences.

While it runs, periodically tail the output to give the user updates on which iteration it's on and what the scores look like.

This handles the full optimization loop automatically. It splits the eval set into 60% train and 40% held-out test, evaluates the current description (running each query 3 times to get a reliable trigger rate), then calls Claude to propose improvements based on what failed. It re-evaluates each new description on both train and test, iterating up to 5 times. When it's done, it opens an HTML report in the browser showing the results per iteration and returns JSON with `best_description` — selected by test score rather than train score to avoid overfitting.

### How skill triggering works

Understanding the triggering mechanism helps design better eval queries. Skills appear in Claude's `available_skills` list with their name + description, and Claude decides whether to consult a skill based on that description. The important thing to know is that Claude only consults skills for tasks it can't easily handle on its own — simple, one-step queries like "read this PDF" may not trigger a skill even if the description matches perfectly, because Claude can handle them directly with basic tools. Complex, multi-step, or specialized queries reliably trigger skills when the description matches.

This means your eval queries should be substantive enough that Claude would actually benefit from consulting a skill. Simple queries like "read file X" are poor test cases — they won't trigger skills regardless of description quality.

### Step 4: Apply the result

Take `best_description` from the JSON output and update the skill's SKILL.md frontmatter. Show the user before/after and report the scores.

---

### Package and Present (only if `present_files` tool is available)

Check whether you have access to the `present_files` tool. If you don't, skip this step. If you do, package the skill and present the .skill file to the user:

```bash
python -m scripts.package_skill <path/to/skill-folder>
```

After packaging, direct the user to the resulting `.skill` file path so they can install it.

---

## Claude.ai-specific instructions

In Claude.ai, the core workflow is the same (draft → test → review → improve → repeat), but because Claude.ai doesn't have subagents, some mechanics change. Here's what to adapt:

**Running test cases**: No subagents means no parallel execution. For each test case, read the skill's SKILL.md, then follow its instructions to accomplish the test prompt yourself. Do them one at a time. This is less rigorous than independent subagents (you wrote the skill and you're also running it, so you have full context), but it's a useful sanity check — and the human review step compensates. Skip the baseline runs — just use the skill to complete the task as requested.

**Reviewing results**: If you can't open a browser (e.g., Claude.ai's VM has no display, or you're on a remote server), skip the browser reviewer entirely. Instead, present results directly in the conversation. For each test case, show the prompt and the output. If the output is a file the user needs to see (like a .docx or .xlsx), save it to the filesystem and tell them where it is so they can download and inspect it. Ask for feedback inline: "How does this look? Anything you'd change?"

**Benchmarking**: Skip the quantitative benchmarking — it relies on baseline comparisons which aren't meaningful without subagents. Focus on qualitative feedback from the user.

**The iteration loop**: Same as before — improve the skill, rerun the test cases, ask for feedback — just without the browser reviewer in the middle. You can still organize results into iteration directories on the filesystem if you have one.

**Description optimization**: This section requires the `claude` CLI tool (specifically `claude -p`) which is only available in Claude Code. Skip it if you're on Claude.ai.

**Blind comparison**: Requires subagents. Skip it.

**Packaging**: The `package_skill.py` script works anywhere with Python and a filesystem. On Claude.ai, you can run it and the user can download the resulting `.skill` file.

**Updating an existing skill**: The user might be asking you to update an existing skill, not create a new one. In this case:
- **Preserve the original name.** Note the skill's directory name and `name` frontmatter field -- use them unchanged. E.g., if the installed skill is `research-helper`, output `research-helper.skill` (not `research-helper-v2`).
- **Copy to a writeable location before editing.** The installed skill path may be read-only. Copy to `/tmp/skill-name/`, edit there, and package from the copy.
- **If packaging manually, stage in `/tmp/` first**, then copy to the output directory -- direct writes may fail due to permissions.

---

## Cowork-Specific Instructions

If you're in Cowork, the main things to know are:

- You have subagents, so the main workflow (spawn test cases in parallel, run baselines, grade, etc.) all works. (However, if you run into severe problems with timeouts, it's OK to run the test prompts in series rather than parallel.)
- You don't have a browser or display, so when generating the eval viewer, use `--static <output_path>` to write a standalone HTML file instead of starting a server. Then proffer a link that the user can click to open the HTML in their browser.
- For whatever reason, the Cowork setup seems to disincline Claude from generating the eval viewer after running the tests, so just to reiterate: whether you're in Cowork or in Claude Code, after running tests, you should always generate the eval viewer for the human to look at examples before revising the skill yourself and trying to make corrections, using `generate_review.py` (not writing your own boutique html code). Sorry in advance but I'm gonna go all caps here: GENERATE THE EVAL VIEWER *BEFORE* evaluating inputs yourself. You want to get them in front of the human ASAP!
- Feedback works differently: since there's no running server, the viewer's "Submit All Reviews" button will download `feedback.json` as a file. You can then read it from there (you may have to request access first).
- Packaging works — `package_skill.py` just needs Python and a filesystem.
- Description optimization (`run_loop.py` / `run_eval.py`) should work in Cowork just fine since it uses `claude -p` via subprocess, not a browser, but please save it until you've fully finished making the skill and the user agrees it's in good shape.
- **Updating an existing skill**: The user might be asking you to update an existing skill, not create a new one. Follow the update guidance in the claude.ai section above.

---

## Reference files

The agents/ directory contains instructions for specialized subagents. Read them when you need to spawn the relevant subagent.

- `agents/grader.md` — How to evaluate assertions against outputs
- `agents/comparator.md` — How to do blind A/B comparison between two outputs
- `agents/analyzer.md` — How to analyze why one version beat another

The references/ directory has additional documentation:
- `references/schemas.md` — JSON structures for evals.json, grading.json, etc.
- `references/skill-audit-checklist.md` — Systematic checklist for auditing existing skills (logical conflicts, missing data, step ordering, threshold issues)
- `references/skill-maintenance-patterns.md` — Changelog deduplication, token optimization, version table hygiene, orphaned feature references.
- `references/skill-translation.md` — Workflow and pitfalls for translating existing skills to another language. Covers: parallel delegation strategy, truncation detection, path consistency, CJK support, cross-file name consistency, external dependency installation. Consult when user asks to translate/localize a skill.
- `references/investment-skill-audit-patterns.md` — Common issues when auditing investment/financial analysis skills: absolute thresholds without industry context, missing terminology, template drift, qualitative assessments lacking quantitative anchors, version drift between SKILL.md and templates, vague quantified descriptions (e.g. "持续增长" without numeric anchors). Use as a supplement to skill-audit-checklist.md for domain-specific checks.
- `references/cross-file-renumbering-cascade.md` — Cross-file step renumbering: when SKILL.md renumbers steps, rubric/calibration/checkpoint files must also be updated. Detection patterns and temporary-placeholder sed technique.
- `references/investment-skill-template-drift.md` — Template drift patterns after investment skill refactoring: scoring range mismatches, checklist desync, verification item divergence, version number drift across 4 locations. Use after any major SKILL.md refactoring that includes a report template.
- `references/investment-skill-formula-consistency.md` — Formula consistency audit patterns: sub-dimension score vs total formula mismatches, template-vs-SKILL.md logic drift, conclusion matrix format drift, section header inconsistencies, absolute threshold calibration gaps.
- `references/agent-execution-feasibility-audit.md` — Agent execution feasibility patterns: reference classification for large files, exclusion checkpoint standardization, scoring math validation, pre-execution script default score labeling, template auto-fill. Use in Round 4+ audits when user asks "can this actually be executed by an agent?"
- `references/iterative-book-study-integration.md` — Workflow for enriching a skill by systematically studying reference books in multiple rounds. Covers: research→proposal→parallel execution→verification cycle, diminishing returns detection, parallel delegation strategy for SKILL.md + references, proposal template. Use when user asks to study a book/document to supplement an existing skill.
- `references/python-pitfalls.md` — Common Python issues when writing skill scripts: encoding declarations for Chinese characters, Path + string concatenation errors, type annotation compatibility. Consult when creating or debugging Python scripts in skills.
- `references/skill-optimization-methodology.md` — Systematic methodology for post-creation skill optimization: 7 issue categories (content duplication, invalid references, cross-file consistency, scattered guidance, vague standards, tool usability, verbose delivery), prioritization, execution order, verification checklist. Use when user says "全量优化" or asks to audit/optimize an existing skill.
- `references/upstream-version-check.md` — Workflow for checking if a skill has upstream updates on GitHub (identify source → compare structure → checksum files → diff → report)
- `references/skill-compression-techniques.md` — Four techniques for compressing large SKILL.md files (📚reference shorthand, sub-step merging, extension-line deletion, reference-block consolidation). Use when SKILL.md exceeds 1000-line soft limit and needs to shrink without losing execution functionality.

---

Repeating one more time the core loop here for emphasis:

- Figure out what the skill is about
- Draft or edit the skill
- Run claude-with-access-to-the-skill on test prompts
- With the user, evaluate the outputs:
  - Create benchmark.json and run `eval-viewer/generate_review.py` to help the user review them
  - Run quantitative evals
- Repeat until you and the user are satisfied
- Package the final skill and return it to the user.

Please add steps to your TodoList, if you have such a thing, to make sure you don't forget. If you're in Cowork, please specifically put "Create evals JSON and run `eval-viewer/generate_review.py` so human can review test cases" in your TodoList to make sure it happens.

Good luck!

[Skill directory: /root/.hermes/skills/skill-creator]
Resolve any relative paths in this skill (e.g. `scripts/foo.js`, `templates/config.yaml`) against that directory, then run them with the absolute tool using the absolute path.

[This skill has supporting files:]
- references/eval-driven-improvement.md  ->  /root/.hermes/skills/skill-creator/references/eval-driven-improvement.md
- references/analytical-framework-design.md  ->  /root/.hermes/skills/skill-creator/references/analytical-framework-design.md
- references/philosophy-distillation.md  ->  /root/.hermes/skills/skill-creator/references/philosophy-distillation.md
- references/schemas.md  ->  /root/.hermes/skills/skill-creator/references/schemas.md
- references/skill-audit-checklist.md  ->  /root/.hermes/skills/skill-creator/references/skill-audit-checklist.md
- references/investment-skill-audit-patterns.md  ->  /root/.hermes/skills/skill-creator/references/investment-skill-audit-patterns.md
- assets/eval_review.html  ->  /root/.hermes/skills/skill-creator/assets/eval_review.html
- scripts/__init__.py  ->  /root/.hermes/skills/skill-creator/scripts/__init__.py
- scripts/aggregate_benchmark.py  ->  /root/.hermes/skills/skill-creator/scripts/aggregate_benchmark.py
- scripts/improve_description.py  ->  /root/.hermes/skills/skill-creator/scripts/improve_description.py
- scripts/utils.py  ->  /root/.hermes/skills/skill-creator/scripts/utils.py
- scripts/quick_validate.py  ->  /root/.hermes/skills/skill-creator/scripts/quick_validate.py
- scripts/generate_report.py  ->  /root/.hermes/skills/skill-creator/scripts/generate_report.py
- scripts/run_loop.py  ->  /root/.hermes/skills/skill-creator/scripts/run_loop.py
- scripts/package_skill.py  ->  /root/.hermes/skills/skill-creator/scripts/package_skill.py
- scripts/run_eval.py  ->  /root/.hermes/skills/skill-creator/scripts/run_eval.py

Load any of these with skill_view(name="skill-creator", file_path="<path>"), or run scripts directly by absolute path (e.g. `node /root/.hermes/skills/skill-creator/scripts/foo.js`).

The user has provided the following instruction alongside the skill invocation: Check this skill for issues
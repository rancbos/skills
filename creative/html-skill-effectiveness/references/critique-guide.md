# Critique Guide

Complete guide for the 5-dimension self-critique system.

## Scoring Bands

| Score | Band | Description |
|-------|------|-------------|
| 0-4 | **Broken** | Fundamental issues that break the experience |
| 5-6 | **Functional** | Works but lacks polish or consistency |
| 7-8 | **Strong** | Competent, polished, intentional |
| 9-10 | **Exceptional** | Memorable, magazine-grade, pushes boundaries |

## 5 Dimensions

### 1. Philosophy Consistency · 哲学一致性

**Definition**: One declared direction, stick to it. No style drift.

**Scoring**:
- **0-4 (Broken)**: Three or more competing styles. User can't identify the aesthetic direction.
- **5-6 (Functional)**: One direction declared but half the elements drift. Inconsistent execution.
- **7-8 (Strong)**: Coherent direction, occasional drift on 1-2 elements.
- **9-10 (Exceptional)**: Every element argues for the same thesis. Unmistakable direction.

**Evidence required**: Cite specific class names, elements, or sections that support or contradict the declared direction.

### 2. Visual Hierarchy · 视觉层级

**Definition**: Can a stranger figure out what to read first, second, third?

**Scoring**:
- **0-4 (Broken)**: Everything shouts. No clear reading order. Competing heroes.
- **5-6 (Functional)**: Hierarchy works on hero but breaks in body. Some sections compete.
- **7-8 (Strong)**: Clear tiers, occasional collision on secondary elements.
- **9-10 (Exceptional)**: Eye moves with zero friction. Obvious what matters.

**Evidence required**: Trace the F-pattern or Z-pattern. Cite specific heading sizes, weights, colors that establish hierarchy.

### 3. Detail Execution · 细节执行

**Definition**: Alignment, leading, kerning, image framing, edge-case spacing. The 90/10 stuff.

**Scoring**:
- **0-4 (Broken)**: Visible tape and string. Misaligned elements, inconsistent spacing, broken images.
- **5-6 (Functional)**: Most pages clean, 1-2 ragged edges. Minor spacing issues.
- **7-8 (Strong)**: Polished, expert eye finds 2-3 misses. Solid craft.
- **9-10 (Exceptional)**: Magazine-grade. Pixel-perfect execution.

**Evidence required**: Cite specific line numbers, class names, or elements where alignment/spacing is off or excellent.

### 4. Functionality · 功能性

**Definition**: Does it WORK? Keyboard nav, click targets, readability, responsive behavior.

**Scoring**:
- **0-4 (Broken)**: Visually fine but doesn't accomplish its job. Broken interactions, unreadable text.
- **5-6 (Functional)**: Core flow works, edge cases broken. Some links don't work.
- **7-8 (Strong)**: Robust through normal use. Handles edge cases well.
- **9-10 (Exceptional)**: Defensively engineered. Graceful degradation, bulletproof.

**Evidence required**: Cite specific interactive elements, test scenarios, or edge cases that pass or fail.

### 5. Innovation · 创新性

**Definition**: One unexpected move that makes people lean in. Not generic AI-median.

**Scoring**:
- **0-4 (Broken)**: Generic AI-slop median. Inter font, purple gradient, stock layout.
- **5-6 (Functional)**: Competent and unmemorable. Gets the job done, won't be shared.
- **7-8 (Strong)**: One memorable moment. A surprise, a delight, a "hey look at this".
- **9-10 (Exceptional)**: Multiple moves you'd steal. Pushes past median decisively.

**Evidence required**: Cite the specific unexpected move(s). What will someone remember?

## Scoring Discipline Rules (Hard Rules)

1. **Always cite evidence** — no "feels off" or vague impressions. Every score must reference specific class names, line numbers, or elements.
2. **Don't average up** — score the WORST sustained band. If Philosophy is 9 but Detail Execution is 4, the overall quality is Broken until fixed.
3. **Don't grade-inflate** — a 7 means STRONG, not "acceptable". A 5 is Functional, not "good enough". Be honest.
4. **Innovation can be low** — 5/10 for production work is fine. Not every artifact needs to be a design award winner. Utility matters.
5. **Separate intent from execution** — a maximalist design that executes poorly scores low on Detail Execution even if Philosophy is bold.

## Output Format: Structured Self-Critique

After scoring, output a structured critique with:

1. **Radar chart mention** (describe the shape, not actual chart)
2. **Band labels** for each dimension
3. **Three action lists**:

```markdown
## Self-Critique Report

### Scores
- Philosophy Consistency: 7/10 (Strong)
- Visual Hierarchy: 6/10 (Functional)
- Detail Execution: 5/10 (Functional)
- Functionality: 8/10 (Strong)
- Innovation: 6/10 (Functional)

### Evidence
[Specific citations for each score]

### Keep (3-5 bullets)
- [What's working, don't break]
- ...

### Fix (3-6 bullets, P0/P1 ordered by visual cost saved per minute)
- [P0: Critical issues that must be fixed before emitting]
- [P1: Should fix for quality]
- ...

### Quick Wins (3-5 bullets, 5-15 minute tweaks with disproportionate impact)
- [Small changes that dramatically improve quality]
- ...
```

## DevLoop: Iterative Refinement

### The Loop

1. **Generate** → first version of the artifact
2. **Critique** → run 5-dimension self-critique, get scores
3. **Check** → if ANY dimension scores < 4 (Broken), iterate
4. **Fix** → each iteration: fix the lowest-scoring dimension first
5. **Re-critique** → score again after fixes
6. **Repeat** → max 3 iterations total

### Escape Hatch

The user can stop the loop at any time:
- Say "good enough" / "stop iterating" / "emit it"
- Or explicitly approve the current version

### Iteration Strategy

**Each iteration should fix the LOWEST-SCORING dimension first**:
- If Philosophy = 3 and Detail = 5, fix Philosophy first (it drags down everything)
- If all dimensions are 5-6, pick the one with the easiest fix that gives biggest visual improvement
- Never iterate on a dimension that already scores 8+

**Max 3 iterations** to prevent infinite loops. If still broken after 3, emit with caveats.

### When to Skip DevLoop

Skip iteration if:
- All dimensions score ≥ 7 (Strong)
- User explicitly says "don't iterate" or "good enough"
- The artifact is a quick draft / prototype (user says "rough", "draft", "quick")

## Critique Report Output Contract

When requested to produce a self-contained HTML critique report:

### Structure

1. **Radar chart** (inline SVG, 5 axes matching the 5 dimensions)
2. **5 dimension cards** with scores + evidence citations
3. **Keep / Fix / Quick-wins action lists** (structured, prioritized)
4. **Before/after comparison** (if in DevLoop, show iteration diffs)

### Output Options

- **As artifact**: Wrap in `<artifact>` tags for download/sharing
- **Inline**: Display directly in the conversation for quick review
- **Combined**: Attach critique report as second artifact alongside the designed artifact

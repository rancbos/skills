---
name: html-skill-effectiveness
description: "Generate beautiful, self-contained, single-file HTML artifacts. 13 patterns, 5-dimension critique, DevLoop iteration. No build step, no dependencies."
version: "2.1"
author: "YardonYan"
license: "Apache 2.0"
tags:
  - html
  - design
  - frontend
  - artifact
  - infographic
  - visualization
  - dashboard
related_skills:
  - baoyu-infographic
  - claude-design
  - popular-web-designs
  - sketch
---

# html-skill-effectiveness / HTML 效能

**Trade documents people skim for documents people actually read.**
**把人们略读的文档变成人们真正会阅读的文档。**

A skill for generating beautiful, self-contained, single-file HTML artifacts. No build step. No dependencies. Open directly in a browser.

## When to Use

Trigger when the user asks for:
- HTML output for status reports, comparisons, dashboards, presentations
- Visual explanations of code, architecture, or data
- Interactive explainers, flowcharts, or module maps
- "Make this HTML prettier / more professional"
- "Generate a status report as HTML"
- "Build a slide deck / dashboard / kanban board"

## Pattern Catalog (13 Patterns)

| # | Pattern | Use For |
|---|---------|---------|
| 1 | **Side-by-Side Comparison** | Tech choices, design options, trade-offs |
| 2 | **Annotated Diff** | PR reviews, code changes, before/after |
| 3 | **Module Map** | Architecture diagrams, data flow |
| 4 | **Living Design System** | Color palettes, typography, component catalogs |
| 5 | **Slide Deck** | Presentations, walkthroughs, demos |
| 6 | **Interactive Explainer** | Teaching concepts, documentation |
| 7 | **Status Report** | Weekly updates, incident reports |
| 8 | **Flowchart** | Pipelines, decision trees, workflows |
| 9 | **SVG Illustration** | Blog diagrams, figures, icons |
| 10 | **Custom Editor** | Triage boards, prompt tuning, configuration |
| 11 | **Dashboard** | Metrics, KPIs, monitoring views |
| 12 | **Live Artifact Dashboard** | Refreshable dashboards with template+data |
| 13 | **Frame Effects** | Cinematic visual moments |

## Design System

### Core Tokens (6 variables)

Everything derives from these via `color-mix()`. No raw hex outside `:root`.

```css
:root {
  --accent: #E8654A;    /* primary accent */
  --fg: #141413;        /* main text */
  --bg: #FEFDFB;        /* page background */
  --muted: #8A8A86;     /* secondary text */
  --serif: 'Playfair Display', Georgia, serif;
  --mono: 'JetBrains Mono', 'Fira Code', monospace;
}
```

### Typography

| Element | Font | Size |
|---------|------|------|
| H1 | Display serif | clamp(44px, 6vw, 76px) |
| H2 | Display serif | clamp(32px, 4vw, 48px) |
| Body | System sans | 16px |
| Code | Mono | 13px |
| Eyebrow | Mono | 11px, uppercase |

**No Inter/Roboto/Arial as display faces.** Choose distinctive typefaces.

### Chinese Font Stack

```css
--font-display-cn: 'Noto Serif SC', 'Source Han Serif SC', 'SimSun', serif;
--font-body-cn: 'Noto Sans SC', 'Source Han Sans SC', 'PingFang SC', sans-serif;
```

## Workflow

### Step 0 — Pre-flight

- [ ] Identify the purpose → map to Pattern (1-13)
- [ ] Identify the tone → choose aesthetic direction (minimal, maximalist, retro, etc.)
- [ ] Identify density → choose max-width (860px dense, 1180px spacious)

### Step 1 — Choose Aesthetic Direction

### Step 2 — Write the Artifact

- All colors from 6 tokens in `:root`
- Use `color-mix()` for derived tones
- Mobile reflow: all grids collapse at ≤920px
- No horizontal scroll

### Step 3 — Self-Critique (5 Dimensions)

Run structured self-critique across 5 dimensions. Each scored 0-10 with evidence.

| Score | Band | Description |
|-------|------|-------------|
| 0-4 | **Broken** | Fundamental issues that break the experience |
| 5-6 | **Functional** | Works but lacks polish or consistency |
| 7-8 | **Strong** | Competent, polished, intentional |
| 9-10 | **Exceptional** | Memorable, magazine-grade, pushes boundaries |

**5 Dimensions:**
1. **Philosophy Consistency** — One declared direction, stick to it
2. **Visual Hierarchy** — Can a stranger figure out reading order?
3. **Detail Execution** — Alignment, leading, kerning, edge-case spacing
4. **Functionality** — Does it WORK? Keyboard nav, click targets, responsive
5. **Innovation** — One unexpected move that makes people lean in

### Step 4 — DevLoop (Iterative Refinement)

1. **Generate** → first version
2. **Critique** → run 5-dimension self-critique
3. **Check** → if ANY dimension < 4, iterate
4. **Fix** → fix lowest-scoring dimension first
5. **Re-critique** → score again
6. **Repeat** → max 3 iterations

**Skip DevLoop if:** all dimensions ≥ 7, user says "good enough", or it's a quick draft.

### Step 5 — Emit

```html
<artifact identifier="slug" type="text/html" title="Title">
<!doctype html>
<html>...</html>
</artifact>
```

One sentence before the artifact. Nothing after `</artifact>`.

## Quality Standards

### P0 — Must Never Happen

- Raw hex outside `:root`
- `data-od-id` on every top-level `<section>`
- Mobile reflow works (grids collapse at ≤920px)
- No `scrollIntoView()` calls (use `scrollTo({...})`)

### P1 — Should Pass

- One decisive flourish (pull quote, striking stat, micro-animation)
- Section rhythm alternates (no two stat rows in a row)
- Headlines under 14 words
- CTA buttons say what happens ("Start free" beats "Get Started")
- Numerics use `.num` (mono, tabular)

### P2 — Nice to Have

- `text-wrap: pretty` / `balance` on long paragraphs
- `color-mix()` for derived tones
- Sticky topnav with frosted glass (`backdrop-filter: blur()`)

## Section Rhythm Guide

| Page kind | Default rhythm |
|-----------|---------------|
| Landing | hero → features → stats → split detail → cta |
| Dashboard | KPI row → primary chart → secondary chart/table |
| Presentation | cover → toc → section-divider → [2-4 body] → cta → thanks |
| Status Report | header → KPI cards → action items → timeline |

**Rules:**
- No two stat rows in a row
- No two quote blocks in a row
- No two feature triplets in a row
- Alternate density: airy → dense → airy
- Max one Frame Effect per page

## Decision Flow

1. What is the purpose? → Map to Pattern (1-13)
2. What is the tone? → Choose aesthetic direction
3. What is the density? → Choose max-width
4. Does it need interaction? → Add minimal JS
5. Is there data to visualize? → Use CSS charts or SVG
6. Does it need refresh/sync? → Pattern #12 (template + data)
7. Is it a presentation? → Pattern #5 with presenter mode
8. Does it need visual impact? → Pattern #13 (Frame Effect)
9. Run critique → Score 5 dimensions, iterate if < 4

## Anti-Patterns

- **Purple/violet gradients** — avoid `#a855f7`, `#8b5cf6`
- **Emoji as feature icons** — use inline SVG or mono glyphs
- **Invented metrics** — every number from user or labelled placeholder
- **Filler copy** — no "Feature One / Feature Two", lorem ipsum
- **Inter/Roboto as display** — use distinctive typefaces

## Example Prompts

- "Generate a status report as HTML"
- "Make this comparison visual with HTML"
- "Create an interactive explainer for [concept]"
- "Build a slide deck about [topic]"
- "Design a triage board for these tickets"
- "Draw a flowchart of this process"
- "Build a dashboard for [metrics]"
- "Create a live dashboard that refreshes from [source]"
- "Make a presentation with speaker notes"
- "Add a dramatic hero effect to this page"
- "Generate a critique report for this design"

## References

See `references/` directory for:
- `pattern-examples.md` — Code snippets by pattern
- `complete-examples.md` — Full HTML examples
- `critique-guide.md` — Complete critique system guide
- `frame-effects.md` — Frame Effects pattern reference

## Version History

- **v2.1** (2026-05-21): 5-dimension self-critique, DevLoop, Pattern #12/#13
- **v2.0** (2026-05-20): Combined html-effectiveness + frontend-design + open-design
- **v1.0** (2026-05): Initial release

## Credits

Based on [The Unreasonable Effectiveness of HTML](https://github.com/ThariqS/html-effectiveness) by ThariqS.
Enhanced by [YardonYan](https://github.com/YardonYan/html-skill-effectiveness).

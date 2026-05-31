# Skill Translation Reference

When asked to translate an existing skill from one language to another (e.g., English → Chinese), follow this workflow to avoid common pitfalls.

## Workflow

1. **Read ALL files first** — use `search_files(target='files')` to enumerate, then read each file completely
2. **Create a terminology glossary** — before translating anything, define consistent translations for key terms (framework names, section titles, technical terms). Present the glossary to the user for approval
3. **Present a plan** — list all files, what gets translated vs preserved, and any structural changes needed (e.g., adding CJK font support to .sty files). Use `clarify` to confirm before executing
4. **Translate in parallel** — use `delegate_task` for independent files; each subagent reads the source, translates, writes to target. Batch 2-3 files per subagent for efficiency. Give each subagent the full terminology glossary and explicit file paths
5. **Verify systematically** — run these checks in order:
   - `wc -l` on all source vs target files (truncation detection)
   - `search_files` for old skill name across all translated files (path consistency)
   - `search_files` for key section names across all files (cross-file consistency)
   - Python syntax check: `python3 -c 'import py_compile; py_compile.compile("path", doraise=True)'`
   - Spot-check YAML frontmatter, LaTeX chapter titles, box default titles

## Pitfalls

### P0: External dependency skills may not be installable via `hermes skills install`

When a skill references external skills (e.g., `scientific-schematics`, `generate-image`), `hermes skills install` may fail (timeout, "could not fetch"). The `npx skills add` approach may also time out on large repos. Fallback strategy:

1. Try `hermes skills install <owner/repo@skill> --force` first
2. If that fails, try `npx skills add <github-url> --skill <name>`
3. If that fails, use `mcp_tavily_tavily_extract` to fetch raw GitHub content (SKILL.md + scripts)
4. Write files manually to `~/.hermes/skills/<skill-name>/`

This is especially common for skills from `davila7/claude-code-templates` (27.7K star repo — very large to clone).

### P1: delegate_task can truncate large files

`write_file` in subagents has been observed to silently truncate files around 500 lines. After any delegate_task that writes a large file, ALWAYS verify with `terminal("wc -l <path>")` and compare to the source file's line count.

**Detection:** `wc -l` on source vs target. If target is significantly shorter, the file was truncated.

**Fix:** Re-translate the missing portion. If the first half was also corrupted, re-translate the entire file in a single delegate_task with explicit instructions to read ALL lines (use offset/limit). After fixing, re-verify with `wc -l`.

### P2: execute_code read_file has a 500-line default limit

When using `read_file` inside `execute_code`, the default `limit=500` means files longer than 500 lines get truncated. Use `offset` and `limit` parameters to read in chunks, or use `terminal("cat <path>")` for the full file.

### P3: Path references not updated on rename

When translating a skill that gets renamed (e.g., `market-research-reports` → `jw-market-research-reports`), ALL internal path references must be updated:
- Bash commands referencing `skills/<old-name>/scripts/...`
- Cross-references in SKILL.md to reference files
- Any hardcoded paths in scripts

**Detection:** `search_files` for the OLD skill name across all files in the new skill directory.

### P4: Cross-file name inconsistency

The SKILL.md, .tex templates, and reference files may independently translate the same concept differently (e.g., "市场概述与定义" vs "市场概述 & 定义"). After translation, grep for key section names across all files and verify consistency.

### P5: LaTeX CJK support

When translating a LaTeX skill to Chinese, the .sty file MUST include:
```latex
\RequirePackage{xeCJK}
\setCJKmainfont{Noto Sans CJK SC}
\setCJKsansfont{Noto Sans CJK SC}
\setCJKmonofont{Noto Sans Mono CJK SC}
```
Without this, the translated .tex will fail to compile.

### P6: Box environment default titles

LaTeX `tcolorbox` environments have default titles (e.g., `[Key Finding]`). These must be translated in the .sty file (e.g., `[核心发现]`), not just in the .tex template. Check ALL `\newtcolorbox` definitions.

### P7: Bash command prompts inside documentation

SKILL.md, reference files, AND `.tex` templates often contain bash examples with English prompts for image generation tools. These should be translated to the target language for consistency with the translated Python script. Use `search_files` to find remaining English prompts after translation.

**Critical blind spot — `.tex` template comments:** LaTeX templates embed image generation commands as comments (`% python skills/...`). These comment lines contain English prompts that are easy to miss because:
1. They're comments, so they don't affect rendered output
2. Audit scripts that check "visible content" skip them
3. They number in the dozens (29 in a typical market report template)

After translating a `.tex` template, ALWAYS run: `search_files` for `'% python skills/'` to find all comment-embedded commands, then grep each for English prompt patterns.

**Subagent blind spot:** delegate_task subagents reliably translate prose and table content but consistently SKIP bash command argument strings (the quoted prompts inside bash code blocks). Even when the context explicitly lists the lines to translate, subagents often miss them. After any delegation-based translation, ALWAYS run a targeted grep for English prompt patterns (`search_files` for phrases like "Bar chart", "diagram showing", "Professional executive") and fix any残留 manually. Check ALL file types: `.md`, `.tex`, `.sty`, `.py`.

### P8: .tex chapter name consistency with SKILL.md

When a translated skill has both SKILL.md (with chapter/section headers) and a `.tex` template (with `\chapter{}` commands), the names MUST match exactly. Common drift patterns:
- SKILL.md uses "与" while .tex uses "&" (e.g., "市场概述与定义" vs "市场概述 & 定义")
- SKILL.md says "投资论点" while .tex says "投资论证"
- SKILL.md says "方法论" while .tex says "研究方法"
- Appendix naming: "公司概况" vs "企业概况"

**Detection:** `grep` for `\chapter{` in the .tex file and `#### 第\|#### 附录` in SKILL.md, then compare names programmatically. Any mismatch is a bug.

### P9: Corruption recovery reverts prior fixes

When a delegate_task writes a truncated or corrupted file and you fix it by spawning another delegate_task to re-translate, the NEW translation overwrites ALL content — including any manual patches you applied between the first and second delegation. This creates a "one step forward, two steps back" pattern.

**Prevention:** Before re-delegating a corrupted file, list ALL manual fixes applied so far. After the re-delegation, re-verify each one.

**Detection:** After any re-delegation, re-run the full verification checklist (line counts, path references, cross-file consistency, English残留 grep). Do NOT assume the re-delegation preserved your intermediate fixes.

**Better approach:** Instead of re-delegating the entire file, use `patch` to fix only the truncated portion — append the missing content to the existing file rather than overwriting it entirely.

## Translation Rules Checklist

- [ ] YAML `name:` field updated to new skill name
- [ ] YAML `description:` translated
- [ ] `allowed-tools:` preserved unchanged
- [ ] All section titles translated consistently
- [ ] All explanatory text translated
- [ ] All table headers and content translated
- [ ] Framework abbreviations (TAM/SAM/SOM, PESTLE, SWOT, BCG, CAGR) preserved with target-language explanation on first use
- [ ] LaTeX commands/environments preserved unchanged
- [ ] LaTeX variable names preserved unchanged
- [ ] LaTeX `\label{}` tags preserved unchanged
- [ ] File paths in `\includegraphics{}` preserved unchanged
- [ ] Python variable/function names preserved unchanged
- [ ] Tool names (scientific-schematics, generate-image, etc.) preserved unchanged
- [ ] All path references updated to new skill name
- [ ] .sty file has CJK support (if translating to CJK language)
- [ ] .sty box default titles translated
- [ ] .tex template chapter names match SKILL.md chapter names
- [ ] Python script prompts translated
- [ ] Bash example prompts in docs translated (grep for "diagram showing", "Bar chart", "Professional" to catch残留)
- [ ] `.tex` comment-embedded prompts translated (`search_files` for `'% python skills/'`)
- [ ] .tex `\chapter{}` names match SKILL.md section headers exactly
- [ ] File line counts match source (no truncation)
- [ ] After any re-delegation: re-verify ALL prior manual fixes still present

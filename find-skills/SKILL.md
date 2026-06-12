---
name: find-skills
description: Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill for X", "is there a skill that can...", or express interest in extending capabilities. This skill should be used when the user is looking for functionality that might exist as an installable skill.
---

# Find Skills

This skill helps you discover and install skills from the open agent skills ecosystem.

## When to Use This Skill

Use this skill when the user:

- Asks "how do I do X" where X might be a common task with an existing skill
- Says "find a skill for X" or "is there a skill for X"
- Asks "can you do X" where X is a specialized capability
- Expresses interest in extending agent capabilities
- Wants to search for tools, templates, or workflows
- Mentions they wish they had help with a specific domain (design, testing, deployment, etc.)

## Installing Skills on Hermes Agent

**Prefer `hermes skills install` for native integration**, but `npx skills add` also works with caveats (see Pitfall 0).

### Native method: `hermes skills install`

```bash
# Install from GitHub (most common)
hermes skills install <owner/repo/skill-name> 2>&1

# Install with force (bypasses CAUTION verdict on community skills)
hermes skills install <owner/repo/skill-name> --force 2>&1

# List installed skills
hermes skills list

# Remove a skill
hermes skills remove <skill-name>
```

**On CAUTION/Blocked verdict:** Community skills that trigger security scans (MEDIUM/HIGH findings) are blocked by default. Use `--force` to override — this was correct behavior for `steipete/agent-scripts/skill-cleaner`, which was blocked on `persistence` and `obfuscation` findings but installed cleanly with `--force`.

**When to use `--force`:**
- Community skills from trusted sources (known GitHub repos, established developers)
- The CAUTION findings are false positives for the use case (e.g., `persistence` in a cleaner tool that writes config)
- You have verified the skill contents manually before forcing

### Alternative method: `npx skills add`

`npx skills add` installs skills to `~/data/.agents/skills/` and tries to create symlinks into `~/.hermes/skills/`. However, the symlinks may not be created correctly on the first run. **Always verify and fix after install** (see Pitfall 0).

```bash
# Install all skills from a repo (use --yes to skip interactive selection)
npx skills add <owner/repo> --yes

# After install, verify symlinks exist
ls -la ~/.hermes/skills/ | grep <skill-name>

# If missing, create manually
ln -sf ~/data/.agents/skills/<skill-name> ~/.hermes/skills/<skill-name>
```

## What is the Skills CLI?

The Skills CLI (`npx skills`) is the package manager for the open agent skills ecosystem. On Hermes, prefer `hermes skills install` (native) but `npx skills add` also works with manual symlink verification (see Pitfall 0).

## How to Help Users Find Skills

### Step 1: Understand What They Need

When a user asks for help with something, identify:

1. The domain (e.g., React, testing, design, deployment)
2. The specific task (e.g., writing tests, creating animations, reviewing PRs)
3. Whether this is a common enough task that a skill likely exists

### Step 2: Check the Leaderboard First

Before running a CLI search, check the [skills.sh leaderboard](https://skills.sh/) to see if a well-known skill already exists for the domain. The leaderboard ranks skills by total installs, surfacing the most popular and battle-tested options.

For example, top skills for web development include:
- `vercel-labs/agent-skills` — React, Next.js, web design (100K+ installs each)
- `anthropics/skills` — Frontend design, document processing (100K+ installs)

### Step 3: Search for Skills

If the leaderboard doesn't cover the user's need, run the find command:

```bash
npx skills find [query]
```

For example:

- User asks "how do I make my React app faster?" → `npx skills find react performance`
- User asks "can you help me with PR reviews?" → `npx skills find pr review`
- User asks "I need to create a changelog" → `npx skills find changelog`

### Step 4: Verify Quality Before Recommending

**Do not recommend a skill based solely on search results.** Always verify:

1. **Install count** — Prefer skills with 1K+ installs. Be cautious with anything under 100.
2. **Source reputation** — Official sources (`vercel-labs`, `anthropics`, `microsoft`) are more trustworthy than unknown authors.
3. **GitHub stars** — Check the source repository. A skill from a repo with <100 stars should be treated with skepticism.

### Step 5: Present Options to the User

When you find relevant skills, present them to the user with:

1. The skill name and what it does
2. The install count and source
3. The install command they can run
4. A link to learn more at skills.sh

Example response:

```
I found a skill that might help! The "react-best-practices" skill provides
React and Next.js performance optimization guidelines from Vercel Engineering.
(185K installs)

To install it:
npx skills add vercel-labs/agent-skills@react-best-practices

Learn more: https://skills.sh/vercel-labs/agent-skills/react-best-practices
```

### Step 6: Offer to Install

If the user wants to proceed, install it for them:

```bash
hermes skills install <owner/repo@skill> 2>&1
```

Example for a skill from `steipete/agent-scripts/skill-cleaner`:

```bash
hermes skills install steipete/agent-scripts/skill-cleaner --force 2>&1
```

Always use `--force` when the source is a community repo and the CAUTION verdict is a known false positive for the use case.

## Common Skill Categories

When searching, consider these common categories:

| Category        | Example Queries                          |
| --------------- | ---------------------------------------- |
| Web Development | react, nextjs, typescript, css, tailwind |
| Testing         | testing, jest, playwright, e2e           |
| DevOps          | deploy, docker, kubernetes, ci-cd        |
| Documentation   | docs, readme, changelog, api-docs        |
| Code Quality    | review, lint, refactor, best-practices   |
| Design          | ui, ux, design-system, accessibility     |
| Productivity    | workflow, automation, git                |

## Pitfalls

### Pitfall0: npx skills add — symlinks may not land in Hermes directory

`npx skills add` installs skills to `~/data/.agents/skills/` and reports "symlink → Hermes Agent", but the symlinks in `~/.hermes/skills/` may not actually be created. After any `npx skills add` run:

1. Check: `ls ~/.hermes/skills/ | grep <skill-name>`
2. If missing, create manually: `ln -sf ~/data/.agents/skills/<skill-name> ~/.hermes/skills/<skill-name>`
3. Verify with `skills_list` that the skill appears

To remove skills installed via npx: delete both the symlink (`~/.hermes/skills/<name>`) AND the source directory (`~/data/.agents/skills/<name>`).

### Pitfall1: npx skills add is interactive — even with `--yes` / `--all`

`npx skills add <repo> --skill <name> -y` still drops into an interactive "Which agents do you want to install to?" picker (multi-select with arrow keys + space + enter). `--all` and `-y` do NOT bypass this. The CLI's `--agent '*'` exists but only takes effect AFTER the picker completes, which can't happen in a non-pty shell call.

**Symptom:** Command hangs at the "Additional agents" selection prompt in any non-interactive shell session (cron, agent tool calls, CI).

**Fallback — direct git clone + copy (preferred when npx is blocked):**
```bash
#1. Shallow clone to /tmp
git clone --depth=1 https://github.com/<owner>/<repo> /tmp/<repo>

#2. Locate the skill directory inside the repo (typically repo/skills/<skill-name>/)
ls /tmp/<repo>/skills/

#3. Copy directly into Hermes skills
mkdir -p ~/.hermes/skills/<skill-name>
cp -r /tmp/<repo>/skills/<skill-name>/. ~/.hermes/skills/<skill-name>/

#4. Verify
ls ~/.hermes/skills/<skill-name>/
# Should see: SKILL.md, possibly references/, scripts/, templates/, assets/
```

**When to use this fallback:**
- `npx skills add` hangs in non-pty shell
- Hermes Agent is not listed among the60+ agents npx skills targets
- You only need ONE skill from a repo, not the whole ecosystem

**Note:** Avoid `git clone --depth1` (with space) via `terminal()` — the tool collapses `--depth1` to `--depth1`, which git rejects. Always use `--depth=1` (equals form).

### Pitfall2: No "Hermes" agent in npx skills' agent list

`npx skills add` enumerates60+ target agents (Amp, Claude Code, Cursor, AiderDesk, etc.) but Hermes Agent is not among them. Even if you bypass the interactive picker, the install lands in `~/data/.agents/skills/` — not where Hermes reads from. The direct git clone + copy fallback (Pitfall1) is the only reliable way to install a skill into Hermes from an arbitrary GitHub repo.

## Tips for Effective Searches

1. **Use specific keywords**: "react testing" is better than just "testing"
2. **Try alternative terms**: If "deploy" doesn't work, try "deployment" or "ci-cd"
3. **Check popular sources**: Many skills come from `vercel-labs/agent-skills` or `ComposioHQ/awesome-claude-skills`

## When No Skills Are Found

If no relevant skills exist:

1. Acknowledge that no existing skill was found
2. Offer to help with the task directly using your general capabilities
3. Suggest the user could create their own skill with `npx skills init`

Example:

```
I searched for skills related to "xyz" but didn't find any matches.
I can still help you with this task directly! Would you like me to proceed?

If this is something you do often, you could create your own skill
using `hermes skills create` or the skill_manage tool.
```

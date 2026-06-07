# Checking Upstream Version of a Skill

When a user asks to "sync" or "update" a skill from upstream, follow this workflow to determine whether a sync is actually needed before doing any merging.

## Workflow

### Step 1: Identify the upstream source

Check for clues in the skill directory:
- `.git` directory → git repo with remote
- `package.json` → npm package
- `LICENSE.txt` with known org (Apache 2.0 + Anthropic/Claude references → `anthropics/skills`)
- SKILL.md content mentioning specific orgs or repos
- Search GitHub: `site:github.com/<org>/skills <skill-name> SKILL.md`

Known upstream registries:
- Anthropic official: `https://github.com/anthropics/skills/tree/main/skills/<name>`
- Hermes hub: `https://hermes-agent.nousresearch.com/docs/skills`

### Step 2: Check upstream commit history

```bash
curl -s "https://api.github.com/repos/<org>/skills/commits?path=skills/<name>/SKILL.md&per_page=3" \
  | python3 -c "import json,sys; [print(f'{c[\"sha\"][:7]} {c[\"commit\"][\"committer\"][\"date\"]} {c[\"commit\"][\"message\"].split(chr(10))[0][:60]}') for c in json.load(sys.stdin)]"
```

### Step 3: Compare file structure

```bash
# List upstream files
curl -s "https://api.github.com/repos/<org>/skills/contents/skills/<name>" \
  | python3 -c "import json,sys; [print(f'{x[\"type\"]:4s} {x[\"name\"]}') for x in json.load(sys.stdin)]"
```

Compare with local: `ls -la ~/.hermes/skills/<name>/`

### Step 4: Compare content (md5 checksums)

For each file that exists in both upstream and local:
```bash
curl -sL "https://raw.githubusercontent.com/<org>/skills/main/skills/<name>/<file>" | md5sum
md5sum ~/.hermes/skills/<name>/<file>
```

### Step 5: Diff SKILL.md if different

```bash
curl -sL "https://raw.githubusercontent.com/<org>/skills/main/skills/<name>/SKILL.md" -o /tmp/upstream.md
diff /tmp/upstream.md ~/.hermes/skills/<name>/SKILL.md
```

Interpret diff output:
- All `>` lines (additions only, no `<` lines) = local is a superset, no sync needed
- `<` lines present = upstream has content local doesn't have → sync needed
- Both `<` and `>` = diverged, needs careful merge

### Step 6: Report findings

Present a clear table:

| Component | Upstream | Local | Status |
|-----------|----------|-------|--------|
| SKILL.md | N lines | M lines | identical / local superset / diverged |
| scripts/ | N files | M files | identical / different |
| references/ | N files | M files | identical / local additions |

**Possible outcomes:**
1. **Local is superset** → "不需要同步。本地已包含上游所有内容。"
2. **Upstream has new content** → Show the diff, let user decide what to merge
3. **Diverged** → Show both versions, propose merge strategy
4. **No upstream found** → "无上游源，纯本地 skill。"

## Pitfalls

### Pitfall 1: API rate limiting
GitHub API has rate limits (60/hour unauthenticated). When comparing many files, batch the checksums rather than fetching one by one. If rate limited, fall back to comparing only SKILL.md + scripts/.

### Pitfall 2: Local modifications may be intentional
Local versions often have legitimate additions (domain-specific pitfalls, Chinese translations, custom references). Don't blindly overwrite local with upstream. Always present the diff and let the user decide.

### Pitfall 3: `raw.githubusercontent.com` can be slow
Use `curl -sL --max-time 15` to avoid hanging. If it times out, the file may not exist upstream (404) or the network is slow — try again or skip that file.

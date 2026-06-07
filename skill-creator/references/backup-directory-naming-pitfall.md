# Backup Directory Naming Pitfall

When creating backups of a skill directory (e.g., `cp -r skill-name skill-name-backup-YYYYMMDD`), the backup directory can cause `skill_view(name='skill-name')` to fail with an "Ambiguous skill name" error if the backup contains a subdirectory with the same SKILL.md name.

## Detection

`skill_view` returns:
```
Ambiguous skill name 'X': 2 skills match across your local skills dir and external_dirs.
matches: ["/root/.hermes/skills/X/SKILL.md", "/root/.hermes/skills/X-backup-YYYYMMDD/X/SKILL.md"]
```

## Root Cause

`skill_view` scans both `skills/` and `external_dirs/` for matching skill names. If a backup directory has the same folder structure (skill-name/SKILL.md inside the backup), it creates a collision.

## Workarounds

1. **Rename backup subdirectory**: `mv skill-name-backup-YYYYMMDD/skill-name skill-name-backup-YYYYMMDD/skill-name-old`
2. **Move backup out of skill dir**: `mv skill-name-backup-YYYYMMDD /tmp/`
3. **Use full path**: `skill_view(name='skill-name/SKILL.md')` — use the categorized path to disambiguate

## Prevention

When creating backups, rename the inner skill directory:
```bash
cp -r skill-name skill-name-backup-YYYYMMDD
mv skill-name-backup-YYYYMMDD/skill-name skill-name-backup-YYYYMMDD/old
```

Or use `--no-target-directory` to avoid nested structure.

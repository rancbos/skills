# Pitfall: Line Number Prefix Pollution

## Problem
When files are read via `read_file` tool and written back, they may accumulate line number prefixes like `N|` or `N|N|N|`. This causes:
- Python `SyntaxError: invalid syntax` (e.g., `1|#!/usr/bin/env python3`)
- Bash syntax errors
- Silent data corruption

## Root Cause
`read_file` returns content with line numbers (e.g., `1|#!/usr/bin/env python3`). If this output is inadvertently written back to the file, the prefixes persist.

## Detection
```bash
# Check first 5 lines for N| prefix
head -5 file.py | grep -P '^\d+\|'
```

## Fix
```bash
# Remove all N| prefixes (handles N|N|N| nesting)
sed -i 's/^[0-9]*|//g' file.py

# For nested prefixes (N|N|N|), run multiple passes or:
sed -i 's/^[0-9]*|[0-9]*|[0-9]*|[0-9]*|//g; s/^[0-9]*|[0-9]*|[0-9]*|//g; s/^[0-9]*|[0-9]*|//g; s/^[0-9]*|//g' file.py
```

## Prevention
- **Before writing**: Always verify the first line has no `N|` prefix
- **After writing**: Run `head -1 file | grep -P '^\d+\|'` to confirm clean
- **In audit_consistency.sh**: Check is already included (item 7)

## Occurrences in This Skill
- `scripts/pre_analysis.py` had `1|1|#!/usr/bin/env python3` (v3.60.8, fixed in v3.61.0)
- `SKILL.md` had `105|105|105|105|105|` prefix on multiple lines (v3.60.8, fixed in v3.61.0)

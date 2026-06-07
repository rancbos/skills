# Python Pitfalls in Skill Scripts

## Encoding Declaration

**Symptom**: `SyntaxError: Non-ASCII character '\xe6' in file ... but no encoding declared`

**Cause**: Python files containing Chinese (or other non-ASCII) characters require an encoding declaration at the top.

**Fix**: Always include this as the second line in Python scripts:
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Docstring here...
"""
```

**When to apply**: Any Python script that will contain Chinese comments, Chinese string literals, or Chinese output messages.

---

## Path + String Concatenation

**Symptom**: `TypeError: unsupported operand type(s) for +: 'PosixPath' and 'str'`

**Cause**: Python's `pathlib.Path` objects support `/` operator for joining, but NOT `+` for concatenation.

**Wrong**:
```python
path = CHECKPOINT_DIR / object_name.replace(' ', '_') + '_research.json'
```

**Right**:
```python
safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in object_name)
path = CHECKPOINT_DIR / f'{safe_name}_research.json'
```

**When to apply**: Any time you're building file paths dynamically in Python scripts.

---

## Type Annotations with Union Types

**Symptom**: In older Python environments, `dict | None` syntax may fail.

**Cause**: The `X | Y` union type syntax requires Python 3.10+.

**Fix for compatibility**:
```python
# Python 3.10+
def load_checkpoint(object_name: str, stage: str) -> dict | None:

# Python 3.9 and earlier
from typing import Optional
def load_checkpoint(object_name: str, stage: str) -> Optional[dict]:
```

**Note**: Current environment is Python 3.12.3, so `dict | None` is fine. But if targeting broader compatibility, use `Optional`.

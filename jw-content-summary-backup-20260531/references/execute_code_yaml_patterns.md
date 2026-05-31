# execute_code 提取模式备忘

## 0. 候选文件实际格式（与 schema 文档描述有差异）

候选文件（principles.md 等）的实际格式：

```
- id: pr-02
  title: 投资者与投机者的根本区别
  type: principle
  source_chapter: ch009 / 第一章 聪明的投资者将获得
  source_line: 3
  source_quote: "市场短期是投票机，长期是称重机。"
  ...
---
- id: pr-03
  title: ...
  ...
```

每块以 `- id:` 开头，`\n---\n` 为块分隔符。**不是** 以 `---` 开头的 YAML 多文档格式。

错误识别：文件不以 `---` 开头，不能用 `yaml.safe_load('---' + block)`。
正确识别：检查 `block.lstrip('-').strip().startswith('id:')` 或 `re.match(r'^\s*-?\s*id:', block)`。

正确解析流程：

```python
import re
for block in text.split('\n---\n'):
    block = block.strip()
    if not block:
        continue
    stripped = block.lstrip('-').strip()
    if not stripped.startswith('id:'):
        continue
    m = re.search(r'^id:\s*["\']?(\S+)', stripped)
    if not m:
        continue
    cid = m.group(1)
    # 继续提取其他字段...
```

> ⚠️ 本节是本次会话（2026-05-24《聪明的投资者》处理）新发现。旧的 "YAML 多文档解析必须加 `---\n` 前缀" pattern 描述的是以 `---` 开头的 YAML-FM 格式，与候选文件格式不同，请勿套用。

### 1. 以 `---` 开头的 YAML-FM 格式（不适用于候选文件）

```python
import yaml
for block in text.split('\n---'):
    block = block.strip()
    if not block.startswith('- id:') and not block.startswith('---'):
        continue
    try:
        data = yaml.safe_load('---\n' + block)
        if isinstance(data, list):
            entries.extend(data)
        elif isinstance(data, dict) and data.get('id'):
            entries.append(data)
    except:
        pass
```

### 2. framework structure 字段的正确处理

`structure` 是简单 dict（key 映射到字符串值），不要嵌套迭代：

```python
# 错误方式（会炸）：
for k, v in struct.items():
    for k2, v2 in v.items():  # v 是 str，不是 dict
        lines.append(...)

# 正确方式：
if e.get('structure'):
    struct = e['structure']
    for k, v in struct.items():
        lines.append(f'  {k}: {v}')
```

### 3. insights.md 空字段填充

`common_sense` 和 `author_reversal` 为空时用空字符串：

```python
if 'common_sense:' not in block and 'author_reversal:' not in block:
    # 在 'related: [...]' 行之后插入：
    lines.append('  common_sense: ""')
    lines.append('  author_reversal: ""')
```

**陷阱**：validate 脚本要求这两个字段必须存在，空值也要填。

### 4. execute_code 中的路径处理

中文路径不用 string concatenation，用 `pathlib.Path`:

```python
from pathlib import Path
out_dir = Path('/home/jw/books/中文书名/中文书名')
candidates_dir = out_dir / 'candidates'
# ✅ out_dir / 'principles.md'
# ❌ f'{out_dir}/principles.md'
```

### 5. to_yaml_entry() 参考实现（用于 execute_code 输出 YAML）

```python
def to_yaml_entry(e):
    kw = ', '.join(f'"{k}"' for k in e.get('keywords', []))
    rel = ', '.join(f'"{r}"' for r in e.get('related', []))
    lines = [
        f'- id: {e["id"]}',
        f'  title: {e["title"]}',
        f'  type: {e["type"]}',
        f'  source_chapter: {e["source_chapter"]}',
        f'  source_line: {e["source_line"]}',
        f'  source_quote: "{e["source_quote"]}"',
        f'  summary: {e["summary"]}',
        f'  keywords: [{kw}]',
        f'  v3_pass: {str(e.get("v3_pass", True)).lower()}',
        f'  v3_reason: {e["v3_reason"]}',
        f'  v2_scenario: {e["v2_scenario"]}',
        f'  related: [{rel}]',
    ]
    # optional fields
    if e.get('common_sense') is not None:
        lines.append(f'  common_sense: "{e["common_sense"]}"')
    if e.get('author_reversal') is not None:
        lines.append(f'  author_reversal: "{e["author_reversal"]}"')
    if e.get('structure'):
        for k, v in e['structure'].items():
            lines.append(f'  {k}: {v}')
    return '\n'.join(lines)
```

适用于 principles / frameworks / boundaries。insights 额外加 `common_sense` + `author_reversal`。boundaries 不需要 `structure`。

### 6. Python 3.12+ Unicode 字符陷阱（execute_code 脚本）

Python 3.12+ 对源代码文件中的非 ASCII 字符执行更严格的校验。在双引号字符串内使用 `→`（U+2192）、`，`（U+FF0C 全角逗号）等字符时，即使合法嵌套在字符串中，也可能触发 `SyntaxError: invalid character`。

**触发条件**：Python 3.12.3 实测，`python3 -c` 内联执行正常，但从 `.py` 文件读取时可能报错。

**修复方案**：
- 用 ASCII 替代：`→` → `->`，`—` → `--`，全角标点 → 半角标点
- 必要时用 `sed -i 's/→/->/g' script.py` 批量替换
- 写 execute_code 脚本时始终用 ASCII 字符和半角标点，保持最广泛兼容性

**实测案例**（《债务危机》2026-05-28）：
```python
# ❌ 触发 SyntaxError: invalid character '→' (U+2192)
"形成\"越印钞→越贬值→越没人持有\"的死亡螺旋。"

# ✅ 正常运行
'形成越印钞->越贬值->越没人持有的死亡螺旋。'
```

### 7. `linked_method_hint` 字段 — case 类型候选必须

`validate_candidates.py` 要求 `type: case` 的候选必须包含 `linked_method_hint` 字段。缺失时 validate 报：
```
cases.md#ca-01: missing required fields: ['linked_method_hint']
```

**修复**：在 case 候选的 `type: case` 之后添加一行：
```yaml
  linked_method_hint: "典型债务周期五阶段模型"
```
然后用 `pipeline_phase2.py` 重跑验证。

**注意**：此字段仅 case 类型需要，framework/principles/boundaries/glossary/insights/procedures 不需要。当前 validate_candidates.py（v4.27）将其列为 case 类型的必需字段。
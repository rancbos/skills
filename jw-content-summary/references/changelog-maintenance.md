# SKILL.md Changelog 维护指南

> 适用于：jw-content-summary 等版本迭代频繁的大型 skill。

## 问题模式

changelog 写在 SKILL.md 头部时，每次 skill_manage(action='patch') 往往在头部追加新版本条目，但不清理旧条目。时间久了会出现：

1. **版本条目重复**：同一版本（如 v4.37）出现 3-6 次，每次措辞略有不同
2. **条目膨胀**：changelog 占 SKILL.md 的 40%+，挤占正文空间
3. **格式混乱**：有些条目是长文描述，有些是 `| v4.XX | date | desc |` 表格格式

## 清理策略

### Step 1：定位 changelog 边界

```bash
grep -n "^## v4\." SKILL.md  # 找所有版本标题
grep -n "^## [0-9]" SKILL.md  # 找所有正文章节
```

changelog 通常在 YAML frontmatter 之后、正文 §1 之前。

### Step 2：去重（Python — 推荐：re.split + last-wins）

比逐行跟踪更稳健，适用于 changelog.md 有多个重复块（如两次迁移遗留）的情况：

```python
import re

with open('changelog.md', 'r') as f:
    raw = f.read()

sections = re.split(r'(^## v[\d.]+.*$)', raw, flags=re.MULTILINE)
header = sections[0]
version_dict = {}
version_order = []

for i in range(1, len(sections), 2):
    ver_header = sections[i].strip()
    ver_body = sections[i+1].strip() if i+1 < len(sections) else ""
    m = re.match(r'## (v[\d.]+(?:-v[\d.]+)?)', ver_header)
    if m:
        ver_num = m.group(1)
        if ver_num in version_dict:
            version_order.remove(ver_num)  # remove old position
        version_dict[ver_num] = (ver_header, ver_body)
        version_order.append(ver_num)

# Rebuild: header + sorted versions (newest first)
# ... write back
```

**关键**：每个版本只保留最后一次出现（last-wins），因为后出现的通常是更完整的描述。

### Step 2b：去重（备选：逐行跟踪）

```python
import re
with open('SKILL.md', 'r') as f:
    lines = f.readlines()

seen = {}
remove = []
for i, line in enumerate(lines):
    m = re.match(r'^## v4\.(\d+) \(', line)
    if m:
        ver = m.group(1)
        if ver in seen:
            end = i + 1
            while end < len(lines):
                if lines[end].startswith('---') or lines[end].startswith('## v4.'):
                    break
                end += 1
            remove.append((i, end))
        else:
            seen[ver] = i

for start, end in reversed(remove):
    del lines[start:end]
```

### Step 3：清理 §14 版本摘要表重复

```python
# 同样逻辑，但匹配 "| v4.XX |" 格式
for i, line in enumerate(lines):
    if line.startswith('| v4.'):
        m = re.match(r'\| v4\.(\d+) \|', line)
        # ... 同上去重逻辑
```

### Step 4：验证

```bash
grep -c "^## v4\.37" SKILL.md  # 应为 1
grep -c "| v4\.37 |" SKILL.md  # 应为 1
```

## 防止复发

- 每次 skill_manage(action='patch') 添加新版本时，同时检查是否需要清理旧条目
- changelog 详细描述保留在 SKILL.md 头部（最近 5-10 个版本）
- 更早的版本只保留在 §14 版本摘要表中（一行一条）
- 考虑将详细 changelog 移到 `references/changelog.md`，SKILL.md 只保留摘要表

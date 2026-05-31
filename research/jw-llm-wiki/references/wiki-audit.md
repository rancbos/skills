# Wiki 健康审计方法论

> 版本：v1.0 | 基于 2026-05-30 全库审计经验

## 审计时机

- 用户要求 lint/审计/健康检查
- 距离上次 audit 超过 30 天
- 大规模摄入（10+ 页面）后
- wiki 超过 100 页时，作为定期维护

## 审计清单（按严重性排序）

### ① 死链检测（最高优先级）

```python
# 1. 获取所有存在页面的 slug
import os, re
all_slugs = set()
for root, dirs, files in os.walk(f"{wiki}/entities"):
    for f in files:
        if f.endswith('.md'):
            all_slugs.add(f[:-3])

# 2. 提取所有 [[wikilinks]] 目标
linked = set()
for root, dirs, files in os.walk(f"{wiki}/entities"):
    for fname in files:
        if not fname.endswith('.md'):
            continue
        with open(f"{root}/{fname}") as f:
            content = f.read()
        for m in re.findall(r'\[\[([^\]|]+)', content):
            target = m.strip()
            if not target.startswith('http') and '|' not in target:
                linked.add(target)

# 3. 死链 = 被链接但不存在
dead = linked - all_slugs
```

### ② 孤儿页面检测

```python
# 统计入链数
incoming = {s: 0 for s in all_slugs}
for root, dirs, files in os.walk(f"{wiki}/entities"):
    for fname in files:
        if not fname.endswith('.md'):
            continue
        with open(f"{root}/{fname}") as f:
            content = f.read()
        for m in re.findall(r'\[\[([^\]|]+)', content):
            target = m.strip()
            if target in incoming:
                incoming[target] += 1

orphans = [s for s, n in incoming.items() if n == 0]
```

### ③ SCHEMA.md 数字漂移

SCHEMA.md 中的 "现有典籍清单" 是最容易漂移的位置。每次大规模摄入后必须更新。

对比方法：
```bash
# 实际各分类页数
for d in $(find $WIKI_PATH/entities -mindepth 1 -maxdepth 1 -type d); do
    echo "$(find $d -name '*.md' | wc -l) $(basename $d)"
done
```

常见漂移源：
- 批量摄入后忘记更新 SCHEMA 清单
- 新增分类（如 malie）未在 SCHEMA 中登记
- 概念页数量遗漏

### ④ index.md 完整性

```python
# 检查 index.md 是否收录所有页面
index_slugs = set()
with open(f"{wiki}/index.md") as f:
    for line in f:
        for m in re.findall(r'\[\[([^\]|]+)', line):
            index_slugs.add(m.strip())

missing = all_slugs - index_slugs
```

同时检查 index 头部的 "总计" 数字是否与实际一致。

### ⑤ 标签漂移

```python
# 收集所有实际使用的标签
all_tags = set()
for root, dirs, files in os.walk(f"{wiki}/entities"):
    for fname in files:
        if not fname.endswith('.md'):
            continue
        with open(f"{root}/{fname}") as f:
            content = f.read()
        m = re.search(r'^tags:\s*\[(.*?)\]', content, re.MULTILINE)
        if m:
            for t in m.group(1).split(','):
                tag = t.strip().strip('"').strip("'")
                if tag:
                    all_tags.add(tag)

# 与 SCHEMA.md 标签分类对比
# 未登记的标签应加入分类或从页面中修剪
```

### ⑥ Frontmatter 字段完整性

```bash
# 检查缺少必填字段的页面
for f in $(find $WIKI_PATH/entities $WIKI_PATH/concepts -name '*.md'); do
    slug=$(basename "$f" .md)
    for field in created updated type tags category; do
        grep -q "^${field}:" "$f" || echo "$slug: missing $field"
    done
done
```

### ⑦ Raw 文件 sha256

```python
# 检查 raw 文件是否有 sha256 frontmatter
for fpath in raw_files:
    with open(fpath) as f:
        head = f.read(200)
    if 'sha256:' not in head:
        # 需要补充
        body = content  # 去掉已有 frontmatter
        sha = hashlib.sha256(body.encode()).hexdigest()
```

## index.md 重建技术

当 index.md 严重过时时，完全重建比增量修补更可靠。

**关键：在 execute_code 中用纯 Python I/O，不要用 terminal() 传 bash for 循环。**
后者在 execute_code 的 shell 逃逸中会失败，导致命令源码被写入文件。

```python
import os, re

def extract_title(filepath):
    """从 YAML frontmatter 提取 title"""
    with open(filepath, 'r') as f:
        in_frontmatter = False
        for line in f:
            line = line.strip()
            if line == '---':
                if not in_frontmatter:
                    in_frontmatter = True
                    continue
                else:
                    break
            if in_frontmatter and line.startswith('title:'):
                return line[6:].strip().strip('"').replace('《','').replace('》','')
    return None

# 按分类目录收集所有页面
entities = {}
for cat_dir in sorted(os.listdir(f"{wiki}/entities")):
    path = f"{wiki}/entities/{cat_dir}"
    if not os.path.isdir(path):
        continue
    items = []
    for fname in sorted(os.listdir(path)):
        if not fname.endswith('.md'):
            continue
        slug = fname[:-3]
        title = extract_title(f"{path}/{fname}") or slug
        items.append(f"[[{slug}]] {title}")
    entities[cat_dir] = items

# 写入 /tmp/ 再 mv，避免 write_file 缓存问题
with open('/tmp/wiki-index-new.md', 'w') as f:
    # 构建 index 内容...
    pass
```

## 修复模式

### 死链分三类处理

| 类型 | 示例 | 修复方式 |
|------|------|---------|
| Typo/别名 | [[mozǐ]] → [[mozi]] | sed 批量替换 |
| 缺实体页 | [[benjamin-graham]] | 创建 stub 页 |
| 缺概念页 | [[tianming]] | 创建概念页+跨实体引用 |

### 孤儿互链策略

按标签分组，同标签页面互相链接：
```python
# 对每个孤儿，找 3-5 个同标签的 peer
for slug in orphans:
    peers = set()
    for tag in page_tags[slug]:
        peers.update(tag_index[tag])  # tag_index: tag→[slugs]
    selected = list(peers - {slug})[:5]
    section = '## 相关书籍\n' + ' '.join(f'[[{p}]]' for p in selected)
    with open(page_path, 'a') as f:
        f.write(section)
```

## 审计报告模板

```
## [YYYY-MM-DD] audit | 全库健康检查

发现：
- 死链：N 个（typo M 个 + 缺页面 K 个）
- 孤儿：N 个（占总页面 X%）
- SCHEMA 数字漂移：N 个分类
- index 遗漏：N 页
- 标签未登记：N 个
- Frontmatter 缺失字段：N 页
- Raw 缺 sha256：N 文件

修复：...
```

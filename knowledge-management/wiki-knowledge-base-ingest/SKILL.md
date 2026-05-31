---
name: wiki-knowledge-base-ingest
description: 将本地 txt/md 文件批量接入 Wiki 知识库（/root/wiki-ai/），生成 entity 页、更新 index.md、追加 log.md。触发词：加入知识库、导入知识库、书籍入库、批量导入文件、txt文件整理、归类到wiki。
agent_created: true
---

# Wiki 知识库批量导入（jw-wiki-ingest）

将 `/root/books/` 等目录下的文本文件（.txt / .md）批量接入 Wiki 知识库（`/root/wiki-ai/`），按现有分类体系生成 entity 页，并更新 `index.md` 索引和 `log.md` 操作日志。

> **TL;DR**: `盘点文件 → 已有/新建分类 → 抽取内容摘要 → 写 entity → 更新 index+log`。跳过已有 entity 文件的书籍，避免重复创建。

## 触发器

用户说类似的话时激活：
- "把 xxx 中的书加入到知识库"
- "把 xxx 目录的文件导入到 wiki"
- "书籍入库"、"导入知识库"、"批量归类 txt 文件"

## 核心概念

**Wiki 知识库结构**（`/root/wiki-ai/`）：
```
index.md       — 全部典籍的 wikilink 索引（按分类分组）
log.md         — 操作日志（追加制）
entities/      — 各分类的实体页目录
  rujia/       — 儒家典籍
  dao/         — 道家
  fo/          — 佛家
  fajia/       — 法家
  baojia/      — 诸子百家
  lishi/       — 历史
  zhongyi/     — 中医
  mengxue/     — 蒙学
  nanhuaijin/  — 南怀瑾
  bingjia/     — 兵家
  invest/      — 价值投资（67本）
```

**Entity 文件格式**：
- 文件名：`{entity_id}.md`
- 内含 YAML frontmatter（可选）、标题、一句话简介、核心观点、wikilinks、原始来源路径
- Wikilink 格式：`[[entity_id]]`

**分类原则**：
- 已有分类优先：价值投资/政治理论/文化典籍等已有分类
- 政治/马列/党和国家著作 → 暂不归入（需新建分类时先报方案）
- 超大文件（>20MB）→ 只建 entity 引用，不复制原始文件内容到 entities/

## 工作流

### Step 0: 确认知识库路径

目标知识库：`/root/wiki-ai/`

### Step 1: 盘点来源目录

扫描源目录（如 `/root/books/`），列出全部文件，排除目录：

```python
import os
books_dir = "/root/books"
book_files = [f for f in os.listdir(books_dir) if os.path.isfile(os.path.join(books_dir, f))]
```

### Step 2: 读取现有 entity 和 index 记录

```python
# 获取已入库的 entity_id 列表
existing_entities = set()
for cat in os.listdir("/root/wiki-ai/entities"):
    d = f"/root/wiki-ai/entities/{cat}"
    if os.path.isdir(d):
        for f in os.listdir(d):
            if f.endswith('.md'):
                existing_entities.add(f.replace('.md', ''))

# 读取 index.md 中的 wikilink（用于识别计划中但未建文件的条目）
with open("/root/wiki-ai/index.md", encoding="utf-8") as fh:
    index_content = fh.read()
links_in_index = set()
import re
for m in re.finditer(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', index_content):
    links_in_index.add(m.group(1).strip())
```

### Step 3: 建立书名 → entity_id 映射表

手动建立映射字典（示例格式）：

```python
name_to_entity = {
    '巴菲特之道.txt': 'buffett-zhi-dao',
    '金钱心理学：财富、人性和幸福的永恒真相.md': 'jinqian-xinlixue',
    ...
}
```

**映射优先级**：
1. 完全匹配书名
2. 含书名关键词模糊匹配
3. 无法映射 → 新建 entity_id

### Step 4: 分类处理

逐文件判断状态：

| 状态 | 条件 | 操作 |
|------|------|------|
| 已存在 | entity_id 在 `existing_entities` 中 | 跳过（在日志中注明"已入库"） |
| 计划中 | entity_id 在 `links_in_index` 但无实体文件 | 重建 entity 文件 |
| 新建 | entity_id 不存在 | 创建 entity 页 |

**分类目录选择**（按文件主题）：
- 价值投资 → `entities/invest/`
- 政治理论/党和国家著作 → **先报方案，不自动入库**（需新建分类）
- 传统文化典籍 → 按儒/道/佛/法/兵等分类
- 马列著作 → 需新建 `marx/` 分类或暂缓

**超大文件处理**（>20MB）：
- 不将文件内容复制到 entities/
- Entity 页正文只写引用路径和摘要，不写全文

### Step 5: 生成 entity 页

Entity 文件模板：

```markdown
# {书名}

**作者**: {作者名}

**类别**: {分类}

**核心标签**: #标签1 #标签2

---

## 一句话简介

{一句话描述}

---

## 核心观点

- {要点1}
- {要点2}
- {要点3}

---

## 与其他典籍的关联

- [[相关entity_id]] — 关联说明

---

## 原始来源

📁 `/root/books/{原始文件名}`

---

*本条目由系统自动创建 · {YYYY-MM-DD}*
```

### Step 6: 更新 index.md

在对应分类下追加 wikilink，格式：

```markdown
|[[entity_id]] 书名 — 一句话简介
```

### Step 7: 追加 log.md

在日志开头插入新条目：

```markdown
## [{YYYY-MM-DD}] ingest | {操作描述}

**来源**: {来源目录} → {目标目录}
**操作**: {操作概要}

**完成书目**:
- {书名1}（{作者或分类}）
- {书名2}（{作者或分类}）

**更新**: index.md（新增{N}条）、entities/{分类}/（{N}个新entity文件）
```

### Step 8: 向用户汇报

汇报格式：
- 总文件数 / 已入库数 / 本次新增数
- 跳过的书目（含原因）
- 更新的文件列表

---

## 已知陷阱

1. **文件名含全角符号**：如 `逃不开的经济周期：历史，理论与投资现实.md`（全角冒号/逗号），清洗时需注意
2. **目录型"书籍"**：`巴菲特致股东的信-沃伦・巴菲特` 是目录不是文件，处理方式：提取 `SUMMARY.md` 内容建 entity
3. **政治内容**：暂不自动归类，需先确认用户意图
4. **超大文件**：直接复制会导致 entities/ 膨胀，只写引用路径

## 配套脚本

无。自定义 Python 脚本直接操作文件系统。

## 参考文件

- `references/entity-template.md` — entity 页完整模板（含 frontmatter）
- `references/index-format.md` — index.md wikilink 格式规范
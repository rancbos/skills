---
name: jw-ebook-organizer
description: This skill should be used when the user wants to organize, sort, classify, or tidy up ebook files (pdf/epub/mobi/azw3) on their computer into category folders. 触发词：整理电子书、归类电子书、图书分类、整理本地图书、电子书归档。英文触发词：organize ebooks, classify books, sort library, tidy up ebooks. It handles scanning a directory for ebook files (including incremental mode), cleaning messy filenames, performing web searches to determine each book's CLC subject area and author, classifying into a multi-level CLC hierarchy (29 subcategories), moving files with multi-format merging and author grouping, generating a human-readable Markdown index, and providing undo/rollback support. Do not use for non-ebook files (images, documents, audio).
agent_created: true
---

IRON LAW: 始终先dry-run确认，再执行实际移动操作。任何文件操作必须可回滚（保留.move_manifest.json）。

# Ebook Organizer (JW 定制版)

自动整理电脑上的电子书文件，采用**中国图书馆图书分类法（CLC/中图法）**，按学科属性分类到不同文件夹。

> **TL;DR**：`scan → clean-titles → 联网搜索→ classify_plan.json → dry-run确认 → move → index → undo(如需)`。29 个 CLC 类目，多格式合并，作者归档，自动去重，支持增量扫描和回滚。

## 触发器

用户说类似的话时激活：
- "帮我整理电脑上的电子书"
- "把未整理的书籍分类归类"
- "整理 F:\xxx 里的电子书"
- "帮我按分类整理图书"
- "归类一下那些下载的电子书"

## 工作流

### Step 1: 确认目标目录

确认用户想整理的目录路径。如果用户未指定，询问目录位置。
常见的路径参考：
- `F:\图书馆\未整理`
- `F:\图书馆`
- `C:\Users\<用户名>\Downloads`

### Step 2: 扫描电子书文件

调用 `scripts/ebook_ops.py scan` 扫描目标目录：

```bash
python <skill_dir>/scripts/ebook_ops.py scan "<target_directory>" -o scan_result.json
```

**增量模式**（适用于后续新增书籍后的再次整理）：

```bash
python <skill_dir>/scripts/ebook_ops.py scan "<target_directory>" -o scan_result.json --incremental
```

增量模式会读取 `.library_state.json`，只返回上次扫描后新增或变更的文件，避免重复处理。

用 `<skill_dir>` 替换为 skill 的实际路径 `~/.hermes/skills/jw-ebook-organizer`。

输出是一个 JSON 文件，包含每个文件的 `filename`、`extension`、`absolute_path`、`size_mb` 等字段。
读取 `scan_result.json` 了解总文件数和具体文件列表。

### Step 3: 书名清洗 + 联网查询分类

#### 3a. 清洗书名

文件名中通常夹杂作者、出版社、来源站点（Z-Library）等噪音。先清洗出干净的书名：

```bash
python <skill_dir>/scripts/ebook_ops.py clean-titles scan_result.json -o cleaned_result.json
```

读取 `cleaned_result.json`，每条记录包含 `clean_title` 字段，即提取后的纯书名。

**检查点**：抽样 5-10 本书的清洗结果，确认 `clean_title` 准确。如有明显错误（书名被截断/噪声残留），调整清洗规则后重新运行 `clean-titles`。

**清洗规则（内置在 `clean_book_title()` 中）**：
- `《聪明的投资者》` → `聪明的投资者`（书名号内的内容优先）
- `聪明的投资者.mobi` → `聪明的投资者`（去掉扩展名）
- `聪明的投资者 (本杰明·格雷厄姆著) (Z-Library).epub` → `聪明的投资者`（去掉作者和来源标记）
- `巴菲特股票投资策略(高清).pdf` → `巴菲特股票投资策略`（去掉"高清"等版本描述）
- `三体全集（套装共3册）.epub` → `三体全集`（去掉套装信息）

#### 3b. 联网查询分类 + 作者国籍

> **注意**：在进行分类前，先加载 `references/clc-categories.md` 获取完整的 CLC 分类表。

逐个（或分批）对清洗后的书名进行联网搜索，查证该书的**学科归属**和**作者国籍**。

**批量说明**：若文件数 > 50，建议分批搜索（每批 20-30 本），告知用户预计搜索次数和耗时；若文件数 > 200，在开始前询问用户是否确认执行全量搜索。

**分类依据**：采用中国图书馆图书分类法（CLC/中图法）。

**搜索策略**：
- 优先搜索出版社官网、豆瓣读书、京东图书、当当等图书信息站点
- 搜索关键词示例：`"<书名>" 豆瓣` 或 `"<书名>" 作者`
- 从搜索结果中提取：该书属于哪个分类 + 作者全名 + 作者国籍
- 同名书籍通过作者信息区分（文件名中一般保留作者名）

**LLM 批量推断模式**（适用于 > 100 本的大规模整理）：
- 对书名明确的经典著作，直接使用 LLM 内在知识判断分类和作者
- 仅对冷门书籍或同名歧义的书进行联网搜索确认
- 将 clean_title 列表分批提交给 LLM，以此格式输出：
  ```
  序号 | 书名 | CLC代码 | 作者 | 国籍
  ```
- 可大幅减少搜索次数（从 N 次搜索降到 ~N/5 次）

**搜索产出**：每条记录应包含以下字段：

| 字段 | 说明 | 示例 |
|------|------|------|
| `clean_title` | 清洗后的书名 | `聪明的投资者` |
| `author` | 作者全名 | `本杰明·格雷厄姆` |
| `nationality` | 作者国籍 | `美国`（用国旗可识别的完整国名） |
| `target_filename` | 目标文件名（见下方格式） | `聪明的投资者-美国·本杰明·格雷厄姆.mobi` |
| `clc_category` | CLC 分类文件夹名 | `F83-金融投资` |

**目标文件名格式**：
```
{clean_title}-{nationality}·{author}.{extension}
```

示例：
| 原始文件名 | 目标文件名 |
|-----------|-----------|
| `聪明的投资者.mobi` | `聪明的投资者-美国·本杰明·格雷厄姆.mobi` |
| `三体全集.epub` | `三体全集-中国·刘慈欣.epub` |
| `国富论.pdf` | `国富论-英国·亚当·斯密.pdf` |

> 特殊处理：作者为国人的（中国），国籍标注 `中国`；作者不明或搜索不到国籍的，仅保留 `书名-作者` 形式；完全查不到作者信息的，不重命名。

**分类依据**：采用中国图书馆图书分类法（CLC/中图法）。详见 `references/clc-categories.md`。

**输出分类计划 JSON**，新版格式（含重命名信息）：

```json
{
  "target_directory": "F:\\图书馆",
  "rename": true,
  "categories": {
    "F83-金融投资": [
      {
        "filename": "聪明的投资者.mobi",
        "absolute_path": "F:\\图书馆\\未整理\\聪明的投资者.mobi",
        "clean_title": "聪明的投资者",
        "author": "本杰明·格雷厄姆",
        "nationality": "美国",
        "target_filename": "聪明的投资者-美国·本杰明·格雷厄姆.mobi"
      }
    ],
    "F83-证券交易": [...]
  }
}
```

> 如果 `target_filename` 不指定或为空，则保留原始文件名。

**move 命令的智能处理逻辑**（自动执行，无需手动配置）：

| 场景 | 处理方式 |
|------|---------|
| 同一书名 + 2+ 个文件（多种格式） | 自动放入 `{书名-作者}/` 子文件夹，每种格式独立存放 |
| 同一书名 + 仅 1 个文件（单一格式） | 直接放在分类根目录，不建书籍子文件夹 |
| 同分类 + 同作者 + 2+ 本书 | 自动放入 `{作者}/` 子文件夹，作者下再按书名分 |
| 无作者信息 | 直接放在分类根目录 |
| 目标路径 + 文件大小均相同 | **去重**：仅保留一份，跳过重复项 |
| 目标路径相同 + 文件大小不同 | **自动加后缀**：`巴菲特传_1.pdf`、`巴菲特传_2.pdf` |

**最终目录层级**：`{分类}/{作者(可选)}/{书名(可选)}/{文件}`

**目录结构示例**（整理后）：

```
F:\图书馆\
├── F83-金融投资\
│   ├── 国富论-英国·亚当·斯密.pdf
│   └── 本杰明·格雷厄姆\
│       └── 聪明的投资者-本杰明·格雷厄姆\
├── B84-心理学\
│   └── 但斌\
└── I24-小说\
    └── 刘慈欣\
```

> 完整的目录结构示例详见 `references/directory-structure.md`。

将分类计划保存为 `classify_plan.json`。

### Step 4: 展示并确认

读取分类计划并展示给用户：

1. **按类别列出** 每个类别有多少本书
2. **总文件数** 和 **类别数量**
3. **问用户是否确认** 执行整理

如果用户要求调整（修改分类、重命名类别、排除某些文件等），修改 `classify_plan.json` 后重新展示。

**在展示给用户之前**，必须执行一次 `--dry-run` 预览：

```bash
python <skill_dir>/scripts/ebook_ops.py move classify_plan.json --dry-run
```

读取 dry-run 输出并与分类计划交叉验证，确保文件路径和**重命名后的文件名**正确。dry-run 结果中 `"STATUS": "DRY_RUN"` 的每条记录的 `to` 字段即为目标路径，应包含重命名后的文件名。

### Step 5: 执行整理

获得用户确认后，执行移动操作。脚本会根据每条记录中的 `target_filename` 自动重命名文件，同时执行多格式合并、作者归档、去重等智能逻辑：

```bash
# 默认模式（移动文件）
python <skill_dir>/scripts/ebook_ops.py move classify_plan.json

# 复制模式（先复制，源文件改为 .source 后缀，更安全）
python <skill_dir>/scripts/ebook_ops.py move classify_plan.json --copy
```

**安全回滚**：每次 move 会在目标目录生成 `.move_manifest.json`，记录了每个文件从哪搬到哪。如果需要撤销：

```bash
# 预览撤销效果
python <skill_dir>/scripts/ebook_ops.py undo --dry-run

# 执行撤销
python <skill_dir>/scripts/ebook_ops.py undo
```

**联网搜索缓存**：Step 3b 搜索时，优先检查是否已搜索过同一书名（clean_title）。将搜索结果缓存到 `search_cache.json`，避免对同书不同格式重复搜索。

### Step 6: 生成图书索引

整理完成后，自动扫描归类后的目录，生成一份 Markdown 格式的**图书索引文档**：

```bash
python <skill_dir>/scripts/ebook_ops.py index "<target_directory>" --output "图书索引.md"
```

索引文档内容示例：

```markdown
# 电子书索引

> 生成时间: 2026-05-10 09:00  |  总藏书: 308 本  |  总大小: 8.5 GB  |  覆盖 8 个分类

---

## F83-金融投资  (42 本 / 856 MB)

| # | 书名 | 作者 | 格式 | 大小 |
|---|------|------|------|------|
| 1 | 聪明的投资者 | 本杰明·格雷厄姆(美国) | pdf | 5.2 MB |
| 2 | 国富论 | 亚当·斯密(英国) | pdf | 3.1 MB |

## B84-心理学  (5 本 / 12.8 MB)

### 但斌  (2 本 / 5.0 MB)
| # | 书名 | 格式 | 大小 |
|---|------|------|------|
| 1 | 巴菲特传 | pdf | 1.0 MB |
| 2 | 价值投资 | pdf | 4.0 MB |

### (根目录)  (3 本 / 7.8 MB)
| # | 书名 | 作者 | 格式 | 大小 |
|---|------|------|------|------|
| 1 | 乌合之众 | 古斯塔夫·勒庞(法国) | mobi | 0.8 MB |
...

## 附录：格式分布

| 格式 | 数量 |
|------|------|
| pdf | 88 |
| epub | 92 |
| mobi | 77 |
```

索引文档保存在整理目录的根目录（即 `<target_directory>` 下），方便随时查阅。

### Step 7: 安全收尾

- 删除临时文件（`scan_result.json`、`cleaned_result.json`、`classify_plan.json`）
- 提示用户已整理完成，并告知索引文档位置
- 如果使用了 `--copy` 模式，提示用户「源文件已标记为 `.source` 后缀，确认无误后可运行 `clean-source` 清理」

### 后整理：Z 文件夹精细化

整理结束后，`Z-综合性图书/` 文件夹中可能堆积了未能自动分类的书籍。按以下步骤处理：

1. 使用 `ebook_ops.py scan "Z-综合性图书" -o z_files.json` 扫描 Z 目录
2. 用 LLM 逐批推断 Z 中每本书的 CLC 分类
3. 手动将文件移动到正确分类目录
4. 重新运行 `ebook_ops.py index` 更新索引

### 后整理：清理 .source 标记文件

使用 `--copy` 模式后，源文件被改为 `.source` 后缀。确认整理结果无误后：

```bash
# 预览要删除的 .source 文件
python <skill_dir>/scripts/ebook_ops.py clean-source "<目标目录>" --dry-run

# 确认后执行删除
python <skill_dir>/scripts/ebook_ops.py clean-source "<目标目录>"
```

## 技术参考

### 脚本命令速查

```bash
SKILL_DIR="$HOME/.hermes/skills/jw-ebook-organizer"

# 扫描
python "$SKILL_DIR/scripts/ebook_ops.py" scan "<目录>" -o scan_result.json
python "$SKILL_DIR/scripts/ebook_ops.py" scan "<目录>" -o scan_result.json --incremental

# 清洗
python "$SKILL_DIR/scripts/ebook_ops.py" clean-titles scan_result.json -o cleaned_result.json

# 移动（预览 / 执行 / 复制）
python "$SKILL_DIR/scripts/ebook_ops.py" move classify_plan.json --dry-run
python "$SKILL_DIR/scripts/ebook_ops.py" move classify_plan.json
python "$SKILL_DIR/scripts/ebook_ops.py" move classify_plan.json --copy

# 撤回
python "$SKILL_DIR/scripts/ebook_ops.py" undo --dry-run
python "$SKILL_DIR/scripts/ebook_ops.py" undo

# 索引
python "$SKILL_DIR/scripts/ebook_ops.py" index "<目录>" --output "图书索引.md"
```

### 临时文件清单

| 文件 | 生成于 | 何时清除 |
|------|--------|---------|
| `scan_result.json` | Step 2 | Step 7 |
| `cleaned_result.json` | Step 3a | Step 7 |
| `classify_plan.json` | Step 3b | Step 7 |
| `search_cache.json` | Step 3b | 手动清除（保留可加速后续整理） |
| `.library_state.json` | scan --incremental | 保留（增量扫描依赖） |
| `.move_manifest.json` | move | 保留（undo 依赖） |
| `图书索引.md` | Step 6 | 保留（最终交付物） |

**操作原则**：
1. **强烈建议先在 dry-run 模式验证**，确认分类正确后再执行实际移动
2. 同名文件冲突时，脚本会自动添加数字后缀（`书名_1.pdf`）
3. 操作范围限定在用户指定的目录内，不会触及系统目录
4. 如果用户只想复制而不是移动，在 Step 5 询问用户意见

## Anti-Patterns（强制阅读）

1. **跳过dry-run**：直接执行move命令，导致文件移动错误无法回滚
2. **手动移动文件**：不使用脚本而手动移动，破坏目录结构和索引一致性
3. **忽略搜索缓存**：对同一书名重复联网搜索，浪费时间和API配额
4. **批量处理不确认**：文件数>200时未询问用户确认，直接执行全量搜索
5. **不清洗书名**：直接使用原始文件名分类，导致分类不准确（作者名、出版社信息干扰）

## Pre-Delivery Checklist（交付前检查）

在完成整理后，必须验证以下项目：

- [ ] 所有文件已成功移动（无错误文件）
- [ ] 索引文档已生成且内容正确
- [ ] 无重复文件（同一书名的多个副本）
- [ ] 分类正确（抽样检查 5-10 本）
- [ ] 文件名格式符合规范（书名-国籍·作者.扩展名）
- [ ] 目录结构符合预期（分类/作者/书名）
- [ ] 临时文件已清理（scan_result.json 等）
- [ ] 用户确认整理结果

## 异常与边界条件

| 场景 | 处理方式 |
|------|---------|
| 扫描目录为空（0 个文件） | 告知用户「未找到电子书文件」，检查路径和 `--ext` 参数，退出 |
| 联网搜索无结果（查不到这本书） | 回退到 CATEGORY_KEYWORDS 关键词匹配推断；全无匹配则归 Z-综合性图书 |
| 联网搜索返回多个矛盾分类 | 取出现频次最高的 2 个结果，用 LLM 判断最优；无法判断时选第一结果 |
| 文件名清洗后为空 | 保留原始文件名 stem 作为 `clean_title`，标记 `清洗失败:使用原名` |
| 目标目录权限不足（写入被拒） | 报告具体失败文件路径，建议用户以管理员身份运行或更换目标目录 |
| `classify_plan.json` 格式错误 | 提示具体格式问题（哪些字段缺失），要求重新生成 |
| Step 5 移动中部分文件失败 | 不中断全部流程，统计 errors 并在报告中列出失败项 |
| 移动后源文件路径出现 `.source` 标记文件 | 属于 `--copy` 模式正常产物，提示用户确认后手动删除 |

**增量模式特别说明**：
- `.library_state.json` 不存在时，`--incremental` 降级为全量扫描
- state 文件与目录结构不一致（如目录重命名），增量扫描降级为全量

**后整理重分类**：
- 整理完成后想修改某本书的分类 → 手动将文件移到正确的 CLC 目录下，然后重新运行 `ebook_ops.py index` 生成索引
- 如果大面积分类错误 → 重新运行 `ebook_ops.py undo` 恢复后，修改 `classify_plan.json` 再执行

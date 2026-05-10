---
name: ebook-organizer-jw
description: This skill should be used when the user wants to organize, sort, classify, or tidy up ebook files (pdf/epub/mobi/azw3) on their computer into category folders. 触发词：整理电子书、归类电子书、图书分类、整理本地图书、电子书归档。It handles scanning a directory for ebook files (including incremental mode), cleaning messy filenames, performing web searches to determine each book's CLC subject area and author, classifying into a multi-level CLC hierarchy (29 subcategories), moving files with multi-format merging and author grouping, generating a human-readable Markdown index, and providing undo/rollback support. Do not use for non-ebook files (images, documents, audio).
agent_created: true
---

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

用 `<skill_dir>` 替换为 skill 的实际路径 `C:\Users\rancb\.workbuddy\skills\ebook-organizer-jw`。

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

**参考分类表**（29 个 CLC 多级类目，重点展开 F/B/K/I 大类）：

| CLC 代码 | 文件夹名 | 典型书籍主题/关键词 |
|----------|---------|-------------------|
| B0 | `B0-哲学理论` | 哲学理论、本体论、认识论、辩证法 |
| B1 | `B1-西方哲学` | 亚里士多德、柏拉图、康德、尼采、黑格尔 |
| B2 | `B2-中国哲学` | 论语、王阳明、儒家、道家、禅宗、周易 |
| B80 | `B80-思维科学` | 底层逻辑、方法论、心智模型、系统思考、批判性思维 |
| B84 | `B84-心理学` | 乌合之众、社会心理、认知偏误、同理心、自控 |
| B9 | `B9-宗教` | 佛教、基督教、伊斯兰教、信仰 |
| C | `C-社会科学总论` | 社会学、统计学、社交、沟通、谈判、影响力 |
| C93 | `C93-管理学` | 管理理论、领导力、德鲁克、明茨伯格 |
| D | `D-政治法律` | 政治、法律、政府治理、社会制度、乡村政治 |
| F0 | `F0-经济学` | 经济学原理、曼昆、凯恩斯、宏观、微观 |
| F1 | `F1-中国经济` | 林毅夫、黄奇帆、双循环、改革、现代化 |
| F2 | `F2-经济管理` | 竞争战略、波特、商业模式、创业、创新 |
| F7 | `F7-贸易` | 贸易经济、外贸、跨境电商、全球化 |
| **F81** | **`F81-财政金融`** | **财政、货币、银行、债券、利率、汇率** |
| **F83** | **`F83-金融投资`** | **巴菲特、价值投资、股票、基金、财报、护城河、复利** |
| **F83** | **`F83-证券交易`** | **K线、技术分析、价格行为、外汇、短线、缠论、量化** |
| F84 | `F84-保险` | 保险、社保、养老、寿险 |
| G | `G-文化教育` | 文化研究、教育、阅读、写作、传媒 |
| H | `H-语言文字` | 语言学、汉语、英语、语法、修辞 |
| **I24** | **`I24-小说`** | **三体、追风筝的人、围城、科幻、武侠、推理** |
| I26 | `I26-散文` | 散文、随笔、瓦尔登湖 |
| I | `I-文学` | 诗歌、文学理论、戏剧、文学史 |
| **K0** | **`K0-史学理论`** | **史学理论、历史哲学** |
| **K1** | **`K1-世界史`** | **世界史、欧洲史、文明史** |
| **K2** | **`K2-中国史`** | **中国史、八次危机、革命史、制度史** |
| K81 | `K81-传记` | 人物传记、自传、回忆录 |
| R | `R-医药卫生` | 医学、健康、营养、中医、养生 |
| TP | `TP-计算机技术` | 编程、AI、Python、算法、架构 |
| Z | `Z-综合性图书` | 百科全书、手册、**无法归类的书籍** |

> 中图法基本大类（全）：A 马列主义 | B 哲学 | C 社科总论 | D 政治法律 | E 军事 | F 经济 | G 文教 | H 语言 | I 文学 | J 艺术 | K 历史地理 | N 自科总论 | O 数理化学 | P 天文 | Q 生物 | R 医药 | S 农业 | T 工业技术 | U 交通 | V 航空 | X 环境 | Z 综合

**分类原则（依中图法精神）：**
- 优先通过联网搜索确认图书的学科分类
- 按图书内容的**学科属性**归类，而非按用途或个人偏好分类
- 《聪明的投资者》→ F83 金融投资（证券投资），而非归入"自助"类
- 《竞争优势》→ F2 经济管理（企业竞争战略）
- 系列套书按套装的主题归入最合适的单一类别
- 多学科交叉的书籍，选择其**主要论述方向**归类
- 联网搜索也查不到明确分类的，用 LLM 基于书名关键词做最佳匹配推断
- 实在无法分类的（包括网络搜索无结果且关键字无法匹配的），归入 `Z-综合性图书`

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
│   ├── 国富论-英国·亚当·斯密.pdf               ← 单格式，放根目录
│   └── 本杰明·格雷厄姆\                         ← 作者(多书)→子文件夹
│       └── 聪明的投资者-本杰明·格雷厄姆\         ← 多格式→子文件夹
│           ├── 聪明的投资者-美国·本杰明·格雷厄姆.epub
│           ├── 聪明的投资者-美国·本杰明·格雷厄姆.mobi
│           ├── 聪明的投资者-美国·本杰明·格雷厄姆.pdf
│           └── 聪明的投资者-美国·本杰明·格雷厄姆_1.pdf  ← 不同版本
├── F83-证券交易\
│   └── 裸K线交易法-中国·许佳聪.pdf              ← 单格式，根目录
├── B84-心理学\
│   └── 但斌\                                    ← 作者(2书)→子文件夹
│       ├── 巴菲特传-中国·但斌.pdf
│       └── 价值投资-中国·但斌.pdf
└── I24-小说\
    └── 刘慈欣\                                  ← 作者(多书)→子文件夹
        ├── 三体-中国·刘慈欣/
        │   ├── 三体-中国·刘慈欣.epub
        │   └── 三体-中国·刘慈欣.pdf
        └── 流浪地球-中国·刘慈欣.pdf

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
# 完整路径（替换 <skill_dir> 为此目录）
SKILL_DIR="C:\Users\rancb\.workbuddy\skills\ebook-organizer-jw"

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

# 清理 .source
python "$SKILL_DIR/scripts/ebook_ops.py" clean-source "<目录>" --dry-run
python "$SKILL_DIR/scripts/ebook_ops.py" clean-source "<目录>"

# 报告 & 索引
python "$SKILL_DIR/scripts/ebook_ops.py" report "<目录>" -o report.json
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

1. **强烈建议先在 dry-run 模式验证**，确认分类正确后再执行实际移动
2. 同名文件冲突时，脚本会自动添加数字后缀（`书名_1.pdf`）
3. 操作范围限定在用户指定的目录内，不会触及系统目录
4. 如果用户只想复制而不是移动，在 Step 5 询问用户意见

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

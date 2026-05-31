# 已知书籍结构模式

本文件记录 jw-content-summary 处理过的特殊文本结构，供后续遇到类似结构时快速诊断。

---

## 多册合集 + 章节标题重复（巴菲特致股东的信）

**结构特征**:
- 一本书含两册（或多册）内容，合并在一个文件中
- 前半部分为第一册的目录（TOC）区，含所有章节标题但正文极少（每个章节文件 <500 字节）
- 后半部分为第二册的正文，章节编号与前半相同（都是"第1章"、"第2章"...）
- 示例：巴菲特致股东的信（5234行），第1-856行是第一册（含目录），第858行开始是第二册正文

**诊断方式**:
```bash
# 检查章节文件大小，TOC artifact 的章节文件 <500 字节
wc -c chapters/*.txt | sort -n | head
```

**修复方案**:
```python
# 方案A：过滤正文量极少的章节（推荐）
if len(body) < 50:
    continue

# 方案B：如果所有章节都重复，用专用解析器
# 见 scripts/buffett-letters-parser-v3.py
# 策略：找所有"第X章"标题，确定正文起始点（跳过目录区）
# 对于巴菲特：正文从第二册第1章（line 858）开始
```

**验证**:
```bash
# 修复后检查：每个章节文件 >5KB
wc -c chapters/*.txt | awk '$1 < 5000 {print "TOO SMALL: " $0}'
```

---

## 纯字符切分书籍（无逻辑章节结构）

**结构特征**:
- 书籍无目录（TOC）标记，章节标题不存在或不可机器识别
- `build_book_index.py` 按字符数固定切分（如每 5000 字一块）
- 章节名为 `Chunk 1`、`Chunk 2` 等，而非真实章节标题
- `book-index.json` 中 `chapter_count` 是切分块数，非真实章数
- 每个章节文件正文内容完整（5-14KB），只是命名无语义

**诊断方式**:
```python
# 特征1: chapters/*.txt 文件大小正常（5-14KB），不是TOC artifact
# 特征2: 章节标题全是 "Chunk N"，无真实章节目录
# 特征3: total_chars / chapter_count ≈ 5000（固定切分）
# 示例: 93,517 / 19 ≈ 4,922字/块
```

**处理方式**:
- 书籍类型判断仍按内容特征（散文/随笔集 → insight + principle 优先）
- extractor 路由不受影响：散文/随笔集类型本身采用全局提取（模式 A）
- 阶段 1 可跳过（书结构简单，无多册合集）
- 进度报告不受影响：`candidate_count` 仍为子代理提取的有效单元数

**示例**:
- 查理·芒格的投资思想（93,517字，19个 `Chunk N`，无真实目录）

---

## 超长单目录 + 单主体章节（目录占位，正文集中在末章）

**结构特征**:
- 书籍有完整目录页（TOC），列出了所有章节标题
- 但目录区段极长（占全部章节条目的80-100%），实际正文几乎全部集中在最后一章
- `structure_type: toc_filtered`，`toc_ratio: 1.0`（全部目录章节都被过滤）
- 章节文件 ch002-ch009 全部 <500 字节（只有标题，无正文）
- 末章（ch010）承载 99%以上内容，文件 >500KB
- `total_chars/chapter_count` 比值严重失真（看似均匀，实则极不均匀）

**示例**:
- 《价值：我对投资的思考》（张磊，2020）：650KB全书，9个目录章节全部占位，末章ch010承载637KB

**诊断方式**:
```bash
# 检查章节文件大小分布
ls -la chapters/*.txt | awk '{print $5, $9}' | sort -n

# TOC artifact: 多个文件 <500 字节，单个文件 >500KB（末章）
```

**处理方式**:
- 阶段 1 可跳过（书籍结构简单，主体单一）
- extractor 按 `book_type_hint` 决定：essay_collection → insight + principle 优先，其他轻量
- 阶段 2 直接对内容主体章节（ch010）全量运行，无需分块
- 预处理输出的 `chapters/` 目录中大部分文件是 TOC artifact，不影响最终质量（ch010 包含全量正文）

**已记录书籍**:
- 《价值：我对投资的思考》（张磊，2020）

---

## 中等 TOC 污染（章节数 >15，toc_ratio 0.1~0.3，章节大小两极分化）

**结构特征**:
- `structure_type: chapters`（非 toc_filtered，未达到 >30% 过滤阈值）
- `toc_ratio: 0.1~0.3`（少量 TOC 条目混入正文，未触发过滤）
- 章节数 >15（不满足阶段 1 跳过条件的数量标准）
- 文件大小**两极分化**：30-50% 章节 <500 字节（TOC 标题行），其余章节 1KB-40KB 不等
- 有效章节约为总章节数的 30-50%（其余为 TOC 占位）
- `total_chars / chapter_count` 比值失真（≈2600，实际有效章节承载 >95% 内容）

**示例**:
- 《聪明的投资者》（本杰明·格雷厄姆，1949/1971）：68 章，toc_ratio=0.186，有效内容约 20 章

**诊断方式**:
```bash
# 检查章节文件大小分布
ls -la chapters/*.txt | awk '{print $5, $9}' | sort -n

# 中等污染：30-50% <500字节（TOC），其余文件1KB-40KB不均匀分布
# 对比：纯 TOC 污染（>30% <500字节）会触发 toc_filtered
# 对比：正常书籍全部 >1KB
```

**处理方式**:
- 阶段 1 可跳过（但需在审计记录中注明争议原因——章节数>15但主题均匀）
- 有效章节 = char_count > 1000 的章节（过滤 TOC 条目）
- extractor 只读取有效章节，跳过 <500 字节的 TOC 文件
- 书籍类型判定按内容特征（本模式常见于方法论专著或散文集）

**与超长单目录模式的区别**:
| | 超长单目录 | 中等 TOC 污染 |
|---|---|---|
| toc_ratio | ≈1.0 | 0.1~0.3 |
| structure_type | toc_filtered | chapters |
| 内容分布 | 99%在末章 | 分散在 30-50% 的章节中 |
| 处理 | 直接读主体章节 | 过滤 TOC 后读取有效章节 |

---

## build_book_index.py 输出异常（路径漂移 + chapter_id 乱序）

**结构特征**:
- `book-index.json` 输出到 `cleaned_text/` 子目录而非书根目录
- `chapter_id` 全为 null（脚本未正确写入）
- 章节顺序按文件名字母排序（如 ch001="第八章"，ch002="第一章"），而非书中实际章号顺序
- `chapter_count` 和 `total_chars` 可能仍然准确，但后续阶段若依赖 `book-index.json` 的 chapter_id 或顺序会出错

**根因（两种场景）**:
1. **场景 A：传了 cleaned_text.txt** —— `build_book_index.py` 用 `src.stem` 作为输出目录名。传 `cleaned_text.txt` 时 `stem` 为 "cleaned_text"，输出漂移到 `books/cleaned_text/`。**修复：必须传原始 `.md`/`.txt` 路径，脚本内置自动清洗。**
2. **场景 B：章节编号不统一** —— 脚本按 `os.listdir()` 字母序写入章节，源文件章节编号格式不统一（"第一章"、"第1章"、"ch01"混用），导致排序结果与书中顺序不符。

**回退流程（已验证有效）**:
1. **场景 A 修复**：删除 `books/cleaned_text/`，用原始源文件路径重跑：`build_book_index.py <原始.md或.txt路径> books/`
2. **场景 B 修复**：跳过有问题的 `book-index.json`，直接读 `chapters/` 目录
3. 用 `head -1` 取每章第一行，手动匹配真实章号
3. 重建 book-index.json（或直接在后续流程中按文件名顺序+人工确认处理）
4. ch010/ch011 < 500字节的碎片：与 TOC artifact 不同，这是 PDF 转换时同一标题被重复切分两次产生的"双胞胎碎片"，直接排除

**验证检查**:
```bash
# 正常书籍章节文件应 >1KB；<500字节 = 碎片
ls -la chapters/*.txt | awk '$5 < 500 {print "FRAGMENT: " $0}'

# 正常书籍章节顺序：前3个文件应为书的第1-3章
for f in chapters/ch001.txt chapters/ch002.txt chapters/ch003.txt; do
    head -1 "$f"
done
```

**已知受影响书籍**:
- 《巴菲特之道》（罗伯特·哈格斯特朗，2015）：8个有效章节，但 ch001="第八章"，ch010/ch011 为"第八章"碎片

---

## 超长章节重复（PDF 转换产物）

**结构特征**:
- 章节文件中存在两个相邻超长章节（>100KB），大小几乎完全相同
- 疑似 PDF 转文本时同一页被切分两次，导致内容完全重复
- `book-index.json` 的 `total_chars` 会将重复内容计入，使字数统计虚高
- 正常书籍单章节很少超过 100KB

**示例**:
- 《彼得林奇投资经典全集》：ch027 和 ch028 各 ~130k，内容疑似重复

**诊断方式**:
```bash
# 找出 >100KB 的章节
ls -la chapters/*.txt | awk '$5 > 100000 {print $5, $9}' | sort -n


# 检查两个超大文件是否内容重复
diff chapters/ch027.txt chapters/ch028.txt | head -20
```

**处理方式**:
- 若确认重复，保留其中一个（如 ch027），删除重复章节（如 ch028）
- 从源文件重新切分时注意重复边界检测
- `total_chars` 需要重新统计（减去重复部分）

**已记录书籍**:
- 《彼得林奇投资经典全集》（Peter Lynch）：ch027 ≈ ch028 ≈ 130k

---

## 章节标题双重命中（TOC与正文使用相同格式）

**结构特征**:
- 书的目录（TOC）和正文中**使用完全相同的章节标题格式**，如 `"01 为什么投资要研究周期？"`
- `build_book_index.py` 的章节标题正则 `^\d{2} (.+)` 在文件中**匹配到两处**：
  - 第1处：TOC 区（文件开头，多个相邻章节标题连续排列，中间无正文）
  - 第2处：正文区（文件中后部，每条标题前后各有空白行）
- 脚本取第1处（TOC），导致所有 `chapter_id` 内容为空/极短（实际正文在第2处）
- 章节总数可能仍然"正确"（如18章），但章节内容几乎全为0字符

**诊断方式**:
```python
# 对每一章标题，在整个文件中搜索它的所有出现位置
for i, line in enumerate(lines):
    if line.strip() == '为什么投资要研究周期？':
        print(f"Found at line {i+1}, prev: {repr(lines[i-1][:20])}, next: {repr(lines[i+1][:20])}")
# 若同一标题出现多次且周围都是空白行，说明是 TOC 重名
```

```bash
# 章节文件全部 0 字符或极小，但 book-index.json 报告了章节数
ls -la chapters/*.txt | awk '{print $5, $9}' | sort -n | head
```

**根因**: 脚本按文件顺序匹配章节标题，正文标题与 TOC 标题格式完全相同，但正文标题在文件后部，TOC 标题在前部，TOC 被先匹配。

**典型场景**:
- 书籍目录在文件开头（常见）
- 正文在目录之后（常见）
- **但目录和正文标题格式完全相同且均为 `"01"` 两位数字开头**（本 Case 独有）
- 更关键：目录中的章节标题**没有前后空白行隔开**（连续排列），而正文标题**前后有空白行**（这是两者的结构差异）

**《周期》实测诊断**:
```
Lines 20-22: '01 为什么投资要研究周期？' → next line is '\n' (blank) → TOC entry
Lines 296: '为什么投资要研究周期？' → prev line is '\n' (blank) → real heading
两者格式不同：目录是 "01 标题"，正文是 "标题"（无数字编号）
```

**回退流程（已验证有效）**:
1. 搜索每一章标题在文件中的**所有**出现位置
2. 通过前后空白行上下文判断哪个是真实正文标题（标题前后各有一行空白行）
3. 记录所有真实标题的**行号（0-indexed）**
4. 用真实行号重建 `book-index.json` 和 `chapters/` 文件
5. 手动删除错误创建的 `chapters/` 内容，从真实行号重新切分

**已知受影响书籍**:
- 《周期》（霍华德·马克斯，2019）：TOC在 lines 21-55，正文从 line 296 开始

---

## 章节标题双重命中变体：TOC标题捕获前言内容（非空章节）

**结构特征**:
- 书籍格式：Markdown（`.md`）或 TXT 均可，文档的章节标题格式在 TOC 区和正文区完全相同（如"第1章　公司治理"）
- 脚本按文件顺序匹配章节标题，**TOC 区的标题被优先匹配**
- 但该 TOC 标题**后面紧跟着大量正文**（译者序、前言、推荐序、导言等），而非空白行或极短内容
- 结果：生成一个**标题错误但内容充实**的章节（如 ch009="第9章　税务问题"，内容 90KB 实为序言）
- 后续 ch010-ch018 才是真正的第1-9章正文
- 与"章节标题双重命中"模式的关键区别：

| 特征 | 标准双重命中（《周期》模式） | 本变体（巴菲特信件） |
|---|---|---|
| TOC匹配结果 | 空/极短（<100字符） | 大段正文（~90KB） |
| 内容来源 | TOC 行仅有标题 | TOC 标题+后续前言全量内容 |
| 诊断方式 | 章节文件几乎空 | 章节文件 >50KB，但标题错配 |
| 对阶段 1 影响 | 易发现（空章节） | 易忽略（需要检查章节标题是否与内容匹配） |

**示例**:
- 《巴菲特致股东的信：投资者和公司高管教程》（沃伦·巴菲特，2018）：ch009 标题为"第9章　税务问题"但内容为译者序+推荐序+前言+开场白+导言（~90KB），实际第9章在 ch018

**诊断方式**:
```python
# 检查每个章节的前几行，确认标题与内容是否匹配
import os
for f in sorted(os.listdir('chapters/')):
    if not f.endswith('.txt'): continue
    with open(f'chapters/{f}') as fh:
        title = fh.readline().strip()
        body_start = fh.read(100).strip()[:50]
    print(f"{f}: title=\"{title}\" -> \"{body_start}...\"")
# 异常信号：title="第9章" 但 body 开头为"译者序"或"前言"
```

```bash
# 章节文件 >50KB 但标题序号与文件顺序不匹配
ls -la chapters/ch009.txt  # 大文件 (>50KB) 但标题是"第9章"
```

**处理方式**: 阶段 1 理解报告中注明章节错配。提取时 ch009 作为"序言/导言"处理（insight+principle 提取器），而非作为正文章节。真正对应标题的正文在后续章节（如 ch018 才是真正的"第9章　税务问题"）。

**已记录书籍**:
- 《巴菲特致股东的信：投资者和公司高管教程》（沃伦·巴菲特，2018）：ch009 序言内容，ch010-ch018 为真正第1-9章

---

## TOC 结构与 .md 源文件兼容性

**背景**: `build_book_index.py` 的章节标题正则兼容 Markdown 格式文件（`.md`）。源文件为 `.md` 或 `.txt` 均可，脚本使用 `read_bytes()` + 编码探测，不受后缀影响。

**处理**: 无需特殊转换，直接传入 `.md` 路径即可。

**检查清单**:
- [x] clean_text.py 正确处理 `.md` 文件（无额外 Markdown 语法干扰）
- [x] build_book_index.py 正确识别章节标题（`#` 前缀格式与纯文本格式均匹配）
- [x] chapters/*.txt 输出仍为纯文本格式（脚本统一输出为 `.txt`）

---

## 混合型结构：Letters + 年会Q&A（不用 build_book_index 切分）

**结构特征**:
- 书包含两种不同类型的内容：①巴菲特致股东/合伙人的信（Letters） ②股东大会问答实录（Q&A）
- 两种内容时间轴重叠（如"巴菲特致股东的信1995"和"股东大会实录1995"同时存在）
- `build_book_index.py` 的通用切分会把 Letters 当独立章节（ch001-ch057），Q&A 当独立章节（ch058-ch095），导致 chapter_count 膨胀到 259+，章节文件全变成 "Chunk N"
- 文件格式为纯文本，无 Markdown 标记

**典型案例**:
| 书名 | Letters | Q&A | 总字符 | build_book_index 输出 |
|---|---|---|---|---|
| 巴菲特致股东的信及伯克希尔股东大会实录 | 57封（1965-2025） | 38个 | 474万字 | 949 chapters（全错） |
| 巴菲特致合伙人+致股东的信全集 | 56封（1957-2021） | 0 | 129万字 | 259 chapters（全错） |

**识别方式**:
```bash
# 特征1: chapter_count 异常大（>50）且章节文件全是 "Chunk N"
# 特征2: cleaned_text.txt 中存在两类年份标题行
grep -E '巴菲特致(合伙人的信|股东的信)\s*[0-9]{4}' cleaned_text.txt | head -5
# 输出: "巴菲特致合伙人的信 1957", "巴菲特致股东的信 1965" → Letters 结构
```

**正确处理（REGEX 切分取代 build_book_index 切分）**:
```python
import re
with open('cleaned_text.txt') as f:
    lines = f.read().split('\n')

letters = []
for i, l in enumerate(lines):
    m = re.match(r'^巴菲特致(合伙人的信|股东的信)\s*(\d{4})', l.strip())
    if m:
        letters.append((i, m.group(1), m.group(2)))

by_type = {}
for _, ltype, year in letters:
    by_type[ltype] = by_type.get(ltype, 0) + 1
print('By type:', by_type)
# 输出: {'合伙人的信': 13, '股东的信': 43}
```

**Extractor 路由**:
- Letters（合伙人的信 + 致股东的信）→ principle / insight / boundary
- Q&A（股东大会实录）→ case / insight
- glossary → 重点（内在价值/安全边际/护城河等核心术语在各封 Letters 中反复出现）

**已知受影响书籍**:
- 《巴菲特致股东的信及伯克希尔股东大会实录》（12.9MB，57+38结构）
- 《巴菲特致合伙人+致股东的信全集》（3.4MB，56封 Letters，无 Q&A）

---

## 纯 Letters 结构书籍（全 Letters，无 Q&A）

**结构特征**:
- 纯信件合集，无 Q&A 内容
- 每封信有明确年份标题（"巴菲特致股东的信 YYYY"）
- build_book_index 可能把每封信切成多个 "Chunk N"（129万字 / 259 chunks），此时需 REGEX 重切

**判断条件（同时满足则全局提取）**:
1. build_book_index 输出 chapter_count 与实际信件数差距 >50%
2. grep 搜索无问答格式标记（无"问："、"答："、"Q:"、"A:"）
3. 每封信内容长度均衡（20-80KB）

**处理**: 按 REGEX 识别信件边界，从 cleaned_text.txt 提取候选写入 candidates/

---

## 通用验证脚本

```python
import os
import json

def diagnose_chapters(book_index_path, chapters_dir):
    """诊断章节文件大小异常（TOC artifact / 单主体章节）"""
    with open(book_index_path) as f:
        idx = json.load(f)

    print(f"total_chars: {idx['total_chars']}")
    print(f"chapter_count: {idx['chapter_count']}")
    print(f"structure_type: {idx.get('structure_type', 'unknown')}")
    print(f"toc_ratio: {idx.get('toc_ratio', 'N/A')}")
    print(f"book_type_hint: {idx.get('book_type_hint', 'unknown')}")
    print()

    sizes = []
    for ch in sorted(os.listdir(chapters_dir)):
        if ch.endswith('.txt'):
            size = os.path.getsize(os.path.join(chapters_dir, ch))
            sizes.append((ch, size))
            flag = " ← TOC artifact" if size < 500 else (" ← MAIN BODY" if size > 500000 else "")
            print(f"{ch:12s} {size:8d} bytes{flag}")

    small = [c for c, s in sizes if s < 500]
    large = [c for c, s in sizes if s > 500000]
    print(f"\nTOC artifacts: {len(small)} ({small})")
    print(f"Main body chapters: {len(large)} ({large})")
    if large and small:
        print("⚠️  Single main body chapter detected — check extractor routing")

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        diagnose_chapters(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python diagnose_chapters.py <book-index.json> <chapters/>")
```

---

## 第X部分结构（部分而非章节，build_book_index 检测不到子章节）

**结构特征**:
- 书籍以「第X部分」（part-level）而非「第X章」（chapter-level）组织
- `build_book_index.py` 的 `CHAPTER_PATTERNS` 正则匹配 `第...章` 但不匹配 `第...部分`
- 结果：检测到 2-3 个部分级标题作为章节，其中前 N-1 个被判定为 TOC 碎片（<500 字符），最后一个承载全书正文
- `structure_type: toc_filtered`，`toc_ratio: 1.0`，`fragmentation_ratio` 极高
- 内部子章节（如「泡沫阶段」「萧条阶段」「和谐的去杠杆化」等）未被脚本切分

**示例**:
- 《债务危机》（瑞·达利欧）：3 个部分，ch001/ch002 各 <100 字符（TOC 碎片），ch003 承载 373K 字符

**诊断方式**:
```bash
grep -n -E '^(第[一二三四五六七八九十]+部分)' cleaned_text.txt | head
# 输出：第X部分出现在文件前半部，后半部无
# 对比正常书籍：章节标题均匀分布
```

**阶段 1 处理**:
1. 用 `grep -n` 定位内部子章节标题（如「泡沫阶段」「顶部」「萧条阶段」「和谐的去杠杆化」等）的行号
2. 在 `stage1-understanding.md` 中按行号区间标注章节角色表（而非依赖 book-index.json 的章节 ID）
3. 角色表示例：
   ```
   | 行号 158-205 | 典型长期债务周期模型 | framework | ... |
   | 行号 206-561 | 典型通缩性债务周期 | framework | ... |
   ```

**阶段 2 处理**:
- 按阶段 1 的行号区间从 `cleaned_text.txt` 切分文本
- 每个 extractor 分配对应行号区间的文本（而非 `chapters/chXXX.txt`）
- 避免将 373K 字符的 ch003.txt 全量丢给 extractor

**已记录书籍**:
- 《债务危机》（瑞·达利欧，2026-05-28 处理）：3 个部分，ch003 合并全书正文

---

**运行**:
```bash
python diagnose_chapters.py books/价值：我对投资的思考/book-index.json books/价值：我对投资的思考/chapters/
```
# 阶段 2 输出陷阱与修复

本文件记录 jw-content-summary 阶段 2 常见的 delegate_task / candidates / extractor schema 问题。

主原则：阶段 2 子代理只负责发现候选；候选必须进入标准 extractor 文件，并通过 `scripts/validate_candidates.py` 后再聚类。

## 1. delegate_task tasks 嵌套 JSON 解析错误

### 症状

```text
Error: tasks must be a JSON array of task objects; received a string that could not be parsed as JSON
```

### 根因

当 `delegate_task` 的 `tasks` 数组内嵌在包含 `context` 字符串的字典中时，长 context 可能导致 tasks 数组被错误解析。

### 正确模式

```python
# 正确：tasks 是顶层数组
任务数组 = [
  {"goal": "...", "toolsets": ["terminal", "file"]},
  {"goal": "...", "toolsets": ["terminal", "file"]},
]
delegate_task(tasks=任务数组)
```

### 错误模式

```python
# 错误：不要把 tasks 包在外层 context 字段里
delegate_task(context="...", tasks=[{"goal": "..."}])
```

## 2. 子代理输出到章节 YAML，而非标准 extractor 文件

### 症状

子代理写出：

```text
candidates/ch004.yaml
candidates/ch005.yaml
```

而不是：

```text
candidates/frameworks.md
candidates/principles.md
candidates/cases.md
```

### 根因

子代理 goal 只给了 `candidates/` 目录，没有明确指定标准输出文件名。

### 识别

```bash
ls candidates/*.yaml
ls candidates/*.md
```

### 修复流程

1. 读取所有 `ch*.yaml`
2. 按 `type:` 字段分类
3. 追加到标准文件：
   - `frameworks.md`
   - `principles.md`
   - `cases.md`
   - `insights.md`
   - `boundaries.md`
   - `procedures.md`
   - `boundaries.md`
   - `glossary.md`
4. 再运行 `validate_candidates.py`
5. 校验通过后再运行 `cluster_candidates.py`

### 预防

在子代理 goal 中明确写：

```text
输出追加到 `/path/to/candidates/frameworks.md`，不要创建 chXXX.yaml。
```

## 3. YAML 字段名漂移

### 常见偏差

| 标准字段 | 错误输出 |
|---|---|
| `summary:` | `principle:` / `framework:` / `insight:` |
| `source_chapter:` | `chapter:` |
| `keywords:` | 缺失 |
| `v2_scenario:` | 缺失 |

### 检查方式

```bash
head -50 candidates/principles.md | grep -E '(summary:|principle:|chapter:|source_chapter:)'
python ~/.hermes/skills/jw-content-summary/scripts/validate_candidates.py candidates
```

### 修复原则

- 字段名必须严格匹配 extractor 模板。
- 能机械修复的字段名，先 patch candidates 文件。
- 若内容结构已经错乱，重新提取比手修更稳。

## 4. 子代理 prompt 防御

在 delegate_task 的 goal/context 中粘贴对应 extractor 模板的完整 YAML 示例，并加一句：

```text
输出字段名必须严格照此格式，不得更改；不得把 summary 改成 principle/framework/insight。
```

## 5. 聚类前硬顺序

阶段 2 收尾必须按这个顺序：

1. 确认 candidates 输出到标准 `.md` 文件
2. 运行 `validate_candidates.py`
3. 修复格式错误
4. 清理候选文件中的非候选标题行（见下方“Markdown 标题被聚类脚本误计为候选”）
5. 运行 `cluster_candidates.py`
6. 读取 clusters.json 的 `granularity`
7. 阶段 2 完成后直接进入阶段 3，全量展开所有 cluster。

不要跳过格式校验直接聚类。

## 6. Markdown 标题被聚类脚本误计为候选

### 症状

`validate_candidates.py --strict` 显示候选数正常，例如 48：

```text
"total_entries": 48,
"compliant": 48
```

但 `cluster_candidates.py` / `score_candidates.py` 多算 1-2 条，例如：

```text
candidate_count: 50
D: 2
```

低分候选类似：

```text
cases.md#cases-1 title: "case candidates"
boundaries.md#boundaries-1 title: "boundary candidates"
```

### 根因

候选文件开头存在：

```markdown
## case candidates
## boundary candidates
```

`validate_candidates.py` 会忽略标题行，但聚类/评分脚本可能把二级标题解析成伪候选，导致 D 级噪声。

### 修复

聚类前删除 candidates 文件中的纯展示标题行，候选文件只保留 YAML-ish 条目：

```python
from pathlib import Path
for p in Path("books/<书名>/candidates").glob("*.md"):
    text = p.read_text(encoding="utf-8")
    text = "\n".join(line for line in text.splitlines() if not line.startswith("## ")) + "\n"
    p.write_text(text, encoding="utf-8")
```

然后重新执行：

```bash
python ~/.hermes/skills/jw-content-summary/scripts/validate_candidates.py --strict books/<书名>/candidates
python ~/.hermes/skills/jw-content-summary/scripts/cluster_candidates.py books/<书名>/candidates books/<书名>/clusters.json
python ~/.hermes/skills/jw-content-summary/scripts/score_candidates.py books/<书名>/candidates books/<书名>/clusters.json books/<书名>/candidate_scores.json
python ~/.hermes/skills/jw-content-summary/scripts/build_summary_plan.py books/<书名>/clusters.json books/<书名>/candidate_scores.json books/<书名>/summary_plan.json
```

### 预防

子代理 prompt 中明确：不要写 `## ... candidates`、不要写说明性标题，直接从 `- id:` 开始输出候选条目。

## 7. schema 字段名：模板示例 vs validate 校验器不一致

### 症状

`validate_candidates.py` 报错：

```json
"issues": ["procedures.md#pr01: missing required fields: ['prerequisites']"]
```

但 extractor 模板（如 `procedure-extractor.md`）的示例写的是 `hidden_assumption:` 而非 `prerequisites:`。

### 根因

extractor 模板是给 LLM 阅读的格式示例，不是 schema 规范。`validate_candidates.py` 才是字段要求的权威来源：

```python
"procedure": BASE_FIELDS + ["steps", "prerequisites", "outcome"],
```

| 实际要求字段 | 模板可能写的别名 |
|---|---|
| `prerequisites` | `hidden_assumption` |
| `source_chapter` | `chapter`（ALIAS 已处理） |
| `source_line` | 无别名 |

### 修复

直接在 candidates 文件中用正确字段名重写有问题的条目，或重新生成时使用 `prerequisites` 而非 `hidden_assumption`。

### 验证

```bash
python ~/.hermes/skills/jw-content-summary/scripts/validate_candidates.py candidates/
# 期望 ok: true
```

## 8. 中文路径下 execute_code 的 subprocess 路径解析失效

### 症状

在 `execute_code` 中直接用含中文的绝对路径写文件时报错 `File not found`；即使路径 `os.path.exists()` 返回 True，`open()` 仍报 FileNotFoundError。

### 根因

`execute_code` 的 Python 解释器环境对含多字节 UTF-8 字符的路径解析与 terminal 环境不一致，尤其在路径经过多次 `repr()` / 字符串格式化后。

### 正确模式

始终在 subprocess 内解析路径，不在主进程传递中文路径字符串：

```python
import subprocess
correct = subprocess.run(
    ['python3', '-c',
     "import os; print(next(f'/home/jw/books/{n}' for n in os.listdir('/home/jw/books') if '林奇' in n and os.path.exists(f'/home/jw/books/{n}/chapters')))"],
    capture_output=True, text=True
).stdout.strip()
# 后续用 correct 变量，不硬编码路径字符串
```

### 错误模式

```python
CORRECT = '/home/jw/books/彼得林奇投资经典全集（...）-彼得.林奇'  # 在 execute_code 中直接硬编码含中文字符串
open(f'{CORRECT}/somefile', 'w')  # 可能失败
```

### 预防

处理含中文字符书名时，优先用 `subprocess.run(['python3', '-c', '...'])` 在子进程内完成所有文件路径操作，避免跨进程传递中文路径字符串。

## 9. execute_code 中 read_file 行号前缀破坏关键词匹配

### 症状

在 `execute_code` 中用 `read_file()` 读取章节文件后，用 `find()` 搜索关键词（如 "市场先生"、"能力圈"）返回 -1，即使关键词确实存在。

### 根因

`read_file()` 返回格式为 `LINE_NUM|CONTENT`，每行前加了行号前缀。例如：

```python
res = read_file("chapters/ch011.txt")
# res["content"] = "     1|第2章 财务与投资\n     2|\n     3|..."
```

而 `terminal(f"cat ...")` 返回的是文件的原始文本，不带行号前缀。

### 修复

在 `execute_code` 中做文本搜索时，用 `terminal(f"cat '<path>'")` 替代 `read_file()`：

```python
# 错误：read_file 加行号前缀 → 关键词匹配全失败
res = read_file(f"{BOOK_DIR}/chapters/ch010.txt", limit=2000)
ch_text = res["content"]
pos = ch_text.find("市场先生")  # → -1！

# 正确：cat 拿到原始文本
res = terminal(f"cat '{BOOK_DIR}/chapters/ch010.txt'", timeout=10)
ch_text = res["output"]
pos = ch_text.find("市场先生")  # → 正确匹配
line = ch_text[:pos].count('\n') + 1  # → 正确行号
```

### 验证

```python
from hermes_tools import terminal
txt = terminal(f"cat '{path}'", timeout=10)["output"]
assert txt.find("市场先生") >= 0, "Keyword not found in raw text"
```

### 预防

在所有需要做字符串搜索/正则匹配的 execute_code 提取脚本中，统一用 `terminal(f"cat ...")` 读文件内容。`read_file()` 只用于人工翻阅/预览。

## 10. 中文全角/半角点字符导致路径静默失败

### 症状

- `cat` / `ls` / `open()` 返回 "No such file or directory"
- 但目录确实存在（用 `ls -d *巴菲特*` 能查到）

### 根因

中文文件名中的两种点字符视觉相似但编码不同：

| 字符 | 名称 | Unicode | 示例 |
|---|---|---|---|
| `·` | 中点 (Middle Dot) | U+00B7 | 沃伦·巴菲特 |
| `・` | 片假名中点 (KATAKANA MIDDLE DOT) | U+30FB | 沃伦・巴菲特 |

`build_book_index.py` 通过 `Path(src).stem` 提取目录名，严格保留源文件名的字符编码。如果源文件名为 `巴菲特・巴菲特.md`（U+30FB），生成的目录也是 `巴菲特・巴菲特`（U+30FB）。后续脚本硬编码 `沃伦·巴菲特`（U+00B7）会静默失败。

### 诊断

```bash
ls -d /home/jw/books/*巴菲特*
echo "/home/jw/books/巴菲特致股东的信-沃伦・巴菲特" | xxd | head -3
# U+30FB 的 UTF-8 编码是 E3 83 BB；U+00B7 是 C2 B7
```

### 修复

不要猜测目录名中的点是哪种字符。每次初始化后用 `terminal(f"ls -d ...")` 动态发现实际目录名：

```python
from hermes_tools import terminal
book = terminal("ls -d /home/jw/books/*巴菲特*", timeout=5)["output"].strip()
BOOK_DIR = book.split('\n')[0]
```

### 预防

始终用 `terminal(f"ls -d ...")` 或 `os.listdir()` 动态发现含中文的目录名，不要硬编码。把所有含中文路径赋值放在同一个表达式而非多个拼接步骤中。

## 11. build_summary_plan.py 参数顺序与全A场景行为

### 症状

`build_summary_plan.py` 输出 `recommended=0, appendix=0, excluded=0`，即使所有候选都是 A 级。生成的 `summary_plan.json` 中 `cluster_count: null, grade_distribution: null`，表明脚本未能正确读取输入文件中的关键字段。

### 全A场景行为（methodology_treatise + A级≥95%）

按 v4.22 规则：直接全量写入 SUMMARY.md，不中断等待用户确认。

---

## 12. execute_code 输出 JSON 导致聚类脚本读不到候选

### 症状

execute_code 生成 candidates 后：
- `cluster_candidates.py` 输出 `candidate_count: 0, cluster_count: 0, granularity: per_file`
- `validate_candidates.py` 也显示 `total_entries: 0`
- 后续 `score_candidates.py` 和 `build_summary_plan.py` 均收到空数据

### 根因

`cluster_candidates.py` 的 `read_candidates()` 解析 blocks，期望 YAML 条目格式（`key: value` 行），不识别 JSON 对象格式（`{"id": "..."}`）。子代理 `delegate_task` 写的 YAML 能被正确解析，execute_code 写的 JSON 则无法解析。

### 正确模式

execute_code 写入 candidates 时，**必须输出 YAML 格式**。见下方完整 `to_yaml_entry()` 示例和执行顺序。

### 识别方法

```bash
python3 -c "
from pathlib import Path
import json
items = []
for p in sorted(Path('candidates').glob('*.md')):
    text = p.read_text(encoding='utf-8', errors='ignore')
    for block in text.split('\n---\n'):
        block = block.strip()
        if block:
            try:
                items.append(json.loads(block))
            except:
                pass
print(f'JSON-style entries: {len(items)}')
"
```

如果返回 0，说明候选文件是 YAML 格式（正常）。

### 正确写入函数（含完整 schema）

```python
def to_yaml_entry(d):
    lines = []
    lines.append(f'- id: {d["id"]}')
    lines.append(f'  title: {d["title"]}')
    lines.append(f'  type: {d["type"]}')
    lines.append(f'  source_chapter: {d["source_chapter"]}')
    lines.append(f'  source_line: {d["source_line"]}')
    lines.append(f'  source_quote: "{d["source_quote"]}"')
    lines.append(f'  summary: {d["summary"]}')
    kw = d.get('keywords', [])
    kw_str = ', '.join(f'"{k}"' for k in kw) if isinstance(kw, list) else f'"{kw}"'
    lines.append(f'  keywords: [{kw_str}]')
    lines.append(f'  v3_pass: {str(d.get("v3_pass", True)).lower()}')
    lines.append(f'  v3_reason: {d.get("v3_reason", "")}')
    lines.append(f'  v2_scenario: {d.get("v2_scenario", "")}')
    rel = d.get('related', [])
    rel_str = ', '.join(f'"{r}"' for r in rel) if isinstance(rel, list) else f'"{rel}"'
    lines.append(f'  related: [{rel_str}]')
    if 'structure' in d:
        for k, v in d['structure'].items():
            lines.append(f'  {k}: {v}')
    if d['type'] == 'insight':
        lines.append(f'  common_sense: "{d.get("common_sense", "")}"')
        lines.append(f'  author_reversal: "{d.get("author_reversal", "")}"')
    return '\n'.join(lines)

with open(f'{out_dir}/principles.md', 'w') as f:
    for i, d in enumerate(entries):
        if i > 0:
            f.write('\n')
        f.write(to_yaml_entry(d) + '\n')
```

### 完整执行顺序

```bash
cd books/<书名>/candidates
python3 ~/.hermes/skills/jw-content-summary/scripts/validate_candidates.py .
python3 ~/.hermes/skills/jw-content-summary/scripts/cluster_candidates.py . clusters.json
python3 ~/.hermes/skills/jw-content-summary/scripts/score_candidates.py . clusters.json candidate_scores.json
python3 ~/.hermes/skills/jw-content-summary/scripts/build_summary_plan.py clusters.json candidate_scores.json summary_plan.json
```

前两个脚本传 candidates 目录路径（`.`），后两个脚本分别传 clusters.json 和 scores.json。cluster_candidates.py 只接受目录，不接受文件列表。

## 13. insights.md 漏写 common_sense/author_reversal 字段

### 识别

`validate_candidates.py` 报错：
```json
"issues": ["insights.md#in-01: missing required fields: ['common_sense', 'author_reversal']"]
```

但其他字段格式正常，`total_entries` 中该条目仍计入。

### 根因

execute_code 生成 insight candidates 时，`common_sense` 和 `author_reversal` 这两个 insight 类型专用字段容易漏掉。validate 正确捕获，手写时不易发现。

### 修复

在 insight 条目的 `related: [...]` 行之后插入两个缺失字段：

```python
from pathlib import Path
p = Path('candidates/insights.md')
text = p.read_text()
blocks = []
for block in text.split('\n---\n'):
    block = block.rstrip()
    if not block or not block.strip().startswith('- id: in-'):
        blocks.append(block)
        continue
    if 'common_sense:' in block:
        blocks.append(block)
        continue
    lines = block.split('\n')
    new_lines = []
    for line in lines:
        new_lines.append(line)
        if line.strip().startswith('related:') and ']' in line:
            new_lines.append('  common_sense: ""')
            new_lines.append('  author_reversal: ""')
    blocks.append('\n'.join(new_lines))
p.write_text('\n\n---\n\n'.join(blocks), encoding='utf-8')
```

### 验证

```bash
python3 ~/.hermes/skills/jw-content-summary/scripts/validate_candidates.py candidates
# 期望 ok: true
```

### 预防

execute_code 中构建 insight 条目时，在字典初始化阶段就包含 `common_sense` 和 `author_reversal` 字段，不要写成可选的后补字段。""
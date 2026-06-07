# 投资分析 Skill 设计模式与反模式（v3.17.1 强化版）

> 来源：jw-company-analysis v2.2.0-v3.17.1 审计修复与迭代补充过程（2026-06-02~03）

---

## 核心审计发现（v3.17.1 深度审计）

### 模板同步三版本落后问题

**现象**：SKILL.md 从 v3.14.0 迭代到 v3.17.0（3个版本），模板版本号仍停留在 v3.14.0。

**根因**：每次修改只改 SKILL.md，模板作为"下游消费者"被系统性遗忘。

**检查方法**：
```bash
# 版本号一致性
grep 'version:' SKILL.md && grep '版本' templates/*.md | tail -1

# 评分范围一致性
grep -E '0-25分|0-30分|0-40分' SKILL.md templates/*.md

# 新增章节同步
for section in "5.3" "7.5"; do
  grep -c "$section" SKILL.md templates/*.md
done
```

**模板同步检查清单**（每次SKILL.md修改后必须执行）：
- [ ] 版本号三端一致（frontmatter / 标题 / 模板底部）
- [ ] 评分范围三端一致（SKILL.md / 模板 / checkpoint-schema.md）
- [ ] 新增章节在模板中有对应占位符
- [ ] 删除/合并的概念在模板中已同步清理

### 综合得分公式数学问题

**现象**：文档说"满分100分"，但实际最大=35+20+10+25+5=95分（逆向调整最多+5）。

**修正**：明确说明"基础满分90分+逆向调整±5分=实际范围85-95分"。投资结论矩阵中的80-100分区间需结合逆向调整分解读。

### 未引用文件清理

**现象**：15个reference文件中有4个从未被SKILL.md或其他reference文件引用。

**检查方法**：
```bash
for f in references/*.md; do
  base=$(basename "$f")
  if ! grep -q "$base" SKILL.md; then
    echo "❌ 未引用: $f"
  fi
done
```

**处理**：删除完全未引用的文件（如case-studies.md、skill-design-patterns-pattern29.md），保留被其他reference间接引用的文件。

### Step瘦身模式

**核心原则**：保留核心框架（5-6个），其余移入"扩展引用"块（`> **扩展概念**（详见 references/...）`）。

**Step 1 实测**：从164行瘦身到90行（-45%），保留5个核心框架，16个移入扩展引用。

**Step 2 待做**：188行，20处张新民引用，14处"详见references"。建议：核心公式表+利润三大前提+评分标准保留，张新民框架移入扩展引用。

### pre_analysis.py 输出对齐

**关键发现**：pre_analysis.py 的简化评分（如ROE>20→护城河20分）不等于最终评分。agent 需在此基础上做定性分析并调整分数。

**bug修复**：line 223 `score_17 = 17` → `score_12 = 17`（变量名错误）。

**SKILL.md 必须明确**：pre_analysis.py 的评分是基础参考，agent 需要在此基础上进行定性分析（四问检验法、护城河评估、管理层评估等）并调整分数。

---

## 二十六、瘦身时模板同步失败模式（v3.17.1 强化）

> 来源：v3.10.0→v3.10.1 + v3.17.0→v3.17.1

### 问题

SKILL.md 大规模瘦身或新增章节后，模板中残留了旧值或缺失新章节。

**v3.17.1 补充发现**：
1. 模板版本号可落后3个版本
2. 模板会缺失SKILL.md新增的章节（如5.3 ESG、7.5卖出信号）
3. 模板Step 4评分范围仍用旧值（40/30/30），SKILL.md已统一为25分制

### 正确做法

瘦身是三端同步操作，不是单文件操作：
```
瘦身 SKILL.md → 立即对比模板差异 → 修复模板 → 验证一致性
```

---

## 二十七、审计快速检查清单模式（v3.17.1 新增）

> 来源：jw-company-analysis v3.17.1 深度审计

### 问题

每次审计都需要重新检查版本号一致性、评分范围、新增章节同步等。容易遗漏。

### 正确做法

创建 `references/audit-quick-checklist.md`，包含：
1. 版本号三端一致性检查命令
2. 评分范围一致性检查命令
3. 新增章节同步检查命令
4. 引用文件健康度检查命令
5. 综合得分公式验证
6. pre_analysis.py 输出对齐说明

**触发条件**：每次修改 SKILL.md 后，执行检查清单中的所有命令。

---

---

## 二十八、并行书籍研究工作流（v3.24.0 强化）

> 来源：jw-company-analysis v3.12.0-v3.24.0 八轮书籍研究（24本，226个概念）

### 问题

用户反复要求"研究/root/books下的书，补充到jw-company-analysis"。每轮研究10-11本书，提取15-18个概念。如果没有标准工作流，每次都要重新规划。**v3.24.0教训**：直接提取容易重复覆盖已有内容，必须先做缺口分析。

### 正确做法

**六步闭环**（v3.24.0 新增第0步）：

```
0. 缺口分析（research-gaps.md）
   → 读取 investment-theory.md 已有概念列表
   → 逐本搜索，标注"已覆盖/未覆盖"
   → P0/P1/P2分级，方案呈报
   ↓ 用户确认"全量执行"
1. 方案呈报（缺口表+概念映射表+预计行数+版本号）
   ↓ 用户确认"全量执行/全量修复"
2. 三路并行 delegate_task（每路3-5本书，写临时文件）
   ↓
3. 合并到 investment-theory.md（追加到最后，加章节标题）
   ↓
4. SKILL.md 引用更新（每个新概念在对应Step加一行📚人类参考）
   ↓
5. 五文件版本更新 + 验证 + 临时文件清理
```

**第0步缺口分析模板**（delegate_task产出 research-gaps.md）：
```markdown
# 书籍研究缺口分析
> 对照基准：investment-theory.md §1-§N（N个概念）

## 1. 《书名》
### 已覆盖（简述）
### 缺口1：概念名
- 位置：第X章/第X页
- 内容摘要：...
- 为什么重要：...
- 优先级：P0/P1/P2
```

**P0/P1/P2分级标准**：
- P0 = 直接影响分析质量（缺少会导致错误判断）
- P1 = 增强深度（已有框架的细化/实操化）
- P2 = 知识补充（扩展认知，不直接影响评分）

**概念提取格式**（v3.24.0 强化，每个概念必须包含）：
```markdown
---

## §N. 概念名称

> **一句话定义**：[简洁中文]

### 核心要点
1. [可执行信号/指标/标准，非描述性语言]
2. ...
3. ...

### 实操应用
[agent执行时如何使用这个概念——具体的判断标准/阈值/检验方法]

### 引用
> [1-2句书中原文，标注来源书名]

---
```

**v3.24.0教训**：第一轮提取的概念偏"描述性"（是什么），后续轮次应偏"可操作性"（怎么用）。缺口分析中应标注"增量价值"——是新框架还是已有框架的细化。

**三路分组原则**：
- 路A：宏观/周期类（对应Step 5逆向检查·Step 7结论）
- 路B：风险/护城河类（对应Step 1/Step 5）
- 路C：估值/财务类（对应Step 2/Step 4）
- 每路3-5本书，避免单路过大导致delegate_task截断

**五文件版本更新**（必须同时更新）：
1. SKILL.md frontmatter（version: X.Y.Z）
2. SKILL.md 标题（# ... vX.Y.Z）
3. 模板底部（**版本**：vX.Y.Z）
4. pre_analysis.py（头部注释 + print语句）
5. checkpoint-schema.md（"version": "X.Y.Z"）

### Pitfall

**Pitfall 1：delegate_task 截断**。大文件（>15000行）的delegate_task可能截断输出。验证方法：`wc -l` 检查输出文件行数，`grep -c "^## §"` 验证概念数。

**Pitfall 2：概念编号重复**。investment-theory.md 有 §86/§87/§88 重复编号（早期遗留）。新概念必须从当前最大编号+1开始，用 `grep "^## §" investment-theory.md | tail -3` 确认。

**Pitfall 3：SKILL.md引用位置**。每个概念的📚人类参考引用必须放在对应的Step章节内，不能集中堆在一处。例如§163灰犀牛→Step 0.3，§178第二层思维→Step 5.2，§182大类资产轮动→Step 7。

**Pitfall 4：边际收益递减+新书发现**。同一本书第二轮提取的概念数通常只有第一轮的50-60%。方案呈报时应标注"边际增量"，避免用户期望过高。**v3.24.0教训**：用户列了11本书，但缺口分析发现其中3本完全未覆盖（金钱心理学/通胀陷阱/流动性经济学）+2本有重大缺口（芒格之道/投资中最简单的事）。这些书不在用户原始列表中但在/root/books/下。缺口分析时应**扩展搜索范围**到整个books目录，而非只看用户列出的书。

### 触发条件

- 用户说"研究/root/books下的书"或"继续研究这几本书"
- 用户说"全量执行"/"全量修复"/"全量修改"=直接执行方案，不再确认
- 用户说"先给方案"=先输出概念映射表，等用户确认再执行
- 用户说"继续研究"同一目录=做第二轮缺口分析，找剩余可挖深度

---

## 二十九、多轮审计修复模式（v3.22.0 提炼）

> 来源：jw-company-analysis v3.10.0-v3.22.0 八轮审计修复（62+项）

### 问题

每次审计都发现类似类型的问题（版本不一致/数学错误/模板不同步/零引用文件），但每次都要从头检查。

### 正确做法

**P0/P1/P2分级标准**：
- **P0**：执行会出错（脚本崩溃/数学错误/逻辑矛盾）
- **P1**：逻辑混淆（版本不一致/表述矛盾/定义缺失）
- **P2**：可优化（引用密度/格式统一/行数精简）

**审计检查清单**（每次修改后执行）：
```bash
# 版本一致性
grep -m1 'version:' SKILL.md
grep -oP 'v3\.\d+\.\d+' templates/*.md | tail -1
grep '版本：' scripts/*.py
grep 'version.*3\.' references/checkpoint-schema.md

# 行数统计
wc -l SKILL.md templates/*.md scripts/*.py references/investment-theory.md

# 零引用文件
for f in references/*.md; do
  base=$(basename "$f")
  grep -q "$base" SKILL.md || echo "❌ 未引用: $f"
done

# 概念编号范围
grep -c "^## §" references/investment-theory.md
grep "^## §" references/investment-theory.md | tail -3
```

### Pitfall

**Pitfall 1：patch转义问题**。SKILL.md中包含中文引号和反斜杠时，patch工具的escape-drift会导致匹配失败。解决：用`execute_code`的`read_file`+字符串替换+`write_file`代替patch。

**Pitfall 2：execute_code超时**。execute_code在处理大文件（>500行替换）时容易超时。解决：拆分为多个小patch，或用terminal的sed做原地替换。

**Pitfall 3：验证遗漏**。修改5个文件后必须逐一验证版本号，不能只检查一个。

---

---

## 三十、迭代式内容膨胀后的结构重构模式（v3.27.0 新增）

> 来源：jw-company-analysis v3.27.0 结构审计（12项问题，11项修复）

### 问题

Skill 经过多轮迭代研究（每轮新增15-20个概念引用），容器结构没有跟着进化。新内容不断被塞入"有空位的 section"，而非语义正确的位置。典型症状：

1. **万能垃圾桶 Step**：某个 Step（通常是最后几个有空位的）变成了所有新概念的堆放区。jw-company-analysis 的 Step 5 从"逆向检查"膨胀到 280 行，塞了 50+ 个与逆向检查无关的宏观理论引用。
2. **引用错位**：管理层评估（Step 1.3）下面堆了大宗商品周期、房地产周期、结构主义分析等完全无关的内容。
3. **密度不均**：有的 Step 引用密度 0.28/行，有的 0.00/行。

### 诊断方法

```bash
# 每个 Step 的行数和引用数
for step in "Step 0" "Step 1" "Step 2" "Step 3" "Step 4" "Step 5" "Step 6" "Step 7" "Step 8"; do
  lines=$(sed -n "/^## $step/,/^## Step\|^---/p" SKILL.md | wc -l)
  refs=$(sed -n "/^## $step/,/^## Step\|^---/p" SKILL.md | grep -c "§[0-9]")
  echo "$step: ${lines}行, ${refs}引用, 密度=$(echo "scale=2; $refs/$lines" | bc)"
done

# 找出引用密度异常高的 Step（可能是垃圾桶）
grep -n "§[0-9]" SKILL.md | awk -F: '{print $1}' | awk 'BEGIN{prev=0}{if($1-prev>5) print "---"; prev=$1; print}' 
```

### 正确做法

**三步重构**：

```
1. 语义审计：列出每个 Step 的职责定义，标注哪些引用属于该职责
2. 创建新容器：如果某类内容没有对应的 Step，创建新 section
   - 例：宏观理论没有归属 → 创建 Step 0.5 宏观环境评估
3. 迁移：将错位引用从当前位置移动到语义正确的 Step
   - 用 patch 的 old_string/new_string 精确替换
   - 在原位置留一行 "详见 Step X.Y" 交叉引用
```

**迁移决策矩阵**：

| 引用类型 | 正确位置 | 错误位置（常见） |
|---------|---------|---------------|
| 宏观经济/周期/货币 | Step 0.5 宏观环境 | Step 5 逆向检查 |
| 行业竞争格局 | Step 3 产业链 | Step 1.3 管理层 |
| 周期理论/资产轮动 | Step 0.5 或 Step 7 | Step 1.3 管理层 |
| 行为金融/认知偏误 | Step 5 逆向检查 | Step 0.3 事件扫描 |
| 估值方法 | Step 4 估值 | Step 5 逆向检查 |

### Pitfall

**Pitfall 1：迁移后出现重复**。从 Step A 迁移到 Step B 时，如果 Step B 已经有同名引用（之前某轮也加了），会出现重复。迁移后必须 `grep -c "概念名" SKILL.md` 检查重复。

**Pitfall 2：交叉引用丢失**。迁移后原位置应保留一行"详见 Step X.Y"交叉引用，否则 agent 在原位置找不到相关内容。

**Pitfall 3：执行总览流程图不同步**。新增 Step 后，执行总览的流程图必须同步更新，否则 agent 按流程图执行时会跳过新 Step。

---

## 三十一、排除检查点完整性审计模式（v3.27.0 新增）

> 来源：jw-company-analysis v3.27.0 排除检查点审计

### 问题

执行总览流程图中只列了部分排除检查点，遗漏了其他 Step 中定义的排除/降级条件。Agent 按流程图执行时可能跳过关键过滤。

### 正确做法

**审计方法**：扫描全文所有"排除""降级""红线""直接排除"关键词，与执行总览流程图对比：

```bash
# 找出所有排除/降级条件
grep -n "排除\|降级\|红线\|直接排除\|一票否决" SKILL.md | grep -v "^#\|注\|说明\|详见"

# 与执行总览对比
sed -n '/执行总览/,/^---/p' SKILL.md | grep "排除\|降级"
```

**补全原则**：每个排除/降级条件都必须在执行总览流程图中有对应条目。格式统一为：
```
→ 排除检查：X.Y条件描述 → ❌排除
→ 降级检查：X.Y条件描述 → ⚠️降级
→ 安全阀检查：条件描述 → ⚠️人工复核
```

---

---

## 三十二、模板污染与跨文件一致性审计模式（v3.29.0 新增）

> 来源：jw-company-analysis v3.28.0→v3.29.0 第八轮审计（11项：3P0+3P1+3P2+2P3）

### 问题

经过多轮迭代后，SKILL.md 与模板/脚本之间出现五类一致性漂移，单独看每个文件都"正确"，但跨文件对比会发现 Agent 执行时的断点。

### 五类漂移模式

**模式1：模板行号前缀污染**
- **现象**：模板每行带 `N|` 前缀（如 `1|# 公司深度分析报告`），来自 `read_file` 输出直接写回文件
- **检测**：`head -3 file.md | cat -v` 看是否有 `N|` 前缀
- **修复**：`python3 -c "import re; c=open(f).read(); open(f,'w').write(re.sub(r'^(\d+)\|','',c,flags=re.MULTILINE))"`
- **教训**：此问题会反复出现。每次用 `read_file` 读取内容后做字符串替换再 `write_file` 回去时，必须先剥离行号前缀

**模式2：ESG排除条件模板缺失**
- **现象**：SKILL.md 定义了4个ESG排除条件（审计非标/质押>80%/实控人被查/重大安全事故），模板只写"高风险-10分**或排除**"——Agent执行时无法判断哪些条件触发排除
- **检测**：`grep '或排除' templates/*.md` 找模糊措辞，对比 SKILL.md 中的明确条件列表
- **修复**：在模板中完整列出排除条件列表，与 SKILL.md 逐字对齐
- **教训**：任何"或X"的模糊措辞都是模板漂移信号——SKILL.md 中有明确条件的地方，模板必须原样复制

**模式3：📚标记遗漏（大批量）**
- **现象**：78处 `详见 references/investment-theory.md` 缺少 📚 人类参考标记，Agent 可能尝试在8-15分钟内读完9833行文件
- **检测**：`grep -c '详见.*references/investment-theory' SKILL.md` vs `grep '详见.*references/investment-theory' SKILL.md | grep -v '📚' | wc -l`
- **修复**：Python 批量替换——对所有含 `详见 references/investment-theory.md` 但不含 📚 的行加标记
- **教训**：每轮新增引用时，新引用可能漏标 📚。审计时必须检查未标记数量

**模式4：Step输出文件模板覆盖缺失**
- **现象**：SKILL.md 定义了 Step 0.5 输出 `step0_macro.json`，但模板中完全没有对应的记录区域
- **检测**：`grep -o 'step[0-9]_[a-z]*\.json' SKILL.md | sort -u` 找所有输出文件，`grep 'step[0-9]' templates/*.md` 检查覆盖
- **修复**：在模板中插入对应的输出区域（表格+结论字段）
- **教训**：SKILL.md 每新增一个 Step/输出文件，模板必须同步新增对应记录区域

**模式5：脚本版本漂移**
- **现象**：pre_analysis.py 版本 v3.22.0，SKILL.md 已到 v3.28.0（差6个版本）
- **检测**：`grep '版本' scripts/*.py` vs `grep 'version:' SKILL.md`
- **修复**：批量替换脚本中的版本号（头部注释 + print语句，通常2处）
- **教训**：五文件版本更新清单（SKILL.md frontmatter + 标题 + 模板 + checkpoint-schema + pre_analysis.py）中，脚本最容易被遗忘

### 完整审计命令集

```bash
# 1. 行号前缀污染检测
head -3 templates/*.md | cat -v | grep '^[0-9]*|'

# 2. ESG排除条件模糊措辞
grep -n '或排除\|或降级' templates/*.md SKILL.md

# 3. 📚标记遗漏
grep '详见.*references/investment-theory' SKILL.md | grep -v '📚' | wc -l

# 4. Step输出文件模板覆盖
diff <(grep -oP 'step\d+_\w+\.json' SKILL.md | sort -u) <(grep -oP 'step\d+_\w+' templates/*.md | sort -u)

# 5. 版本号四端一致
grep -m1 'version:' SKILL.md; grep '版本' templates/*.md | tail -1; grep '版本' scripts/*.py | head -1; grep 'version.*3\.' references/checkpoint-schema.md
```

### 触发条件

- 每次 SKILL.md 修改后执行上述5项检查
- 用户说"全量修改"/"全量修复"时，先跑审计命令集再制定方案
- 新增 Step/输出文件时，必须同步更新模板

**来源**：jw-company-analysis v2.2.0-v3.29.0 审计修复与迭代补充过程（2026-06-02~04）

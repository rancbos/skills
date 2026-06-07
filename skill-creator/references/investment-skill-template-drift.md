# 投资类 Skill 模板漂移防护

> 来源：jw-company-analysis v3.10.0→v3.29.0 九轮审计经验（2026-06-03~04）

## 问题背景

投资类 skill 通常有复杂的报告模板（含评分表、检查清单、验证项）。大规模重构 SKILL.md 后，模板是最容易被遗忘同步的文件。模板不会自动跟随 SKILL.md 变化。

## 模板漂移的四类典型表现

| 漂移类型 | 示例 | 根因 |
|---------|------|------|
| 评分范围不一致 | SKILL.md Step 3 四子项均为 0-25 分，模板写 /30、/30、/20、/20 | 模板在早期版本自定义了分布，SKILL.md 后来统一为等分 |
| 检查清单不同步 | SKILL.md 有 12 项建仓终检，模板只有 7 项 | 模板精简时误删了终检项 |
| 验证项数不一致 | SKILL.md Step 8.2 有 3 问，模板扩展为 7 问 | 模板先行增强，SKILL.md 未同步 |
| 复验项遗漏 | SKILL.md 有"所有者收益"复验，模板缺失 | 模板瘦身时误删关键复验项 |
| **残留模式引用** | SKILL.md 删除速览/标准模式只保留深度，模板仍列三档模式 | 模板头部"使用时机"段未同步删除 |

## 投资类 Skill 模板的特殊性

- 评分范围分布（如 Step 3 四子项 25/25/25/25 vs 30/30/20/20）直接影响加权计算
- 建仓终检清单（7-12 项）是投资安全的最后防线，缺失 = 风险
- 所有者收益、安全边际等 DCF 关键输入的复验项不可遗漏
- Step 5 安全阀得分 < -20 的风险警示必须在模板中体现

## 重构后必做的模板同步检查

```bash
# 1. 检查评分范围一致性
grep -n '/[0-9]*分' templates/*.md  # 对比 SKILL.md 中的评分标准

# 2. 检查清单项数一致性
grep -c '\[ \]' templates/*.md  # 对比 SKILL.md 中的清单项数

# 3. 检查 Step 8 验证项一致性
grep -A 20 '8\.2' templates/*.md  # 对比 SKILL.md Step 8.2

# 4. 检查版本号一致性
grep 'version' SKILL.md | head -1
grep '版本' templates/*.md | tail -1

# 5. 检查关键复验项（投资类特有）
grep '所有者收益' templates/*.md  # DCF 核心输入
grep '安全边际' templates/*.md    # 估值核心输出
grep '逆向检查.*<.*-20' templates/*.md  # 安全阀警示
```

## 版本号多端同步

版本号存在于多个位置，重构时容易只更新其中一两个（jw-company-analysis v4.1.5 审计发现实际有10处需要同步）：

| 位置 | 字段 | 示例 |
|------|------|------|
| SKILL.md frontmatter | `version: "X.Y.Z"` | YAML 头部 |
| SKILL.md 标题 | `# xxx vX.Y.Z` | 文件第一行标题 |
| templates/*.md 标题 | `# xxx（vX.Y.Z）` | 模板第一行 |
| templates/*.md version字段 | `> **version**: X.Y.Z` | 模板元数据 |
| references/checkpoint-schema.md 标题 | `# xxx（vX.Y.Z）` | schema 标题 |
| references/checkpoint-schema.md JSON示例 | `"version": "X.Y.Z"` | JSON 示例中的 version 字段 |
| references/scoring-rubric-*.md | `version: X.Y.Z` | 每个 rubric 文件的 YAML frontmatter |
| references/special-entities-calibration.md | `version: X.Y.Z` | 校准文件的 YAML frontmatter |
| references/maintenance-guide.md | `vX.Y.Z` | 架构说明中的版本引用 |
| references/version-history.md | `\| vX.Y.Z \|` | 版本记录表行 |

**规则**：更新版本号时，必须同时更新全部位置。用 `grep -rn 'version.*X\.Y' SKILL.md templates/ references/` 做全量扫描。

**子 agent 版本漂移**：当使用 delegate_task 做重构时，子 agent 可能自行 bump 版本号（如 v4.0.0、v4.1.0），与主 agent 的版本规划冲突。重构完成后必须检查并统一版本号。

## 五端同步（含预执行脚本）：如果 skill 有 `scripts/pre_analysis.py` 等预执行脚本且内含版本号，版本同步范围扩展到5处：

| 位置 | 字段 | 示例 |
|------|------|------|
| SKILL.md frontmatter | `version: "X.Y.Z"` | YAML 头部 |
| SKILL.md 标题 | `# xxx vX.Y.Z` | 文件第一行标题 |
| 模板底部 | `**版本**：vX.Y.Z` | 模板最后一行 |
| version-history.md | `\| vX.Y.Z \|` | 版本记录表 |
| scripts/pre_analysis.py | `版本：vX.Y.Z` + print语句 | 脚本头部+输出 |

## v3.28.0 新增漂移模式（来源：jw-company-analysis 第八轮审计）

### 漂移模式5：新增Step输出区域缺失

**表现**：SKILL.md 新增了 Step 0.5（宏观环境评估）并定义了输出格式（step0_macro.json），但模板中完全没有对应的记录区域。Agent 执行后无处填写宏观评估结果。

**检测**：
```bash
# 列出SKILL.md中所有Step及其输出
grep -n '输出.*json\|→ 输出' SKILL.md
# 对比模板中是否有对应的记录区域
grep -n 'step[0-9]_.*\.json\|宏观环境\|Step 0\.5' templates/*.md
```

**修复**：在模板中插入新Step的输出区域。格式：表头说明数据来源 + 关键字段表格 + 状态标记。

### 漂移模式6：排除条件列表缺失

**表现**：SKILL.md 定义了明确的排除条件列表（如ESG排除4条件：审计非标/质押>80%/实控人被查/重大安全事故），但模板只写"高风险-10分**或排除**"——未列出具体条件。Agent 执行时可能只做扣分而不触发排除。

**检测**：
```bash
# 找SKILL.md中的排除条件定义
grep -n '排除条件\|直接排除.*：\|排除（触发' SKILL.md
# 对比模板中是否有对应条件列表
grep -n '排除' templates/*.md
```

**修复**：在模板中补充排除条件完整列表。排除条件必须与SKILL.md一字不差。

### 漂移模式7：条件调节规则缺失

**表现**：SKILL.md 定义了条件调节规则（如技术面信号→建仓比例调节：🟢🟢上调至40%/🟡下调至20%/🔴暂停），但模板只有固定值（30%/50%/70%）。Agent 无法体现调节逻辑。

**检测**：
```bash
# 找SKILL.md中的条件调节/联动规则
grep -n '上调\|下调\|偏积极\|偏保守\|暂停' SKILL.md
# 对比模板中是否有对应调节逻辑
grep -n '上调\|下调\|偏积极\|偏保守' templates/*.md
```

**修复**：在模板的对应位置补充条件调节规则表或交叉引用。

### 漂移模式8：read_file行号前缀污染

**表现**：模板（或其他.md文件）每行带 `N|` 前缀（如 `1|# 标题`），来自 `read_file` 输出直接 `write_file` 回去。文件内容被永久损坏。

**检测**：`head -3 file.md | cat -v` 看是否有 `数字|` 前缀

**修复**：
```python
import re
c = open(f).read()
open(f, 'w').write(re.sub(r'^(\d+)\|', '', c, flags=re.MULTILINE))
```

**防护**：用 `execute_code` 做字符串替换时，先 `read_file` 获取内容，用 regex `r'^\s*\d+\|'` 剥离前缀，再做替换，最后 `write_file`。

### 漂移模式9：📚人类参考标记遗漏（批量）

**表现**：SKILL.md 中大量 `详见 references/investment-theory.md` 缺少 📚 标记，导致 Agent 尝试在执行时间内读完巨型文件。

**检测**：
```bash
total=$(grep -c '详见.*references/investment-theory' SKILL.md)
unmarked=$(grep '详见.*references/investment-theory' SKILL.md | grep -v '📚' | wc -l)
echo "总引用: $total, 未标记: $unmarked"
```

**修复**：Python 批量替换——对含 `详见 references/investment-theory.md` 但不含 📚 的行加标记。

**防护**：每轮新增引用后立即检查未标记数量。审计时将此作为必检项。

### 漂移模式10：脚本版本号遗忘

**表现**：五文件版本同步清单中，`scripts/pre_analysis.py` 最容易被遗忘（SKILL.md已更新3+个版本，脚本仍停在旧版本）。

**检测**：`grep '版本' scripts/*.py | head -1` vs `grep 'version:' SKILL.md`

**修复**：批量替换脚本中的版本号（头部注释 + print语句，通常2处）。

**防护**：将脚本纳入版本同步清单的**第一位**（最先检查、最后遗忘的位置）。

### 漂移模式11：检查点 Schema 文件漂移

**表现**：`references/checkpoint-schema.md` 中的版本号、Step 范围定义、得分区间与 SKILL.md 不一致。checkpoint-schema 是"隐式模板"——它定义了 agent 恢复执行时读取的 JSON 结构，如果 range 字段过时（如安全阀 -50 vs 实际 -60），恢复后 agent 会用错误的阈值判断。

**检测**：
```bash
# 版本号对比
grep 'version' references/checkpoint-schema.md | head -1
grep 'version:' SKILL.md | head -1

# 关键数值对比（安全阀范围、权重等）
grep 'range.*\[' references/checkpoint-schema.md
grep '安全阀.*范围' SKILL.md

# 权重对比
grep '"weight"' references/checkpoint-schema.md
grep '权重' SKILL.md | head -5
```

**修复**：逐项对齐版本号、range、weight 字段。

**防护**：将 checkpoint-schema.md 纳入版本同步清单（第6端）。完整同步清单：

| # | 位置 | 字段 |
|---|------|------|
| 1 | SKILL.md frontmatter | `version: X.Y.Z` |
| 2 | SKILL.md 标题 | `# xxx vX.Y.Z` |
| 3 | templates/*.md 标题 | `# xxx（vX.Y.Z）` |
| 4 | scripts/*.py 头部+print | `版本：vX.Y.Z` |
| 5 | references/checkpoint-schema.md | 标题 + `"version"` 字段 + 关键数值 |
| 6 | references/version-history.md | 版本记录表行 |

### 漂移模式12：跨 Section 阈值矛盾

**表现**：SKILL.md 内部不同 section 对同一概念使用不同指标或不同阈值。典型案例如下：

| Section A | Section B | 矛盾 |
|-----------|-----------|------|
| Step 5.2 "资产金融负债率 >70% 红线" | Step 10.3 "有息负债率 >80% 需关注" | 不同指标 + 不同阈值 |
| Step 3.2.1 "护城河宽度：窄=ROIC<10%" | Step 10.3 "护城河评分<3" | 评分阈值与宽度定义脱钩 |
| Step 7 安全阀 "范围-60到+20" | 权重表 "安全阀 -50到+20" | 同一指标不同数值 |

**检测**：
```bash
# 找所有数值阈值定义
grep -n '> [0-9]*%\|< [0-9]*%\|≥ [0-9]*\|≤ [0-9]*' SKILL.md | head -30

# 找同一概念在不同section的定义
grep -n '负债率.*>\|负债率.*红线' SKILL.md
grep -n '护城河.*<\|护城河评分' SKILL.md
grep -n '安全阀.*范围\|安全阀.*-5\|安全阀.*-6' SKILL.md
```

**修复**：
1. 统一指标名称（如全部用"资产金融负债率"或全部用"有息负债率"，不要混用）
2. 统一阈值（如果 Step 5.2 定义 70% 为红线，Step 10.3 风险警示应引用同一指标和阈值）
3. 在阈值首次出现处添加 "(Step X.Y 定义)" 交叉引用

**防护**：审计时做"阈值一致性扫描"——提取所有数值阈值，按概念分组，检查同组内是否一致。

### 漂移模式13：Step 重编号级联遗漏

**来源**：jw-company-analysis v4.1.3 审计（2026-06-06）

**表现**：SKILL.md 进行了 Step 重编号（如 Step 0-11 → Step 1-14，跳过 Step 2），但依赖文件中的 Step 引用仍指向旧编号。影响范围比普通版本漂移更大——不是 1-2 个数字偏差，而是整个编号体系错位。

**受影响文件**（按遗忘概率排序）：
1. `templates/*.md` — 最易遗忘（31+ 处 Step 引用）
2. `references/checkpoint-schema.md` — JSON 注释 + 示例中的 step 字段值
3. `references/scoring-rubric-*.md` — 子维度编号（2.x→5.x 等）
4. `references/special-entities-calibration.md` — 校准表中的 Step 引用
5. `references/maintenance-guide.md` — 架构说明中的 Step 编号表

**检测**：
```bash
# 对比 SKILL.md 和模板中的 Step 编号范围
echo "SKILL.md steps:" && grep -oP 'Step \d+' SKILL.md | sort -t' ' -k2 -n -u | tr '\n' ' '
echo "Template steps:" && grep -oP 'Step \d+' templates/*.md | sort -t' ' -k2 -n -u | tr '\n' ' '

# 检查子维度编号是否跟随父 Step
echo "Rubric sub-dims:" && for f in references/scoring-rubric-*.md; do
  echo "  $(basename $f): $(grep -oP '^\#+ [0-9]+\.[0-9]' "$f" | sed 's/#* //' | tr '\n' ' ')"
done

# 检查模板清单项数是否与 SKILL.md 一致
echo "SKILL.md checklist:" && grep -c '| ①' SKILL.md
echo "Template checklist:" && grep -c '| ①' templates/*.md
```

**修复**：
1. 用 Python 做全文替换（避免 sed 的顺序陷阱——如 Step 3→6 再 Step 6→9 会级联污染）
2. 使用临时占位符：先 `Step N → TEMP_M`，再 `TEMP_M → Step M`
3. 子维度编号需同步更新（2.1→5.1, 3.1→6.1 等）
4. checkpoint-schema 中的 JSON 示例 `"step": N` 字段值需同步
5. 检查清单项数差异（模板可能保留了已删除的清单项）

**防护**：重编号后立即运行上述检测脚本，逐文件确认 Step 引用范围一致。将此检查纳入重构后的「必做验证」清单。

### 漂移模式14：终检清单措辞与阈值漂移（Item Count Match ≠ Content Match）

**来源**：jw-company-analysis v4.1.5 审计（2026-06-06）

**表现**：SKILL.md 和模板的终检清单项数一致（如都是8项），但个别检查项的措辞、阈值、或判定标准不同。这是模式2（检查清单不同步）的**子类型**——更隐蔽，因为 `grep -c` 项数检查通过。

**实际案例**：

| 检查项 | SKILL.md | 模板 | 差异 |
|--------|---------|------|------|
| ⑤安全边际 | 优秀企业>30%，一般企业>50% | A股>30%，一般>40% | 阈值差10%+措辞不同 |
| ⑥风险分析 | 无重大偏见 | 无重大偏见+无爆雷信号 | 模板多一个限定词 |
| ⑧永久损失风险 | 最坏情形下可承受（不影响生活/现金流） | 永久性资本损失风险可接受 | 措辞差异大 |

**检测**：
```bash
# 逐项对比终检清单（不能只查项数）
diff <(grep '| ①\|| ②\|| ③\|...' SKILL.md) <(grep '| ①\|| ②\|| ③\|...' templates/*.md)
# 或：提取通过标准列做精确对比
grep -oP '⑤.*?\|' SKILL.md templates/*.md
```

**修复**：SKILL.md 是 source of truth。逐字复制 SKILL.md 的终检清单到模板。

**防护**：审计时不能只检查项数，必须逐项对比"通过标准"列的内容。

### 漂移模式15：未使用引用简写积累

**来源**：jw-company-analysis v4.1.5 审计（2026-06-06）

**表现**：SKILL.md 定义了多个引用简写（如 `📚§XX=file.md`、`🧠=file2.md`），但实际执行步骤中只使用了部分简写。未使用的简写浪费行数且造成"这个文件在哪些步骤被引用"的误导。

**实际案例**：jw-company-analysis 定义了6种简写（📚/🧠/💰/🌍/📊/🔧），实际仅使用📚和🌍两种。其余4种从未在正文出现。

**检测**：
```bash
# 提取定义的简写
grep '📖 引用简写' SKILL.md
# 对每种简写检查使用次数
for sym in '📚' '🧠' '💰' '🌍' '📊' '🔧'; do
  echo "$sym: $(grep -c "$sym" SKILL.md) uses"
done
# 使用次数=1的（仅定义行）即为未使用
```

**修复**：移除使用次数=1的简写定义。保留使用的简写。

**防护**：新增简写后立即在正文中至少使用一次。审计时检查使用计数。

### 漂移模式16：背景理论文件Step编号漂移

**来源**：jw-company-analysis v4.1.5 审计（2026-06-06）

**表现**：SKILL.md 重编号后，大型理论参考文件（如 investment-theory.md 9833行、macro-context.md 145行）中的 `Step N` 引用仍指向旧编号。这些文件不在版本同步清单中，容易被遗忘。

**实际案例**：
- macro-context.md L3："本文件供 Step 0.5 使用" → 应为 Step 3
- investment-theory.md 8处 "Step 0" → 应为 Step 1/3
- investment-theory.md "Step 5 逆向检查" → 应为 Step 10.5

**检测**：
```bash
# 检查理论文件中的Step引用
grep -n 'Step [0-9]' references/investment-theory.md references/macro-context.md references/china-value-investing.md
# 对比SKILL.md的Step编号范围
grep -oP 'Step \d+' SKILL.md | sort -t' ' -k2 -n -u
```

**修复**：sed 批量替换，注意使用临时占位符避免级联污染（如 Step 0→1 后 Step 10 变成 Step 110）。

**防护**：将理论参考文件纳入 Step 重编号的影响范围清单。重编号后 `grep -rn 'Step [0-9]' references/` 做全量扫描。

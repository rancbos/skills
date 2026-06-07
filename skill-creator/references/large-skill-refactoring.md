# Large Skill Refactoring Patterns

> 来源：jw-company-analysis v2.1.0→v2.2.0 全量重构经验（1580行→663行，-58%）

## 核心原则

### Decision Tree, Not Textbook

SKILL.md 的唯一职责是告诉 agent **下一步做什么**。理论背景、名人语录、方法论历史属于 `references/`。

**测试方法**：对 SKILL.md 的每一行问："这一行是否直接影响 agent 的下一个动作？" 如果答案是"否"，移到 references/。

**典型违规**：
- 巴菲特/芒格语录（除非直接作为判断标准）
- 方法论框架的历史背景
- 多个框架覆盖同一判断维度（如护城河有8个框架）
- 详细行业案例

**例外**：评分标准（0-25分的具体锚点）、一票否决条件、数据校验规则必须留在 SKILL.md。

### Full Rewrite > Incremental Patches（当减少>50%时）

当目标是将 SKILL.md 减少 50%+ 时，写完整新文件比 30+ 次 patch 更可靠。

**原因**：
- 每次 patch 改变行号，后续 patch 的 old_string 可能漂移
- 多次 patch 后难以验证整体一致性
- 一次性重写可以确保结构统一

**流程**：
1. 读取完整 SKILL.md
2. 识别保留内容（决策逻辑）vs 移出内容（理论/参考）
3. 创建 references/ 理论文件（如有大量理论内容）
4. 写出完整新 SKILL.md
5. 验证：grep 检查旧引用残留、Step编号一致性、权重表重复

### Execution Flow Overview

在 Step 0 之前添加 ASCII 流程图，展示完整 pipeline。Agent 一眼看清从输入到输出的全路径。

```
┌─ 输入 ──────────────────────────┐
│ 描述                             │
└──────────────────────────────────┘
         ↓
┌─ Step 1: 名称 ──────────────────┐
│ 子步骤概述                       │
└──────────────────────────────────┘
         ↓
        ...
         ↓
┌─ 输出 ──────────────────────────┐
│ 描述                             │
└──────────────────────────────────┘
```

**为什么有效**：SKILL.md 通常有 8-12 个 Step，每个 Step 有子步骤。没有总览时，agent 需要通读全文才能理解流程。总览让它在第一行就知道全貌。

## 审计分级（P0-P5）

审计发现的问题按严重性分级，决定修复顺序：

| 级别 | 定义 | 典型问题 | 修复策略 |
|------|------|---------|---------|
| P0 致命 | 直接导致执行错误 | 引用旧Step编号、权重表矛盾 | 立即精确 patch |
| P1 严重 | 增加执行成本或遗漏 | 教科书式SKILL.md、重复框架、术语不完整 | 结构性重构 |
| P2 中等 | 影响质量但不阻断 | 报告模板顺序不一致、校准说明分散 | 流程优化 |
| P3 低 | 不影响执行 | 死引用文件、版本记录冗长 | 清理 |

**修复顺序**：P0 先修（精确patch）→ P1 结构性重构（可能需要full rewrite）→ P2-P3 流程优化

## 重构检查清单

重构完成后，逐项验证：

- [ ] **旧引用残留**：grep 旧Step编号（如 `Step 0\.0`、`Step 0\.5`、`Step 2\.3`）确认清零
- [ ] **权重表唯一**：grep `权重` 确认只出现一次完整表格
- [ ] **Step编号连续**：`## Step 1` 到 `## Step N` 无跳号
- [ ] **子步骤编号正确**：`### 1.1` 到 `### 1.4` 与父 Step 对应
- [ ] **报告模板顺序一致**：模板中 Step 编号 = 执行顺序
- [ ] **references/ 全引用**：每个 references/ 文件至少被 SKILL.md 引用一次
- [ ] **无死引用**：SKILL.md 中引用的每个 references/ 文件都存在
- [ ] **术语表无过时引用**：术语表中的"详见 Step X.Y"指向正确位置
- [ ] **模板评分范围一致**：模板中每个子项的 `/X分` 与 SKILL.md 评分标准一致
- [ ] **模板检查清单完整**：模板终检清单项数 = SKILL.md 终检清单项数
- [ ] **模板验证项一致**：模板 Step 8.2 反验证问数 = SKILL.md Step 8.2 问数
- [ ] **版本号四端一致**：SKILL.md frontmatter = SKILL.md 标题 = 模板 = version-history.md

### Pitfall 1.5：版本号漂移（Version Number Drift）

版本号存在于四个位置，重构时容易只更新其中一两个：

| 位置 | 字段 | 示例 |
|------|------|------|
| SKILL.md frontmatter | `version: "3.10.1"` | YAML 头部 |
| SKILL.md 标题 | `# xxx v3.10.1` | 文件第一行标题 |
| 模板底部 | `**版本**：v3.10.1` | 模板最后一行 |
| version-history.md | `\| v3.10.1 \|` | 版本记录表 |

**规则**：更新版本号时，必须同时更新全部四处。用 `grep -rn 'v[0-9]\+\.[0-9]' SKILL.md templates/ references/version-history.md` 验证一致性。

**子 agent 版本漂移**：当使用 delegate_task 做重构时，子 agent 可能自行 bump 版本号（如 v4.0.0、v4.1.0），与主 agent 的版本规划冲突。重构完成后必须检查并统一版本号。

## 常见陷阱

### Pitfall 0：重构后模板漂移（Template Drift After Refactoring）

SKILL.md 大规模瘦身/重构后，模板文件最容易被遗忘同步。**模板不会自动跟随 SKILL.md 变化。**

**三类典型漂移**：

| 漂移类型 | 示例 | 根因 |
|---------|------|------|
| 评分范围不一致 | SKILL.md Step 3 四子项均为 0-25 分，模板写 /30、/30、/20、/20 | 模板在早期版本自定义了分布，SKILL.md 后来统一为等分 |
| 检查清单不同步 | SKILL.md 有 12 项建仓终检，模板只有 7 项 | 模板精简时误删了终检项 |
| 验证项数不一致 | SKILL.md Step 8.2 有 3 问，模板扩展为 7 问 | 模板先行增强，SKILL.md 未同步 |
| 复验项遗漏 | SKILL.md 有"所有者收益"复验，模板缺失 | 模板瘦身时误删关键复验项 |

**防御措施**：重构 SKILL.md 后，必须执行模板同步检查：

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
```

**修复优先级**：模板漂移属于 P1（严重影响质量），因为 agent 使用模板生成报告时会按模板的评分范围/检查清单执行，而非 SKILL.md 的标准。

### Pitfall 1：patch 后行号漂移

对大文件做多次 patch 时，每次 patch 改变行号，后续 patch 的 old_string 可能匹配到错误位置。

**解决**：减少 patch 次数。小改动用 patch，大改动用 full rewrite。

### Pitfall 2：理论外移后 agent 信息不足

将理论移入 references/ 后，SKILL.md 中的引用链接如果写得模糊（如"详见 references/"），agent 不知道去读哪个文件。

**解决**：每个引用指明具体文件和章节（如"详见 `references/investment-theory.md` 第6节"）。

### Pitfall 3：报告模板顺序 ≠ Step 执行顺序

报告模板按"重要性/可读性"排列，但 Step 按"分析依赖"排列。两者不一致时，agent 输出报告时会混乱。

**解决**：统一为同一顺序。在输出结构章节加注说明。

## 迭代增量研究的"万能垃圾桶"反模式

> 来源：jw-company-analysis v3.12.0→v3.27.0 经历12轮书籍研究后的结构手术

### 问题描述

当一个 skill 经过多轮迭代增量研究（如每轮研究一批新书补充概念），新内容会被放在"有空位的 section"而非语义正确的位置。经过 5+ 轮后，某些 section 变成"万能垃圾桶"——堆了 50+ 个与该 section 语义无关的引用。

**jw-company-analysis 案例**：
- Step 5（逆向检查）从 ~25 行膨胀到 ~280 行，堆了宏观经济学、帝国兴衰、货币体系、周期理论等 50+ 个引用
- Step 1.3（管理层）堆了大宗商品周期、房地产周期、结构主义分析等与管理层无关的引用
- 根因：每轮研究后，新概念被"就近塞入"有空位的 section

### 检测方法

```bash
# 检查各 section 的 §引用密度
for step in "Step 0" "Step 1" "Step 2" "Step 3" "Step 4" "Step 5" "Step 6" "Step 7" "Step 8"; do
  count=$(awk "/^## $step/{s=1} s && /§[0-9]/{c++} /^## Step [0-9]/{if(s) exit} END{print c}" SKILL.md)
  echo "$step: $count §refs"
done

# 引用密度不均匀 = 可能有垃圾桶
```

### 修复模式：结构手术（两阶段）

**第一阶段：拆分 + 迁移**
1. 识别"垃圾桶 section"中的语义错位引用
2. 创建新 section（如 Step 0.5 宏观环境评估）承接迁移内容
3. 将错位引用迁移到语义正确的 section
4. 垃圾桶 section 只保留语义相关的引用

**第二阶段：验证 + 清理残留**（必须做！）
1. 第一阶段完成后，**全文 grep 检查迁移的引用是否仍有残留**
2. 检查是否有重复内容（同一引用在新旧两个位置都出现）
3. 检查其他 section 是否也有同样的错位引用

**关键教训**：结构手术几乎不可能一次做完。第一阶段完成后必须做第二阶段验证。jw-company-analysis 的案例中，第一阶段清理了 Step 5 header 区域的宏观引用，但遗漏了 Step 5.2 中段的 ~37 行重复引用。

### 新 section 结构化模板

当迁移的目标是一个新 section（如 Step 0.5），不要只是堆引用——需要加结构：

```markdown
### X.Y 新 Section 名称

> 执行指引：Agent 只需快速扫描，提取 3-5 个最相关的判断。
>
> 输出：`stepX_output.json`（结构化输出格式）

#### A. 主题分组1
（引用按语义分组）

#### B. 主题分组2
（引用按语义分组）

#### 输出格式
```json
{
  "field1": "值",
  "field2": "值"
}
```
```

**三要素**：
1. **执行指引**：Agent 该怎么用这个 section（快速扫描 vs 逐条分析）
2. **主题分组**：引用按语义聚类，不要混堆
3. **输出格式**：这个 section 应该产出什么结构化数据

## patch 多匹配失败的诊断与修复

当 `patch` 工具报 `Found N matches for old_string` 时：

### 原因

内容在文件中出现了多次（可能是迭代增量研究导致的重复，或 read_file 行号前缀导致的格式变体）。

### 诊断步骤

```bash
# 1. 检查具体有多少处匹配
grep -c "关键片段" file.md

# 2. 查看每处的行号和上下文
grep -n "关键片段" file.md

# 3. 检查是否有 read_file 行号前缀污染
grep -c "^[0-9]*|" file.md
```

### 修复策略

1. **如果是内容重复**：先用 Python 脚本去重，再做 patch
2. **如果是行号前缀污染**：先清理前缀
   ```bash
   python3 -c "
   import re
   with open('file.md', 'r') as f:
       content = f.read()
   cleaned = re.sub(r'^(\d+)\|', '', content, flags=re.MULTILINE)
   with open('file.md', 'w') as f:
       f.write(cleaned)
   "
   ```
3. **如果是合法重复**：在 old_string 中加入更多上下文使其唯一（如包含前后的子步骤标题）

## Step 压缩技术（Step Compression）

> 来源：jw-company-analysis v3.19.0 Step 2 瘦身（188行→101行，-46%）

当某个 Step 的行数远超其他 Step（如 Step 2 是 Step 1 的 2 倍），且该 Step 包含大量"人类参考"性质的理论概念时，使用此技术。

### 方法：核心内联 + 扩展移入引用

1. **识别核心内容**（必须留在 SKILL.md）：
   - 评分表格（4-5行）
   - 强制前置检验（如"利润三大前提"）
   - 关键红线阈值（如"70%红线"）
   - 行业校准规则

2. **识别扩展内容**（可移入引用）：
   - 理论框架的历史背景
   - 多个框架覆盖同一判断维度
   - 详细行业案例
   - 计算公式推导过程

3. **压缩格式**：在 Step 末尾添加一行引用块：
   ```markdown
   > **📚人类参考**：概念A / 概念B / 概念C（`references/investment-theory.md` §30, §31）
   ```

### jw-company-analysis 实测数据

| Step | 压缩前 | 压缩后 | 减少 | 移入引用的概念数 |
|------|--------|--------|------|----------------|
| Step 1 | 164行 | 90行 | -45% | 16个框架 |
| Step 2 | 188行 | 101行 | -46% | 25个概念 |
| 模板Step 2 | 400行 | 70行 | -82% | 30个分析项 |

### 何时使用

- 单个 Step > 150 行且其他 Step < 100 行
- 该 Step 有 > 10 处"详见 references/"引用
- 模板中该 Step 的 [X] 占位符 > 50 个

### 注意事项

- 压缩后 SKILL.md 行数应减少 5-10%（非激进压缩）
- 模板同步压缩：如果 SKILL.md 的 Step 2 瘦身了，模板的 Step 2 也要同步
- 验证：压缩后 grep 确认无引用到已删除内容

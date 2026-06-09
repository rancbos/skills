---
name: jw-research-report-analysis
description: >
  卖方研报结构化提取与深度对比分析。从研报中挖掘隐含假设、预期差、分析师语气情绪、操作建议四大隐性信息，
  多篇研报交叉对比时构建"假设脆弱性热力图"和"预期差矩阵"，识别共识风险与逆向价值。
  触发词：研报分析、research report analysis、研报提取、研报对比、研报解读、卖方报告分析、
  分析师报告、券商研报、深度拆解研报、研报摘要、多篇研报对比、研报观点对比、
  分析研报、读研报、解析研报、报告拆解、报告解读。
  适用场景：单篇研报深度拆解、2-10篇研报横向对比、研报观点矛盾识别、共识脆弱性评估。
  不适用于：新闻快讯分析、财报数据提取（用 jw-company-analysis）、行业宏观分析（用 jw-industry-analysis）。
---

# 研报深度分析（Research Report Analysis）

IRON LAW: 所有分析结论必须锚定研报原文证据。无原文引用 = 无结论。禁止编造分析师未表述的观点。

Red Flags（出现以下情况必须回退重检）：
- 语气判断无原文依据 → 回退到原文定位
- 隐含假设非报告实际依赖 → 重新扫描核心逻辑链
- 预期差判断无市场参照 → 先确认一致预期再判断偏离

---

## 工作流程

- [ ] Step 0: 输入识别 ⛔ BLOCKING
- [ ] Step 1: 单篇研报提取（阶段1）
- [ ] Step 2: 多篇研报对比（阶段2）（仅多篇输入时执行）
- [ ] Step 3: 输出生成 ⚠️ REQUIRED
- [ ] Step 4: 交付验证

---

## Step 0: 输入识别 ⛔ BLOCKING

识别输入类型：
- **单篇**：1份研报文本/文件 → 执行 Step 1 → 跳过 Step 2
- **多篇**：≥2份研报文本/文件 → 执行 Step 1（逐篇）→ 执行 Step 2

确认信息：
- 研报来源（机构、分析师、日期）
- 分析目标（个股/行业/宏观）
- 输出偏好（JSON结构化 / Markdown可读 / 两者都要，默认两者）

→ 进入 Step 1

---

## Step 1: 单篇研报提取（阶段1）

加载 `references/extraction-guide.md`，按以下维度逐篇提取。

### 1.1 核心观点（core_thesis）

问自己：这篇报告最核心的一句话结论是什么？分析师给出什么评级？

- viewpoint：一句话总结核心观点
- rating：买入/增持/中性/减持/卖出
- tone.sentiment：强烈看多 / 审慎看多 / 中性 / 审慎看空 / 强烈看空
- tone.confidence_level：极度自信 / 较为确定 / 模棱两可 / 相当谨慎
- tone.evidence：**必须引用至少一处原文**

### 1.2 隐含假设（hidden_assumptions）

问自己：如果什么条件不成立，这篇报告的核心结论就会崩溃？

逐条列出报告依赖的关键假设，评估：
- dependency：核心驱动 / 辅助条件 / 背景假设
- fragility：高（单一变量可推翻）/ 中（需多个变量同时变化）/ 低（基本面稳固）
- fragility_reason：脆弱性判断依据

⚠️ 只提取报告实际依赖的假设，不要推测分析师"可能"的假设。

### 1.3 预期差（expectation_gap）

问自己：市场当前的一致预期是什么？这篇报告是强化还是挑战了共识？

- market_consensus：推断当前市场一致预期
- report_stance：强化共识 / 挑战共识 / 提出差异化视角
- gap_detail：分歧点具体描述
- implication：若分析师正确，预期差收益或风险有多大

⚠️ 无明确分歧时写"强化共识"，不强行制造预期差。

### 1.4 关键论据（key_arguments）

逐条列出支撑核心观点的论据：
- argument：论据内容
- evidence_type：数据 / 逻辑推演 / 政策引用 / 行业调研
- evidence_detail：具体数据或事实

### 1.5 催化剂（catalysts）

- catalyst：事件/政策/数据
- timeline：时间窗口
- potential_impact：高/中/低

### 1.6 风险因素（risk_factors）

- risk：风险描述
- likelihood：高/中/低
- impact_description：影响程度

### 1.7 验证方法（verification_methods）

问自己：如何用可获取的数据验证分析师的假设？

- hypothesis：待验证假设
- method：验证路径
- data_source：建议数据来源

### 1.8 操作建议（actionable_advice）

提取所有具体建议，无则留空：
- target_price / entry_point / position_sizing / stop_loss / investment_horizon / specific_strategy

⚠️ 研报未给出的字段留空，禁止编造具体价位或仓位。

→ 单篇完成。若为多篇输入，对每篇重复 Step 1 后进入 Step 2。

---

## Step 2: 多篇研报对比（阶段2）

加载 `references/comparison-guide.md`，基于 Step 1 的结构化结果进行深度对比。

### 2.1 一致性分析（consistency_analysis）

问自己：哪些维度上分析师们达成了共识？共识的强度如何？

列出观点一致的维度，标注支持的 report_id。

### 2.2 矛盾识别（contradiction_identification）

问自己：分析师们在哪些关键问题上产生了分歧？分歧的根源是什么？

对每个矛盾点：
- 分别陈述双方立场（带 report_id）
- 根源分析：假设不同 / 数据源不同 / 分析框架不同 / 时间窗口不同

### 2.3 假设脆弱性热力图（assumption_vulnerability_heatmap）

问自己：哪些假设被多篇报告同时依赖？这些假设有多脆弱？

找出≥2篇报告共同依赖的假设，评估：
- shared_by：依赖该假设的 report_id 列表
- vulnerability_score：共识依赖度 × 脚弱性的综合评分（高/中/低）
- sensitivity_analysis：若该假设不成立，对各报告结论的影响程度

⚠️ 这是系统性风险预警的核心输出。共同依赖+高脆弱 = 最大风险共鸣点。

### 2.4 预期差矩阵（expectation_gap_matrix）

问自己：哪些报告在提供"逆向思维"？逆向的程度有多大？

对每篇报告评估：
- stance：强化共识 / 挑战共识
- gap_size：预期差大小（显著/中等/微小）
- controversy_level：争议程度

### 2.5 操作建议共识（consensus_actionable_summary）

汇总各报告的操作建议：
- consensus_target：目标价区间
- consensus_position：仓位建议共识
- divergence_in_advice：操作建议上的关键分歧

→ 进入 Step 3

---

## Step 3: 输出生成 ⚠️ REQUIRED

加载 `assets/output-template.json` 作为输出骨架。

### 单篇模式
输出完整 `report_summaries[0]` 对象。

### 多篇模式
输出完整 `report_summaries[]` + `comparative_analysis`。

### 输出格式
- 默认同时输出 Markdown 可读版 + JSON 结构化版
- Markdown 版以"结论先行"结构：核心观点 → 隐含假设 → 预期差 → 完整提取
- JSON 版严格遵循 `assets/output-template.json` 字段规范
- 用户指定纯 JSON 时仅输出 JSON

---

## Step 4: 交付验证

### Pre-Delivery Checklist

#### 完整性
- [ ] 所有必填字段无遗漏（core_thesis, hidden_assumptions, expectation_gap）
- [ ] 每篇研报均完成 Step 1 全部 8 个子维度
- [ ] 多篇模式：comparative_analysis 五个子模块均已输出

#### 证据链
- [ ] tone.evidence 包含至少一处原文引用
- [ ] 所有隐含假设均可在报告中找到逻辑支撑
- [ ] 预期差判断有市场参照基准
- [ ] 无任何编造的目标价、仓位或操作建议

#### 质量
- [ ] 假设脆弱性热力图标注了≥1个共同依赖假设（多篇模式）
- [ ] 矛盾识别覆盖了核心分歧点，非边缘细节
- [ ] JSON 输出可被下游系统解析（无语法错误）

---

## 反模式（Anti-Patterns）

- **编造预期差**：报告未挑战共识时，不要强行制造分歧 → 写"强化共识"
- **语气武断**：不要用主观感受判断语气 → 必须有原文证据
- **假设过度挖掘**：只提取报告实际依赖的假设，不是所有可能的前提
- **矛盾夸大**：措辞差异≠观点矛盾 → 只在核心逻辑不同时标注矛盾
- **操作建议补全**：分析师未给目标价时不要"推算" → 留空
- **一次性全量加载**：不要在 Step 0 就加载所有 references → 按步骤按需加载

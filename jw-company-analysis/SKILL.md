---
name: jw-company-analysis
description: "深度分析A股/港股/美股公司是否值得长期持有。基于巴菲特/芒格价值投资哲学，四维加权评估（企业质量35%+财务健康20%+产业链10%+估值25%）+逆向检查安全阀+技术面时机信号。触发：'分析XX公司'、'深度分析XX'、'这家公司值不值得持有'、'XX股票分析'、'XX股票怎么样'、'这家公司值得买吗'、'价值投资分析'、'帮我看看XX'、'长期持有分析'。"
version: 3.59.0
updated: 2026-06-06
---

# 公司深度分析器 v3.59.0

> **Iron Law**: 报告中每一个结论性判断，都必须附带可验证的论据链（数据事实+推导逻辑+信源标注）。空口断言 = 报告不合格。

> **核心公式**: `投资价值 = 优秀企业 × 合理价格 × 正确持有`

**与 jw-stock-value-analyzer 的分工**：jw-stock-value-analyzer 做行业筛选+快速评分（该不该看）→ 综合分≥60 → jw-company-analysis 做深度公司分析（值不值得长期持有）。

**不做的事**：不预测短期股价涨跌、不推荐具体买卖时点、不替代用户独立判断。

**论据最低标准**（每个结论至少满足1项）：①量化数据 ②时间序列（≥2时间点）③对比基准 ④信源可追溯。📚详见 `references/data-preparation.md` 论据充分性原则完整版。

---

## 统一权重表

| 维度 | 权重 | 满分 | 加权满分 |
|------|------|------|---------|
| 企业质量（Step 1） | 35% | 100 | 35 |
| 财务健康（Step 2） | 20% | 100 | 20 |
| 产业链（Step 3） | 10% | 100 | 10 |
| 估值（Step 4） | 25% | 100 | 25 |
| 逆向检查（Step 5） | 安全阀 | -50到+20 | -5到+2 |
| 技术面（Step 6） | 不参与加权 | 100 | — |

`综合得分 = 企业质量×35% + 财务健康×20% + 产业链×10% + 估值×25% + 逆向调整分`

基础满分90分。逆向调整分 = Step 5得分 × 10% = -5到+2分。总范围：-5到92分。

技术面不参与加权，仅作为建仓时机信号系统。

---

## 排除检查汇总表

| # | Step | 条件 | 后果 |
|---|------|------|------|
| 1 | 0.3 | 重大负面事件（🔴影响>10%营收或一票否决） | ❌排除 |
| 2 | 1.1 | 四问检验Q1-Q4全部答不清 | ❌排除 |
| 3 | 1.1 | 四问检验任一答不清 | ⚠️降级 |
| 4 | 1.2 | 护城河评分 < 10 | ⚠️降级 |
| 5 | 2.1 | 利润为真不通过（经营CF/净利<1.0） | ❌排除 |
| 6 | 4.3 | 估值陷阱触发 ≥ 3项 | ⚠️降级 |
| 7 | 5.3 | 审计意见非标 | ❌排除 |
| 8 | 5.3 | 大股东质押率 > 80% | ❌排除 |
| 9 | 5.3 | 实际控制人被调查/立案 | ❌排除 |
| 10 | 5.3 | 重大环保/安全事故 | ❌排除 |
| 11 | 5 | 逆向检查得分 < -20 | ⚠️人工复核 |

**降级规则**：综合得分 × 0.85 系数。

---

## 执行总览

```
Step 0: 数据准备（排除检查0.3）→ Step 0.5: 公司背景 → Step 0.6: 宏观环境
  ↓
Step 1: 商业模式与企业质量 35%（排除1.1/1.2）
  ↓
Step 2: 财务健康度 20%（排除2.1）
  ↓
Step 3: 行业赛道与产业链 10%
  ↓
Step 4: 估值与安全边际 25%（降级4.3）
  ↓
Step 5: 逆向检查安全阀（排除5.3 / 人工复核<−20）
  ↓
Step 6: 技术面（建仓时机信号）
  ↓
Step 7: 综合评分与投资结论
  ↓
Step 8: 交卷前自检（强制后置）
  ↓
输出：.md 报告 → /root/data/
```

---

## 🔴 Step 0：数据准备与校验（强制前置）

> 📚完整流程详见 `references/data-preparation.md`

**💾 检查点状态检查**（执行前必做）：
```bash
CHECKPOINT_DIR="/root/data/.checkpoints/{股票代码}_{YYYYMMDD}"
cat "$CHECKPOINT_DIR/checkpoint.json" 2>/dev/null || echo '{"status":"no_checkpoint"}'
```
- `status=completed` → 直接输出已有报告
- `status=in_progress` → 读取 `last_step`，从 `last_step+1` 继续
- 不存在 → 从 Step 0 开始
- `pre_analysis.py` 已执行且 step0/step1/step2 JSON 存在 → 从 Step 3 继续（复用预执行结果）

**脚本调用速查表**（A股）：
```bash
# 公司概况
timeout 15 ~/.hermes/skills/jw-investment-data/scripts/fetch_market_data.py --category profile --symbol {代码} --market A
# 基础行情（多源验证）
timeout 25 ~/.hermes/skills/jw-investment-data/scripts/jw-data quote {代码}
# ⭐综合财务画像（adata 43列+预告/快报+营运+股本+概念，60-120秒）
timeout 120 ~/.hermes/skills/jw-investment-data/scripts/fetch_market_data.py --category comprehensive --symbol {代码} --market A 2>/dev/null
# 宏观环境
~/.hermes/skills/jw-investment-data/scripts/jw-data macro all
# 5年多维财务（可选补充）
timeout 120 ~/.hermes/skills/jw-investment-data/scripts/fetch_market_data.py --category financial --symbol {代码} --market A
# 技术指标
~/.hermes/skills/jw-investment-data/scripts/jw-data indicators {代码}
# ⭐七轨布林线
python3 ~/.hermes/skills/jw-company-analysis/scripts/7track_boll.py --symbol {代码} --market A --json
# K线图
~/.hermes/skills/jw-investment-data/scripts/jw-data chart {代码}
# 资金流向
timeout 30 ~/.hermes/skills/jw-investment-data/scripts/fetch_market_data.py --category capital_flow --symbol {代码} --market A
```

**港美股**：`python ~/.hermes/skills/jw-stock-value-analyzer/scripts/fetch_stock_data.py --symbol {代码} --market {HK/US}`

**⚠️ Pitfall**：
- 用 `--category quote --symbol 600519 --market A --format json`，不用旧格式 `--code`
- comprehensive 失败时 fallback 到 `financial` + web search（Pitfall 7）
- 管道模式必须 `2>/dev/null`（py_mini_racer DeprecationWarning 破坏 JSON）
- 预执行脚本：`python ~/.hermes/skills/jw-company-analysis/scripts/pre_analysis.py --symbol {代码} --market A`

**核心取数规则**：脚本优先（结构化+可验证）→ web search 做定性补充。comprehensive 覆盖85-88%量化数据，剩余12-15%依赖 web search。

**Step 0 完成标准**：①环境验证通过 ②关键数据10项校验完成 ③近30天事件扫描（无🔴排除级）④信息完整性通过 ⑤十分钟测试12项≥3项答清 ⑥"求"框架初评完成

**💾 检查点**：Step 0 完成 → 写入 `step0_data.json`（含 `industry_type`）

---

## Step 1：商业模式与企业质量（⭐核心，35%）

> 📚详见 `references/business-quality.md`

### 1.1 商业模式可理解性（0-25分）
- **四问检验法**：Q1卖什么？→ Q2客户为何选你？→ Q3为何没被资本抢走？→ Q4给100亿能否复制？
- **"求"框架**：三求22-25 / 两求18-21 / 一求14-17 / 0求0-9
- 评分：20-25（一句话说清）/ 15-19（基本清晰）/ 10-14（复杂可理解）/ 0-9（无法理解）

### 1.2 护城河（0-25分）
- 类型（品牌/成本/转换成本/网络效应/牌照/规模/消费者垄断）→ 宽度（宽/中/窄）→ 趋势（加深/稳定/被侵蚀）→ 逆向检查
- 评分：20-25（宽+加深）/ 15-19（宽+稳定或中+加深）/ 10-14（中+稳定）/ 0-9（窄或被侵蚀）

### 1.3 管理层质量（0-25分）
- 五维度：资本配置能力 / 股东导向 / 诚信与透明度 / 长期主义 / 激励机制
- 附加评估：治理结构四维检查（1.3.1）+ 战略能力（1.3.2）+ 执行力（1.3.3）
- 评分：20-25（五维度优秀）/ 15-19（四维度优秀）/ 10-14（三维度合格）/ 0-9（有诚信问题）

### 1.4 成长性（0-25分）
- 增长质量判断：好的增长=高ROIC内生增长；坏的增长=低回报扩张、靠并购堆增长
- 评分：20-25（高增+高质量+可持续）/ 15-19（中增+质量合格）/ 10-14（增长放缓）/ 0-9（负增长或质量差）

**企业质量总分 = 1.1+1.2+1.3+1.4（满分100）**

**💾 检查点**：Step 1 完成 → 写入 `step1_quality.json`

---

## Step 2：财务健康度（20%）

> 📚详见 `references/financial-health.md`

### 2.1 盈利质量（0-25分）
**🔴 利润三大前提过滤器**（强制前置）：
- ①利润为真：经营CF/净利>1.0 → 不通过=**直接排除**
- ②利润可持续：连续5年盈利，毛利率波动<3pp → 不通过=降级
- ③维持盈利不需大量资本：FCF/净利>80% → 不通过=降级

### 2.2 资产负债表健康度（0-25分）
- 资产负债率<50% / 有息负债率<30% / 流动比率>1.5 / 商誉/净资产<20%
- 张新民核心：资产金融负债率<20%优秀，>40%警惕，70%红线

### 2.3 现金流质量（0-25分）
- 经营CF连续5年为正 / FCF连续3年为正 / FCF/净利>80%
- 所有者收益 = 净利润 + 折旧摊销 - 维护性资本开支

### 2.4 财务趋势（0-25分）
- 5年ROE趋势 / 毛利率趋势 / 营收CAGR / 净利润CAGR
- "一美元前提"：市值增长/留存收益 > 1 = 优秀

**财务健康总分 = 四项之和（满分100）**

**🔍 中间检查点**：利润三大前提通过？总分≥50？无财务造假迹象？

**💾 检查点**：Step 2 完成 → 写入 `step2_financial.json`

---

## Step 3：行业赛道与产业链（10%）

> 📚详见 `references/value-chain-analysis.md`

### 3.0 行业赛道评估（前置判断，不参与加权）
- 3.0.1 市场空间与阶段 / 3.0.2 竞争格局 / 3.0.3 驱动因素与风险
- 赛道评级：优质 → 正常 → 一般 → 差

### 3.1 产业链定位（0-25分）
处于微笑曲线哪个环节？品牌/技术/平台=高附加值，纯代工/原材料=低附加值。

### 3.2 议价能力（0-25分）
波特五力评估：CR3/进入壁垒/替代品/供应商议价/购买者议价。

### 3.3 产业链风险（0-25分）
供应链单点故障？关键原材料受制于人？地缘政治影响？

### 3.4 产业链趋势（0-25分）
国产替代进程？集中度变化？技术迭代？政策驱动的产业链转移？

**产业链总分 = 3.1+3.2+3.3+3.4（满分100）**。3.0 不参与加权。

---

## Step 4：估值与安全边际（25%）

> 📚详见 `references/valuation-methods.md`

### 4.0 行业估值方法选择（强制前置）
读取 step0_data.json 的 `industry_type` → 匹配下表选方法：

| 行业类型 | 主方法 | 辅方法 | 不适用 |
|---------|--------|--------|--------|
| 金融-银行 | PB分位 | DDM | PE/PEG/DCF |
| 金融-保险 | PEV | PB+DDM | PE/PEG/DCF |
| 周期-资源 | 正常化PE | 产能市值比+PB | 当期PE/PEG |
| 消费-品牌 | DCF所有者收益 | PE分位+股息率 | PS/PB |
| 科技-成长 | PEG+PS | DCF | PB/PE分位 |
| 医药-创新 | DCF+管线估值 | PS+PE分位 | PB |
| 制造-传统 | DCF所有者收益 | PE分位+PB | PS |
| 公用事业 | DDM | DCF+股息率 | PEG/PS |

不适用方法必须标注 `[跳过：XX方法不适用于{行业}]`，不参与评分。

### 4.1 内在价值估算（0-25分）
- 首选 DCF 所有者收益法 + 2-3种相对估值法交叉验证
- PE分行业锚定区间 📚详见 `references/valuation-methods.md` 4.1.1
- PEG成长估值法 📚详见 `references/valuation-methods.md` 4.1.2
- PB资产估值法 📚详见 `references/valuation-methods.md` 4.1.3
- PS市销率 📚详见 `references/valuation-methods.md` 4.1.4

### 4.2 安全边际（0-25分）
`安全边际 = (内在价值 - 当前价格) / 内在价值`
- >40%: 21-25分 / 25-40%: 15-20 / 10-25%: 10-14 / <10%: 0-9
- A股建议：优秀企业>30%，一般企业>50%

### 4.3 估值陷阱（0-25分，每触发一项扣5分）
低PE陷阱 / 高增长陷阱 / 资产价值陷阱 / 股息陷阱 / 商誉陷阱

**⚠️ 宏观联动**：Step 0.6 利率→DCF折现率调整；周期位置→PE分位调整；风险等级→安全边际调整。

**💾 检查点**：Step 4 完成 → 写入 `step4_valuation.json`

---

## Step 5：逆向检查与误判防护（安全阀）

> 📚详见 `references/munger-mental-models.md`

### 5.1 芒格误判心理学（10项核心检查）

**评分简化查表法**：

| 偏见情况 | 扣分 |
|---------|------|
| 无偏见或仅1项轻微 | 0 到 -5 |
| 2-3项轻微 | -12 |
| 3项中等 或 5-6项轻微 | -21 |
| 有严重偏见 或 4项中等 | -32 到 -50 |

> 严重程度定义：轻微=不影响核心判断 / 中等=影响部分评分 / 严重=导致判断错误。不得自行降低严重程度。

### 5.2 逆向检查
- 子得分A：逆向检查（+10通过 / -10不通过）
- 子得分B：市场情绪（恐惧+10 / 贪婪-10 / 中性0）

### 5.3 ESG风险
- 低风险+0 / 中风险-5 / 高风险-10
- **排除条件**（触发任一直接排除）：审计非标 / 质押>80% / 实控人被查 / 重大安全事故

**Step 5 总分** = 误判扣分 + 逆向检查(±10) + 市场情绪(±10/0) + ESG扣分，硬限 -50到+20。<-20 触发人工复核。

---

## Step 6：技术面分析（建仓时机信号）

> 📚详见 `references/technical-analysis-guide.md`

**七轨布林线**（⭐重点）：
```bash
python3 ~/.hermes/skills/jw-company-analysis/scripts/7track_boll.py --symbol {代码} --market A --json
```
核心用法：基本面确认好公司后，等价格触及四轨/五轨时建仓。

**信号汇总**：🟢🟢极佳（多指标强烈买入）/ 🟢良好 / ⚪中性 / 🟡警示 / 🔴不佳 / 🔴🔴极差

**其他指标速查**：
- **均线**：MA5/10/20多头排列→🟢 / 价格站稳MA250→基本面确认 / MA60/120向上→趋势健康
- **MACD**：金叉→🟢 / 死叉→🔴 / 底背离→🟢🟢 / 顶背离→🔴🔴
- **RSI**：<20→🟢🟢(黄金坑) / 20-30→🟢 / 30-70→⚪ / 70-80→🟡 / >80→🔴🔴

**⚠️ fallback**：七轨脚本失败→用标准3轨推算，标注 `[⚠️降级]`，信号最多评为⚪。

---

## Step 7：综合评分与投资结论

> 📚详见 `references/position-management.md`

### 7.1 加权总分
`综合得分 = Step1×35% + Step2×20% + Step3×10% + Step4×25% + Step5调整分`
行业校准规则 📚详见 `references/industry-calibration.md`

### 7.2 投资结论
| 综合得分 | 结论 | 建仓建议 |
|---------|------|---------|
| ≥80 | ⭐优秀 | 当前价位可建仓 |
| 65-79 | 🟢好标的 | 等回调至安全边际内 |
| 50-64 | 🟡观望 | 暂不建仓 |
| <50 | 🔴不推荐 | 不建仓 |

### 7.3 辩论记录（Bull→Bear→Synthesis 5段结构化）
- Bull（3条看多+数据依据）→ Bear（3条看空+逐条反驳Bull）→ Synthesis 5段：Rating/Thesis/What-would-change/Risks/Holding

### 7.4 建仓终检清单（12项，全部通过才可建仓）
📚详见 `references/position-management.md` 7.5

### 7.5 卖出与止损信号
📚详见 `references/position-management.md` 7.6

**💾 检查点**：Step 7 完成 → 写入 `step7_conclusion.json`

---

## Step 8：交卷前自检（强制后置）

### 8.1 关键数据复验（抽查2项）
从股价/市值/PE-TTM/净利/ROE/安全边际/综合分/所有者收益中抽查，换信源重新取数。

### 8.2 综合反验证（10项）
①Step1-4均有评分+论据 ②Step5已执行 ③Step6已评估 ④综合分可复算 ⑤不依赖单一数据 ⑥评分与结论一致 ⑦风险警示确认 ⑧近30天事件纳入 ⑨核心结论≥2条数据支撑 ⑩辩论每条有数据依据

### 8.2.1 算术回验（强制）
报告中所有 A+B=C / A×B=C / 百分比公式，必须逐条独立回验。

### 8.3 反事实压力测试（综合分≥60必须执行）
场景A（现价+20%）+ 场景B（现价-20%）必须回答。场景C（净利-30%）+ 场景D（强监管）综合分≥70必须回答。

**任一环节不通过 → 报告打回修订。**

---

## 输出结构

报告12章：①一句话摘要 ②分析概要（关键数据表+信源等级）③商业模式(Step1) ④财务健康(Step2) ⑤产业链(Step3) ⑥估值(Step4) ⑦逆向检查(Step5) ⑧技术面(Step6) ⑨投资结论(Step7) ⑩自检摘要(Step8) ⑪完整信源索引(含K.4弱信源) ⑫能力边界声明

📚报告模板详见 `templates/company-analysis-report.md`

**文件命名**：`{公司名}_{股票代码}_{YYYYMMDD}.md`，保存路径：`/root/data/`

**⚠️ 飞书文档创建**：`cd /root/data && lark-cli docs +create --api-version v2 --doc-format markdown --content @文件名.md`

---

## Anti-Patterns（强制阅读）

- ❌ 用"护城河很宽"代替具体论据 → 必须说明类型+宽度+趋势+逆向检验
- ❌ 用当期PE判断周期股估值 → 必须用正常化PE（5-10年均值）
- ❌ 综合分≥80但安全边际<25%仍推荐建仓 → 安全边际不足时降为"观望"
- ❌ 跳过算术回验直接交付 → 8.2.1 强制执行
- ❌ 单源数据未标注🟡/🔴 → K.4弱信源清单必须填写
- ❌ 价格类数据混淆（目标价当现价）→ 反混淆5问必过
- ❌ comprehensive 返回空就放弃 → fallback 到 financial + web search
- ❌ 并行委派多家公司分析 → 逐家执行，每家完成后保存

---

## 能力边界声明

1. **数据局限**：基于公开数据，可能遗漏非公开信息
2. **模型局限**：DCF等估值模型依赖假设，假设不同结论不同
3. **知识局限**：可能对某些行业理解不够深入
4. **时间局限**：基于历史数据，未来可能与历史不同
5. **心理局限**：即使有误判防护，仍可能受心理偏见影响

**本分析不构成投资建议**，仅为学习和研究目的。投资有风险，入市需谨慎。

---

## 术语定义

| 术语 | 定义 |
|------|------|
| 护城河 | 企业持久竞争优势，使竞争对手在10年内难以侵蚀其利润（宽/中/窄） |
| 安全边际 | (内在价值 - 当前价格) / 内在价值，低于25%需谨慎 |
| 所有者收益 | 净利润 + 折旧摊销 - 维护性资本开支（巴菲特定义的"真实利润"） |
| DCF | 现金流折现法，将未来所有者收益按折现率折算为当前价值 |
| 逆向检查 | 反转假设的思维工具：不买可能因为什么？什么会摧毁这家公司？ |

📚完整术语体系详见 `references/investment-theory.md`

---

## 参考文件索引

| 文件 | 内容 | 加载时机 |
|------|------|---------|
| `references/data-preparation.md` | Step 0 完整流程+论据原则+信源体系+价格混淆防护 | Step 0 执行时 |
| `references/business-quality.md` | Step 1 商业模式+护城河+管理层+成长性详细评估 | Step 1 执行时 |
| `references/financial-health.md` | Step 2 盈利质量+资产负债表+现金流+财务趋势详细指标 | Step 2 执行时 |
| `references/value-chain-analysis.md` | Step 3 产业链定位+议价能力+风险+趋势详细分析 | Step 3 执行时 |
| `references/valuation-methods.md` | Step 4 DCF/PE/PEG/PB/PS/PEV/DDM 全部估值方法详解 | Step 4 执行时 |
| `references/munger-mental-models.md` | Step 5 芒格25种误判倾向完整体系 | Step 5 执行时 |
| `references/technical-analysis-guide.md` | Step 6 均线/MACD/RSI/布林带详细技术分析 | Step 6 执行时 |
| `references/position-management.md` | Step 7 建仓策略/卖出信号/催化剂/可视化图表 | Step 7 执行时 |
| `references/industry-calibration.md` | 行业校准速查：PE锚定区间/PB速查/行业类型判定 | 各Step行业校准时 |
| `references/investment-theory.md` | 完整投资理论框架（§1-§39） | 需要理论深入时 |
| `references/macro-context.md` | 宏观环境评估框架（周期/债务/灰犀牛/资产轮动） | Step 0.6 执行时 |
| `references/industry-pb-details.md` | 六大行业PB估值区间详解 | Step 4 PB估值时 |
| `references/data-coverage-audit.md` | 数据覆盖率审计记录（维护用） | 取数策略优化时 |
| `references/skill-design-patterns.md` | Skill设计模式与反模式（维护用） | Skill迭代优化时 |
| `references/checkpoint-schema.md` | 检查点JSON结构定义 | 写入检查点时 |
| `references/data-fetch-strategy.md` | 分层取数策略完整映射 | 取数失败时 |
| `references/insurance-pev-case-taiping.md` | 保险PEV估值实战案例 | 保险行业分析时 |
| `references/valuation-case-studies.md` | 估值实战案例集 | 估值计算时 |
| `references/zhang-xinmin-core.md` | 张新民财报分析核心框架 | 财务分析时 |
| `references/zhang-xinmin-advanced.md` | 张新民高级分析方法 | 深度财务分析时 |
| `references/china-value-investing.md` | 中国特色价值投资 | A股分析时 |
| `templates/company-analysis-report.md` | 报告模板 | 生成报告时 |
| `scripts/pre_analysis.py` | 预执行脚本（节省3-5分钟） | Step 0 预执行 |
| `scripts/7track_boll.py` | 七轨布林线脚本 | Step 6 技术面 |

**📚 引用说明**：本 skill 内联内容为 agent 执行所需的骨架和关键约束。理论扩展、详细方法论、实战案例均在 references 中按需加载。

---

## 版本记录

详见 `references/version-history.md`（完整版本历史）。

**v3.59.0 变更摘要**（2026-06-06）：
- S1：SKILL.md 从 2122 行精简至 ~450 行，详细内容抽取到 10 个 references 文件
- S2：description 增加自然语言触发变体
- S3：新增 Anti-Patterns 集中章节
- S4：Step 5 评分简化为查表法
- S5：共享脚本映射合并到 Step 0 脚本速查表
- S6：每步增加 💾 检查点写入标记

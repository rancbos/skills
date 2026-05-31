# 阶段 2 — 动态提取 + 统一验证 + 软聚类

## 目标

根据阶段 1 的动态路由，只启动必要的子代理。子代理负责发现候选；主代理基于全文索引统一补全 V1 跨域证据；最后用脚本做软聚类，减少阶段 3 重复阅读。

## 核心分工

| 角色 | 做什么 | 不做什么 |
|------|--------|----------|
| extractor 子代理 | 发现候选、给原文锚点、判断独特性 V3 | 不做最终 V1 跨域验证 |
| 主代理 | 统一补全 V1 证据、异常检测、进度汇报 | 不重新读全文 |
| 脚本 | 软聚类候选 | 不删除候选 |

## 动态启动 extractor

按阶段 1 路由表启动 2-5 个子代理，不固定 5 个。

常见组合：

| 书籍类型 | extractor 组合 |
|----------|----------------|
| 方法论专著 | framework, principle, case, boundary |
| 学术理论 | framework, glossary |
| 传记案例 | case, principle, boundary |
| 散文随笔 | principle, insight |
| 实操手册 | procedure, boundary, case |
| 强洞见散文/随笔 | insight, principle |

> glossary 不拿全书，只拿 `snippets/definitions.json` 和必要章节片段。

## 子代理输入

每个子代理接收：

- 阶段 1 的 `stage1-understanding.md`
- 路由表中分配给它的 `chapters/*.txt` 或 `snippets/*.json`
- 对应 extractor prompt
- 输出路径 `candidates/<type>.md`

**减少重复读取（v4.60 强制，v4.66 Token 优化）**：子代理**必须**在 delegate_task 的 context 参数中直接嵌入 stage1 的核心内容（书籍类型、章节结构、路由表），**禁止**让子代理独立读取 `stage1-understanding.md`。每个子代理独立读取会重复消耗 ~50K tokens × N 个子代理。提取方法：主代理读取 stage1 后，将 §1 基本信息、§2 核心命题、§4 路由表 嵌入 context。**预计节省**：62 个子代理 × ~50K = ~200K tokens。

## 子代理输出字段

```yaml
id: f01
title: 逆向思维
type: framework
source_chapter: ch003 / 第三讲
source_quote: "..."      # ≤150 字
summary: "用自己的话, 5-10 行"
keywords: [逆向, 反过来想, 避免错误]
v3_pass: true
v3_reason: "常识是'多想', 作者强调'优先反着想'，排序反常识"
v2_scenario: "如果面试被问不知道答案的问题..."
```

**⚠️ 格式规范（v4.60 新增）**：字段行必须是 `- field: value` 或 `- **field**: value` 格式。脚本同时支持两种，但**不要用其他格式**（如 `field：value` 全角冒号、`**field**：value` 全角冒号）。

**子代理输出结构要求**：
- 文件第一行用 `# Title` 作为标题（会被脚本自动跳过）
- 每个候选用 `## id — 标题` 分隔
- 字段用 `- **field**: value` 格式（脚本支持带 `**` 的粗体格式）
- 不要在字段行中使用全角冒号 `：`

注意：子代理不再要求 `v1_pass`。V1 由主代理统一做。

## V3 独特性（子代理内嵌）

一个聪明但没读过这本书的人，能说出这个洞见吗？

- ✅ 通过：只有读了这本书才能获得的独特视角
- ❌ 不通过：任何聪明人都能说出的常识 → 放入 rejected/

## V1 跨域验证（主代理统一补证）

### 为什么移出 extractor

定向切片会导致误杀：一个方法论的第二证据可能在另一个 extractor 的文本范围内。

### 操作方式

主代理拿每个候选的：

- `title`
- `keywords`
- `summary`
- `source_chapter`

在以下材料中寻找第二证据：

- `book-index.json` 的章节标题/首尾段/关键词
- `snippets/quotes.json`
- `snippets/cases.json`
- `snippets/warnings.json`
- 必要时读取少量相关 `chapters/chXXX.txt`

V1 判定：

```yaml
v1:
  passed: true
  evidence:
    - ch003: 投资决策场景
    - ch007: 工程设计场景
  note: "两个证据来自不同章节和不同对象"
```

找不到第二证据：
- 不立即删除
- 降级标记：`v1_status: weak`
- 阶段 3 默认不完整展开，除非它的 V3 独特性极强

## 软聚类

子代理全部完成 + V1 补证后，**先运行 dry-run 测试解析是否正常**，再运行完整管道：

```bash
# Step 0: 预置测试（v4.60 新增）—— 验证脚本能正确解析候选格式
python3 ~/.hermes/skills/jw-content-summary/scripts/pipeline_phase2.py \
  books/<slug>/candidates books/<slug>/ --dry-run

# 预期输出：ok=true, count=60, types={framework: 15, principle: 18, ...}
# 如果 count=0 或 ok=false，检查候选文件格式（见上方格式规范）

# Step 1: 正式运行管道
python3 ~/.hermes/skills/jw-content-summary/scripts/pipeline_phase2.py \
  books/<slug>/candidates books/<slug>/
```

一次完成 validate → cluster → score → build_summary_plan，生成 `clusters.json` + `candidate_scores.json` + `summary_plan.json` + `phase2_result.json`。

```yaml
cluster_id: c003
canonical_title: 逆向思维
members:
  - frameworks.md#f02
  - principles.md#p04
  - cases.md#c07
evidence_count: 3
types: [framework, principle, case]
decision: pending
```

阶段 3 只读 cluster 摘要，必要时再回看成员。

## 自动进入阶段 3

阶段 2 完成后自动进入阶段 3，全量展开所有 cluster。数量闸门和用户确认闸口已移除（v4.22）。质量决策包照常生成作为审计记录。



## execute_code 分批策略（v4.62 新增）

**问题**：长书（>50章）用 execute_code 一次性读取所有章节会超时（>5min），且 token 消耗过大。

**解决方案**：按 extractor 路由表分批处理，每批 20-30 章。

### 分批规则

| 章节数 | 批次策略 | 每批章节数 |
|--------|----------|-----------|
| ≤30 | 单批 | 全部 |
| 31-60 | 2批 | 30 |
| 61-120 | 3-4批 | 30 |
| >120 | delegate_task 回退 | — |

### 执行流程

```python
# 1. 从 stage1-understanding.md 提取路由表
# 2. 按 extractor 分组章节
# 3. 每组内按 30 章分批
# 4. 每批用 execute_code 提取，输出 YAML 到 candidates/<type>.md
# 5. 最后运行 pipeline_phase2.py
```

### 关键注意事项

- **不要读全书**：每批只读路由表分配的章节
- **追加写入**：多个批次写入同一文件时，第二批开始不覆盖
- **source_line 格式**：支持行号（`42`）、章节名（`ch017`）、年份（`1984年致股东信`）
- **超时回退**：execute_code 超时 → delegate_task → 主代理直接读取

## 常见失败模式

1. **动态路由太少** — 为省 token 漏掉关键 extractor
2. **V1 只看候选原切片** — 这是 v3.7 的陷阱，必须跨索引补证
3. **软聚类当去重** — cluster 只分组，不删除任何成员
4. **glossary 又读全书** — glossary 只读 definitions.json 和必要上下文

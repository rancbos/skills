# 手动创建 Candidates 指南

## 场景

当 `validate_candidates.py` 失败（格式不正确、缺少必需字段）或 pipeline 无法正常运行时，需要手动创建 candidates。

## 何时使用手动创建

1. **validate 失败**：candidates 格式不符合 SCHEMA 要求
2. **pipeline 异常**：脚本执行错误或超时
3. **快速原型**：需要快速生成 SUMMARY.md，不追求完美格式
4. **单章主导型**：章节内容较少，手动提取更高效

## 手动创建流程

### 1. 读取章节内容

```python
# 读取章节文本
chapter_path = "/path/to/book/cleaned_text/chapters/ch001.txt"
with open(chapter_path, 'r', encoding='utf-8') as f:
    content = f.read()
```

### 2. 识别方法论单元

快速扫读内容，识别：
- **框架（framework）**：核心概念体系、分析模型
- **原则（principle）**：指导性规则、核心观点
- **程序（procedure）**：操作步骤、流程
- **边界（boundary）**：限制条件、注意事项
- **案例（case）**：具体例子、实证
- **术语（glossary）**：专业术语定义
- **洞见（insight）**：反直觉观点、独特见解

### 3. 创建 candidates 文件

```yaml
# 文件路径：/path/to/book/candidates/frameworks.md

- id: fw-01
  title: 核心框架名称
  type: framework
  source_chapter: ch001
  source_quote: "原文引用内容"
  source_line: 42
  summary: "框架摘要"
  keywords: [关键词1, 关键词2, 关键词3]
  related: [pr-01, bd-01]
  v3_pass: true
  v3_reason: "方法论清晰，有明确应用场景"
  v2_scenario: "应用场景描述"
  content: |
    详细内容描述。
    包含核心概念和应用方法。

- id: pr-01
  title: 核心原则名称
  type: principle
  source_chapter: ch001
  source_quote: "原文引用内容"
  source_line: 56
  summary: "原则摘要"
  keywords: [原则关键词]
  related: [fw-01]
  v3_pass: true
  v3_reason: "原则清晰，可操作性强"
  v2_scenario: "应用场景描述"
  content: |
    详细内容描述。
    包含具体原则和应用方法。

- id: pc-01
  title: 操作程序名称
  type: procedure
  source_chapter: ch001
  source_quote: "原文引用内容"
  source_line: 78
  summary: "程序摘要"
  keywords: [程序关键词]
  related: [fw-01, pr-01]
  v3_pass: true
  v3_reason: "步骤清晰，可执行"
  v2_scenario: "应用场景描述"
  steps:
    - step1: "步骤1描述"
    - step2: "步骤2描述"
    - step3: "步骤3描述"
  prerequisites: "前置条件"
  outcome: "预期结果"
  content: |
    详细内容描述。
    包含具体步骤和流程。
```

### 4. 运行 pipeline（可选）

如果 candidates 格式正确，可以尝试运行 pipeline：

```bash
cd /root/.hermes/skills/jw-content-summary
python3 scripts/pipeline_phase2.py /path/to/book/candidates /path/to/book
```

如果 pipeline 失败，直接进入下一步。

### 5. 手动编写 SUMMARY.md

当 pipeline 失败或无输出时，直接编写 SUMMARY.md：

```markdown
# 书名 - 方法论提炼

## 问题一：作者的写作意图
作者旨在...（简要说明写作目的）

## 问题二：作者的核心论点
1. 核心论点1
2. 核心论点2
3. 核心论点3

## 问题三：作者的论证逻辑
作者通过以下逻辑链条论证核心观点：
1. 论证步骤1
2. 论证步骤2
3. 论证步骤3

## 问题四：这本书的局限性
1. 局限性1
2. 局限性2
3. 局限性3

## 问题五：这本书对我的启发
1. 启发1
2. 启发2
3. 启发3

---

## 方法论单元一：标题

**R — Reading**：
> 原文引用内容
> ——来源章节

**I — Interpretation**：
解释和意义。

**A1 — Application (个人经历)**：
个人应用场景。

**A2 — Application (工作场景)**：
工作应用场景。

**E — Evidence**：
论证依据。

**P — Pitfall**：
常见陷阱。

**B — Benefit**：
预期收益。

---

## 方法论单元二：标题
（重复上述结构）

---

## 审计信息
本提炼基于《书名》课程讲义，提炼核心方法论单元。

提炼时间：YYYY年M月D日
来源文件：filename.txt（N字符）
处理流程：文本清洗 → 索引构建 → 手动候选提取 → 方法论提炼

注意事项：
1. 本文为手动提炼，格式可能不完全符合标准
2. 方法论单元基于内容提炼，实践应用需结合具体情况
```

## 质量检查

手动创建的 SUMMARY.md 需要检查：

1. **七段完整性**：每个方法论单元是否包含 R/I/A1/A2/E/P/B 七段
2. **引用有出处**：R 段是否有明确的章节引用
3. **引用长度**：R 段引用是否 ≤150 字符
4. **反直觉洞见**：是否体现作者独特的反直觉见解
5. **审计信息**：是否包含字面量「审计信息」

## 优缺点

### 优点
- 快速生成 SUMMARY.md
- 不依赖 pipeline 脚本
- 灵活应对格式问题

### 缺点
- 格式可能不完全符合标准
- 缺少 pipeline 的质量评分和聚类
- 需要人工判断和提取

## 版本

- 2026年6月5日：创建手动创建指南

# Candidates 必需字段格式（v4.60+）

## 问题

`validate_candidates.py` 使用 SCHEMA 验证 candidates 格式。缺少必需字段会导致 validate 失败，pipeline 无法正常运行。

## 必需字段（BASE_FIELDS）

所有类型的 candidate 都必须包含以下字段：

```yaml
- id: fw-01                              # 必需：唯一标识符
  type: framework                        # 必需：类型（framework/principle/case/boundary/procedure/glossary/insight）
  source_chapter: ch001                  # 必需：来源章节
  source_quote: "原文引用内容"            # 必需：原文引用
  source_line: 42                        # 必需：来源行号（整数）
  summary: "方法论摘要"                   # 必需：简短摘要
  keywords: [关键词1, 关键词2]           # 必需：关键词列表
  related: [pr-01, bd-01]               # 必需：相关 candidate ID 列表
  v3_pass: true                          # 必需：v3 验证通过标志
  v3_reason: "验证通过原因"               # 必需：v3 验证原因
```

## 类型特定字段

### insight 类型
```yaml
- id: in-01
  type: insight
  # ... BASE_FIELDS ...
  common_sense: "常识内容"                # 必需：常识性内容
  author_reversal: "作者反转内容"         # 必需：作者的反直觉观点
  v2_scenario: "应用场景"                 # 必需：应用场景描述
```

### principle 类型
```yaml
- id: pr-01
  type: principle
  # ... BASE_FIELDS ...
  v2_scenario: "应用场景"                 # 必需：应用场景描述
```

### framework 类型
```yaml
- id: fw-01
  type: framework
  # ... BASE_FIELDS ...
  v2_scenario: "应用场景"                 # 必需：应用场景描述
```

### case 类型
```yaml
- id: ca-01
  type: case
  # ... BASE_FIELDS ...
  linked_method_hint: "关联方法提示"      # 必需：关联方法提示
  v2_scenario: "应用场景"                 # 必需：应用场景描述
```

### procedure 类型
```yaml
- id: pc-01
  type: procedure
  # ... BASE_FIELDS ...
  steps:                                 # 必需：步骤列表
    - step1: "步骤1描述"
    - step2: "步骤2描述"
  prerequisites: "前置条件"               # 必需：前置条件
  outcome: "预期结果"                     # 必需：预期结果
```

### boundary 类型
```yaml
- id: bd-01
  type: boundary
  # ... BASE_FIELDS ...
  # 无额外必需字段
```

### glossary 类型
```yaml
- id: gl-01
  type: glossary
  # ... BASE_FIELDS ...
  # 无额外必需字段
```

## 示例：正确的 candidate 格式

```yaml
- id: fw-01
  type: framework
  source_chapter: ch001
  source_quote: "预期差框架的核心是..."
  source_line: 42
  summary: "预期差框架：实际走势与盘前预期的偏离"
  keywords: [预期差, 盘前定性, 市场结构]
  related: [pr-01, pr-02]
  v3_pass: true
  v3_reason: "方法论清晰，有明确应用场景"
  v2_scenario: "适用于短线交易决策，帮助交易者从涨跌思维转向预期差思维"
```

## 常见错误

### 1. 缺少必需字段
```yaml
# 错误：缺少 source_chapter, source_quote, source_line, summary, v3_pass, v3_reason
- id: fw-01
  type: framework
  keywords: [关键词]
  content: "内容"
```

### 2. 字段名拼写错误
```yaml
# 错误：source_line 拼写错误
- id: fw-01
  type: framework
  source_chapter: ch001
  source_quote: "引用"
  source_lin: 42  # 拼写错误，应为 source_line
```

### 3. 字段类型错误
```yaml
# 错误：source_line 应为整数，不是字符串
- id: fw-01
  type: framework
  source_chapter: ch001
  source_quote: "引用"
  source_line: "第42行"  # 应为整数 42
```

## 验证命令

```bash
# 验证 candidates 格式
python3 scripts/validate_candidates.py books/<title>/candidates

# 严格模式（检查所有字段）
python3 scripts/validate_candidates.py --strict books/<title>/candidates
```

## 修复建议

如果 validate 失败，检查：
1. 是否包含所有 BASE_FIELDS
2. 字段名是否拼写正确
3. 字段类型是否正确（source_line 为整数）
4. 类型特定字段是否完整

## 版本

- v4.60：发现并修复粗体格式问题
- v4.63：扩展 source_line 验证支持年份、章节名、中文描述
- 当前文档：2026年6月5日创建

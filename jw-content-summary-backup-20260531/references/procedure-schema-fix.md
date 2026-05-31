# Procedure Extractor — Correct Schema Reference

> **Known Issue (v4.4–v4.6)**: `procedure-extractor.md` template示例写 `hidden_assumption`，但 `validate_candidates.py` 要求 `prerequisites`。Extractor 模板与 validator schema 不一致， extractor 模板需要 out-of-band 更新（不通过 skill_manage）。

## validate_candidates.py 要求的 procedure 必需字段

```yaml
- id: pr01
  title: "{{流程标题}}"
  type: procedure
  source_chapter: ch003       # 或 "ch003" 格式
  source_line: 1              # 整型，引用在源章节文件中的行号
  source_quote: "{{≤150 字原文}}"
  summary: "{{流程用于什么问题；前置条件是什么；步骤之间如何因果相连}}"
  keywords: [流程关键词, 步骤关键词]
  steps: "1 输入... → 2 操作... → 3 输出..."   # 必须有 "→" 连接因果
  prerequisites: "执行前必须已经具备……"         # 注意：是 prerequisites，不是 hidden_assumption
  outcome: "执行后的可验证结果"
  v3_pass: true
  v3_reason: "{{读者没读过书很难自己说出这个反转}}"
  v2_scenario: "可迁移到：{{新手可执行的新场景}}"
  related: [fw01, pr02]       # 不超过3条
```

## 与 extractor 模板的差异

| 字段 | extractor模板(错误) | validate(正确) |
|---|---|---|
| 前提条件字段 | `hidden_assumption:` | `prerequisites:` |
| 格式示例 | 无 | `"执行前必须已经具备……"` |

## 修复 procedure candidate 的方法

如果 validate 报告 `missing required fields: ['steps', 'prerequisites', 'outcome']`，说明候选文件用的是旧字段名。修复步骤：

1. 找到对应的候选文件（通常是 `candidates/procedures.md`）
2. 将 `hidden_assumption:` 替换为 `prerequisites:`
3. 补充缺失的 `steps:` 和 `outcome:` 字段
4. 重新运行 `validate_candidates.py`

## 生成合规 procedure candidate 的脚本模板

```python
proc = {
    "id": "proc01",
    "title": "评估企业的四步法（12准则系统检查清单）",
    "type": "procedure",
    "source_chapter": "ch003",
    "source_line": 1,
    "source_quote": "巴菲特评估企业的系统流程：①企业准则——②管理准则——③财务准则——④市场准则。",
    "summary": "巴菲特有系统的12准则检查清单……",
    "keywords": ["12准则", "企业评估", "四步法"],
    "steps": "1 逐一核对12准则 → 2 全部满足才进入估值阶段 → 3 估值计算内在价值 → 4 评估安全边际 → 5 决定是否买入",
    "prerequisites": "需要至少3-5年的财务数据、对行业的持续跟踪理解。",
    "outcome": "得到买入/不买入/进一步研究的明确结论。",
    "v3_pass": True,
    "v3_reason": "这是巴菲特方法论的操作化。",
    "v2_scenario": "用12准则评估任何股票。",
    "related": ["fw01", "fw02"],
}
```

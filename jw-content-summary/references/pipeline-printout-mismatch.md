# pipeline_phase2.py 终端输出误报告警

## 问题描述

运行 `pipeline_phase2.py` 时，终端可能显示：

```
[score] candidates=37 avg=0
[plan] recommended=0 appendix=0
```

但实际的 JSON 文件（`candidate_scores.json`、`summary_plan.json`）中的数据可能是正确的（如 avg=95.27, recommended=10）。

## 根因

v4.26 之前版本的 `pipeline_phase2.py` 存在两个字段名不匹配：

| 位置 | 代码使用 | 实际 JSON 字段 |
|------|---------|---------------|
| score 阶段 print | `scores.get("avg_score", 0)` | `"average_score"` |
| plan 阶段 print/safety valve | `plan.get("recommended", [])` | `"recommended_units"` |
| plan 阶段 print | `plan.get("appendix", [])` | `"appendix_units"` |
| plan 阶段 print | `plan.get("weak", [])` | `"excluded_or_weak"` |

## 判断信号

如果终端输出 `avg=0` 但 `candidate_scores.json` 中的 `average_score` 正常（>0），说明命中此 bug。

如果终端输出 `recommended=0 appendix=0` 但 `summary_plan.json` 中的 `recommended_units` 数组非空，说明命中此 bug。

## 修复

v4.27 已修复 `pipeline_phase2.py`：使用 `scores.get("average_score", scores.get("avg_score", 0))` 兼容两种字段名，以及 `plan.get("recommended_units", plan.get("recommended", []))` 兼容两种字段名。

## 不受影响的部分

- JSON 文件写入始终正确（各子脚本独立写入，不受 pipeline wrapper 字段名影响）
- `phase2_result.json` 中的 `results["stages"]["plan"]["recommended"]` 在修复前也可能显示 0（使用 wrapper 的字段名），但 `summary_plan.json` 始终正确
- `build_summary_plan.py` 读取 `scores_file` 和 `clusters_file` 时使用正确的字段名，不受影响

## 工作建议

当 pipeline 终端输出与预期不符时：**直接检查 JSON 文件**（`candidate_scores.json`、`summary_plan.json`），不要信任终端 print 的数字。终端输出仅作进度指示，不以它做决策。

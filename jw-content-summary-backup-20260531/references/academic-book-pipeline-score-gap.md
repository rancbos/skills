# 学术类书籍 pipeline 评分失真（v4.37）

## 现象

学术类书籍（行为经济学、认知心理学、社会学等）的候选人在 `pipeline_phase2.py` 输出中得分极低（4-7/10），grade 全 D，全部进入 `excluded_or_weak`，但内容实际完整可用。

## 根因

`validate_candidates.py` 对格式元数据字段的缺失扣分极重：
- `missing_source_quote`: -30分
- `v3_not_passed`: -30分
- `missing_or_invalid_source_line`: -15分

学术类书籍的文本结构与训练语料不同，execute_code 提取的候选常缺少这些字段，但正文中的 R/I/A1/A2/E/P/B 七段内容仍然完整。

## 判断信号

```json
// candidate_scores.json
{
  "average_score": 4.17,
  "grade_distribution": {"A": 0, "B": 0, "C": 0, "D": 18},
  "penalties": {
    "missing_source_quote": -30,
    "v3_not_passed": -30,
    "missing_or_invalid_source_line": -15
  }
}

// 但正文内容完整：
// candidates/frameworks.md 中有 3 个完整 framework 条目
// candidates/principles.md 中有 6 个完整 principle 条目
// 每条都有 R 引用、I 阐释、A1 案例、A2 场景、E/P/B 段
```

penalties 集中在 `missing_source_quote`、`v3_not_passed`、`missing_or_invalid_source_line` 三项，而实质性内容字段（如 `missing_v2_scenario`、`empty_related`）无罚分，即高度提示格式问题而非内容问题。

## 处理路径（不走回退）

1. **直接写 SUMMARY**：跳过 `summary_plan.json` 的推荐/排除逻辑，按书领域知识直接编组 12-16 个方法论单元
2. **候选内容可用性验证**：读 candidates/*.md 实际正文，不依赖 score/grade
3. **validator 验证**：写完后跑 `validate_summary.py`，学术书内容通常 PASS（validator 检测内容本身，不检测 score）
4. **审计区记录**：`average_score: 4.17`、`grade: all D`、pipeline 格式失真、手动编组

## 参考案例

| 书名 | score | grade | 处理 |
|---|---|---|---|
| 思考，快与慢 | 4.17/10 | 全D（18个） | 手动编组10个单元 → validate PASS |
| 投资中最简单的事 | 0-5/10 | 全D（37个） | 全量读取+手动编组（v4.24） |
| 查理·芒格的投资思想 | 0/10（全零） | 全A | per_file granularity bug → by_type 重跑 |

## 相关

- §9.1 碎片化计划回退：`single_member_ratio: 1.0` 场景
- §9.2 per_file granularity bug：另一种 score 归零根因
- `references/empty-plan-fallback.md`：全空计划回退流程
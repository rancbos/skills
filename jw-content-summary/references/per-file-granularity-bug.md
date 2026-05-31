# per_file granularity 陷阱（v4.30）

## 问题描述

`cluster_candidates.py` 的 `--granularity` 参数有两个选项：`by_type`（正确）和 `per_file`（陷阱）。

当 granularity=per_file 时，**每个输入文件独立成一个 cluster**，文件内容完全不被语义分析。N 个候选文件 → N 个 cluster。如果每个候选类型文件内包含 2 个 entry（header 元数据块 + body 内容块），会产生大量单成员 cluster，每个候选被罚 `single_member_cluster`（-20分），导致 score 归零。

## 触发场景

execute_code 从 chapters/*.txt 提取候选时，每个候选类型生成一个文件：
- `candidates/frameworks.md`（含多个 fw-XX entry）
- `candidates/principles.md`（含多个 pr-XX entry）
- `candidates/cases.md`（含多个 ca-XX entry）
- ...

如果此时用 `per_file` granularity 运行聚类，每个文件变成一个 cluster（而不是按语义合并），产生大量单成员 cluster。

## 判断信号

```json
// clusters.json
{
  "total_clusters": 40,
  "per_file_clusters": 40,     // ← per_file 模式的印记
  "single_member_count": 40,
  "single_member_ratio": 1.0,
  "suggested_merge_count": 0
}

// candidate_scores.json
{
  "grade_distribution": {"A": 3, "B": 17, "C": 0, "D": 20},
  "average_score": 0.0        // ← 全被 penalty 归零
}
// penalty_breakdown 包含大量 single_member_cluster（-20分/个）
```

## 修复步骤

**不需要手动编组回退，直接重跑 pipeline：**

```bash
# 1. 用 by_type granularity 重新聚类
python3 scripts/cluster_candidates.py \
  --input candidates/ \
  --output clusters.json \
  --granularity by_type

# 2. 重新跑完整 pipeline
python3 scripts/pipeline_phase2.py candidates/ <output_dir>/
```

`by_type` 按候选内容语义分组（framework+procedure 合并、case+boundary 合并），生成的 cluster 有实质内容，无单成员惩罚。

## 根因代码位置

`scripts/cluster_candidates.py` 中 granularity 参数的默认值或传入逻辑。pipeline_phase2.py 调用时如果未明确传 `--granularity by_type`，可能默认用 per_file。

## 预防

pipeline_phase2.py 调用 cluster_candidates.py 时应明确传 `--granularity by_type`，不应该依赖默认值。
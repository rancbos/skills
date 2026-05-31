# Pitfall 7：粗体格式正则不匹配（v4.62）

## 问题

子代理输出 candidates 时使用 `- **id**: BUF-E1-001` 粗体格式，但三个脚本的正则只匹配 `- id: BUF-E1-001` 非粗体格式。

## 受影响的脚本与函数

| 脚本 | 函数 | 原正则 | 修复后 |
|------|------|--------|--------|
| `validate_candidates.py` | `parse_entries()` | `re.split(r"\n(?=-?\s*id\s*:\s+)", ...)` | `re.split(r"\n(?=-?\s*\*{0,2}\s*id\s*\*{0,2}\s*:\s+)", ...)` |
| `validate_candidates.py` | `parse_entries()` | `re.search(r"-?\s*id\s*:\s*(\S+)", block)` | `re.search(r"-?\s*\**\s*id\s*\**\s*:\s*(\S+)", block)` |
| `cluster_candidates.py` | `read_candidates()` | `re.split(r"\n(?=\s*-?\s*id\s*:\|##\s+)", ...)` | `re.split(r"\n(?=\s*-?\s*\*{0,2}\s*id\s*\*{0,2}\s*:\|##\s+)", ...)` |
| `score_candidates.py` | `read_candidates()` | `re.split(r"\n(?=\s*-?\s*id\s*:\|##\s+)", ...)` | `re.split(r"\n(?=\s*-?\s*\*{0,2}\s*id\s*\*{0,2}\s*:\|##\s+)", ...)` |

## 症状

- `--dry-run` 显示 `count=62, ok=true`（因为 dry-run 调用 `cluster_candidates.read_candidates`，已修复）
- 正式 pipeline 输出 `[validate] ok=False, total_entries=0` 或 `[score] candidates=9`（远少于实际候选数）
- `clusters.json` 中 `cluster_count` 可能正确（因为 cluster 阶段用了修复后的 read_candidates），但 `candidate_scores.json` 只有少量条目

## 诊断

```python
# 快速诊断：对比三个脚本的候选读取数
import sys
sys.path.insert(0, 'scripts')
from cluster_candidates import read_candidates as rc_cluster
from pathlib import Path

cdir = Path('/path/to/candidates')
items = rc_cluster(cdir)
print(f'cluster read_candidates: {len(items)}')

# 如果 cluster 读到 62 但 pipeline 只处理 9 个 → validate/score 脚本的正则有问题
```

## 修复

对三个文件分别 patch：

```python
# validate_candidates.py — parse_entries() 中两处
# 1. split 正则
raw_blocks = re.split(r"\n(?=-?\s*\*{0,2}\s*id\s*\*{0,2}\s*:\s+)", "\n" + text)
# 2. search 正则
m = re.search(r"-?\s*\**\s*id\s*\**\s*:\s*(\S+)", block)

# cluster_candidates.py — read_candidates() 中一处
blocks = re.split(r"\n(?=\s*-?\s*\*{0,2}\s*id\s*\*{0,2}\s*:|##\s+)", "\n" + text)

# score_candidates.py — read_candidates() 中一处
blocks = re.split(r"\n(?=\s*-?\s*\*{0,2}\s*id\s*\*{0,2}\s*:|##\s+)", "\n" + text)
```

## 根因

三个脚本在 v4.22+ 架构切换时更新了 `read_candidates` 函数以支持 `- **id**:` 粗体格式（`extract_field` 已支持），但 `re.split()` 分割 blocks 的正则仍然只匹配非粗体的 `- id:`。由于 split 在前、extract_field 在后，blocks 被错误合并，导致大量候选被跳过。

## 验证

修复后运行完整 pipeline：

```bash
python3 scripts/pipeline_phase2.py candidates/ output/
# 预期：[validate] total_entries=62, [score] candidates=62
```

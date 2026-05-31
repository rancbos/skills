# cluster_candidates.py 参数陷阱

`cluster_candidates.py` 的 CLI 参数设计与 `score_candidates.py` 语义相反，容易混淆。

## CLI 用法对比

| 脚本 | 参数1 | 参数2 | 参数3 |
|---|---|---|---|
| `cluster_candidates.py` | candidates 目录 | **clusters.json 文件路径** | — |
| `score_candidates.py` | candidates 目录 | clusters.json 文件路径 | candidate_scores.json 文件路径 |
| `build_summary_plan.py` | clusters.json 文件路径 | scores.json 文件路径 | summary_plan.json 文件路径 |

## cluster_candidates.py 参数详情

```
python scripts/cluster_candidates.py <candidates_dir> <out_json>
```

- 参数1（candidates_dir）：candidates 文件所在目录
- 参数2（out_json）：**输出文件路径**，不是目录

若误将第二个参数传为目录路径（如 `candidates`），会触发：

```
IsADirectoryError: [Errno 21] Is a directory: '.../candidates'
```

## 正确调用示例

```bash
cd /home/jw/books/聪明的投资者-本杰明·格雷厄姆/聪明的投资者-本杰明·格雷厄姆
python3 /home/jw/.hermes/skills/jw-content-summary/scripts/cluster_candidates.py candidates clusters.json
```

## 预防

每个脚本第一次运行时查 header 确认：
```bash
head -20 /home/jw/.hermes/skills/jw-content-summary/scripts/cluster_candidates.py
```

不要类比其他脚本的参数顺序。用 `scripts/cluster_candidates.py --help` 确认。
# delegate_task 输出格式陷阱

> 来源：2026-06-01 巴菲特致股东的信总结实战。3 个脚本 bug 导致 3 次 pipeline 重跑，浪费 ~330K tokens + 10 分钟。

## 问题 1：extract_field 不支持粗体格式

子代理生成的 candidates 格式：`- **type**: framework`（带 `**` 粗体标记）

脚本的 `extract_field` 正则只匹配 `- type: framework`（不带 `**`），导致所有字段无法解析。

**影响**：cluster_candidates.py、score_candidates.py、validate_candidates.py 三个脚本全部受影响。

**修复**：正则从 `r"^\s*-?\s*{name}\s*:\s*(.+)$"` 改为 `r"^\s*-?\s*\**\s*{name}\s*\**\s*:\s*(.+)$"`

**预防**：运行完整 pipeline 前先用 `--dry-run` 测试解析。

## 问题 2：read_candidates 将标题行解析为候选

candidates 文件第一行是 `# Boundary Candidates — 书名`，被 read_candidates 解析为一个空候选（无 keywords、无 source_quote），导致分数为 0。

**修复**：增加字段存在性检查——`if not has_id and not has_source_chapter and not has_type: continue`

## 问题 3：字段检查不支持粗体格式

`"id:" not in block` 检查不匹配 `- **id**: b01`，导致修复问题 1 后反而所有候选被过滤掉（0 个）。

**修复**：改用正则表达式检查 `bool(re.search(r"^\s*-?\s*\**\s*id\s*\**\s*:", block, re.M))`

## 格式规范

delegate_task 子代理输出 candidates 时，字段行必须符合以下格式之一：
- `- field: value`（标准格式）
- `- **field**: value`（粗体格式，脚本支持）

**禁止**：
- `field：value`（全角冒号 `：`）
- `**field**：value`（粗体 + 全角冒号）

## dry-run 预检

```bash
# 正式运行前先测试解析
python3 scripts/pipeline_phase2.py <candidates_dir> <output_dir> --dry-run

# 预期输出：ok=true, count=60, types={framework: 15, principle: 18, ...}
# 如果 count=0 或 ok=false，检查候选文件格式
```

## Token 节省

| 优化项 | 节省 Token | 原理 |
|--------|-----------|------|
| dry-run 预检 | ~330K | 避免 3 次 bug 修复循环 |
| context 嵌入 stage1 | ~150K | 4 个子代理不再各自读取 stage1-understanding.md |
| context 嵌入 chapters 关键段落 | ~100K | 减少重复文件读取 |

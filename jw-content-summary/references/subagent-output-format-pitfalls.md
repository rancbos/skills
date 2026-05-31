# 子代理输出格式陷阱

## 问题描述

delegate_task 子代理生成的 candidates 文件格式与脚本预期不匹配，导致 pipeline 全部返回 0 候选或 0 分。

## 根因链

1. 子代理输出格式：`- **type**: framework`（Markdown 粗体）
2. 脚本 extract_field 正则：`r"^\s*-?\s*{name}\s*:\s*(.+)$"`（不支持 `**`）
3. 结果：所有字段解析失败，candidate_count=0

## 三个具体 Bug

### Bug 1: extract_field 不支持粗体格式
- **文件**：cluster_candidates.py、score_candidates.py、validate_candidates.py
- **修复**：正则改为 `r"^\s*-?\s*\**\s*{name}\s*\**\s*:\s*(.+)$"`
- **验证**：`python3 -c "import re; print(bool(re.search(r'^\s*-?\s*\**\s*type\s*\**\s*:\s*(.+)$', '- **type**: framework', re.M)))"`

### Bug 2: read_candidates 将标题行解析为候选
- **现象**：`# Boundary Candidates — 巴菲特致股东的信` 被解析为 id="boundaries-0" 的空候选
- **修复**：增加字段存在性检查——block 必须包含 id/source_chapter/type 字段之一
- **判断信号**：candidate_scores.json 中出现 id 以 `-0` 结尾、keywords=[] 的条目

### Bug 3: 字段检查使用字符串匹配而非正则
- **现象**：`"id:" not in block` 不匹配 `- **id**: b01`
- **修复**：改用 `re.search(r"^\s*-?\s*\**\s*id\s*\**\s*:", block, re.M)`
- **关键**：必须同时修复 cluster_candidates.py 和 score_candidates.py 的 read_candidates 函数

## 预防措施

1. **dry-run 预检**：运行 `pipeline_phase2.py <candidates_dir> <output_dir> --dry-run` 测试解析
2. **格式规范**：在 methodology/02 中明确要求子代理输出格式（支持 `- field:` 和 `- **field**:` 两种）
3. **单元测试**：用 1-2 个真实候选文件测试 extract_field，再运行完整 pipeline

## 实战案例

《巴菲特致股东的信》总结时：
- 第 1 次 pipeline：avg=0（extract_field 不支持粗体）
- 第 2 次 pipeline：0 候选（字段检查不支持粗体 → 全部过滤）
- 第 3 次 pipeline：68 候选但全垃圾（标题行被解析为候选）
- 第 4 次 pipeline：60 候选 avg=67.17（全部修复后正常）

每次修复后重跑 pipeline 约 3 分钟 + 100K tokens，3 次循环浪费 9 分钟 + 300K tokens。

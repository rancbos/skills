# Candidates 子代理输出格式陷阱（v4.60 发现）

## 问题

子代理生成的 candidates 文件使用 `**粗体**` 格式标记字段名：

```markdown
- **id**: b01
- **title**: 基于货币的资产是"最危险的安全资产"
- **type**: boundary
- **source_chapter**: ch012 投资替代品
```

但 `cluster_candidates.py`、`score_candidates.py`、`validate_candidates.py` 的解析正则期望的是无粗体格式：

```markdown
- id: b01
- title: 基于货币的资产
- type: boundary
```

## 修复（v4.60 已修复）

三个脚本的 `extract_field` 和字段检查正则已更新，支持 `\**` 粗体标记：

```python
# 旧正则（不支持粗体）
m = re.search(rf"^\s*-?\s*{re.escape(name)}\s*:\s*(.+)$", text, re.M)

# 新正则（支持粗体）
m = re.search(rf"^\s*-?\s*\**\s*{re.escape(name)}\s*\**\s*:\s*(.+)$", text, re.M)
```

## 另一个陷阱：标题行被解析为候选

子代理文件首行通常是标题（如 `# Boundary Candidates — 巴菲特致股东的信`），会被 `read_candidates` 解析为一个空候选。

**修复**：增加字段存在性检查——如果 block 没有 `id:`、`source_chapter:` 和 `type:` 字段，跳过该 block。

## 影响范围

以下脚本已修复：
- `cluster_candidates.py` — read_candidates + extract_field
- `score_candidates.py` — read_candidates + extract_field
- `validate_candidates.py` — parse_entries

## 版本

v4.60 发现并修复。子代理输出格式应统一使用 `- **field**: value` 或 `- field: value`，两种格式现在都被支持。

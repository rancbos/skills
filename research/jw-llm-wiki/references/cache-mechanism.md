# 缓存机制详解

## 概述

缓存机制是 jw-llm-wiki 的核心优化之一，用于避免重复处理相同素材，显著降低 token 消耗。

**收益估算：**
- 首次处理：消耗约 2000-3000 tokens
- 缓存命中：消耗约 100-200 tokens（仅读取已有结果）
- 节省：50-80% 的 token 消耗

## 工作原理

```
用户提供素材
    ↓
计算素材 MD5 hash
    ↓
查询 .wiki-cache.json
    ↓
├─ HIT（hash 匹配）→ 跳过处理，直接返回已有结果
└─ MISS（无记录或 hash 不同）→ 执行完整处理流程
    ↓
处理成功后更新缓存
```

## 缓存文件结构

**位置：** `$WIKI_PATH/.wiki-cache.json`

**格式：**
```json
{
  "/path/to/raw/file.md": {
    "hash": "abc123...",
    "size": 12345,
    "mtime": 1622505600,
    "updated": "2026-05-30T16:00:00+08:00",
    "source_page": "wiki/sources/2026-05-30-素材标题.md"
  }
}
```

**字段说明：**
- `hash`：素材文件的 MD5 hash
- `size`：文件大小（字节）
- `mtime`：文件修改时间（时间戳）
- `updated`：缓存更新时间
- `source_page`：对应的 wiki source 页面路径

## 使用方法

### 1. 检查缓存状态

```bash
bash ${SKILL_DIR}/scripts/cache.sh check "<raw文件路径>"
```

**返回值：**
- `HIT` → 缓存命中，跳过处理
- `MISS:no_entry` → 首次处理此素材
- `MISS:hash_changed` → 素材内容有变化，需要重新处理
- `MISS:file_not_found` → 文件不存在

### 2. 更新缓存

```bash
bash ${SKILL_DIR}/scripts/cache.sh update "<raw文件路径>"
```

**使用时机：**
- 完整处理流程成功后
- 简化处理流程成功后

### 3. 删除缓存

```bash
bash ${SKILL_DIR}/scripts/cache.sh invalidate "<raw文件路径>"
```

**使用时机：**
- 删除素材时
- 素材文件被移动或重命名时

### 4. 查看缓存状态

```bash
bash ${SKILL_DIR}/scripts/cache.sh status
```

## 集成到工作流

### Ingest 工作流

```
1. 缓存检查 ← 新增步骤
   ↓
   ├─ HIT → 跳过处理，直接返回
   └─ MISS → 继续处理
2. 捕获原始来源
3. 保存到 raw/
4. 分析内容
5. 创建/更新 wiki 页面
6. 更新 index.md 和 log.md
7. 更新缓存 ← 新增步骤
8. 报告变更
```

### Delete 工作流

```
1. 识别目标素材
2. 扫描影响范围
3. 安全确认
4. 执行级联清理
5. 清理缓存 ← 新增步骤
6. 断链检查
7. 报告结果
```

## 最佳实践

### 1. 始终先检查缓存
在处理任何素材前，先运行缓存检查。这可以节省大量 token。

### 2. 处理成功后更新缓存
只有在完整处理流程成功后才更新缓存。如果处理失败，不要更新缓存。

### 3. 删除素材时清理缓存
避免缓存中保留已删除素材的记录。

### 4. 定期检查缓存状态
使用 `cache.sh status` 查看缓存状态，清理无效条目。

## 故障排除

### 问题：缓存命中但内容已变化

**原因：** 素材文件被修改，但 hash 计算错误

**解决：**
```bash
# 强制更新缓存
bash ${SKILL_DIR}/scripts/cache.sh invalidate "<raw文件路径>"
bash ${SKILL_DIR}/scripts/cache.sh update "<raw文件路径>"
```

### 问题：缓存文件损坏

**原因：** .wiki-cache.json 格式错误

**解决：**
```bash
# 删除缓存文件，重新开始
rm $WIKI_PATH/.wiki-cache.json
```

### 问题：缓存脚本找不到 WIKI_PATH

**原因：** 环境变量未设置

**解决：**
```bash
# 设置环境变量
export WIKI_PATH=/root/wiki-ai
# 或在 ~/.hermes/.env 中添加
echo "WIKI_PATH=/root/wiki-ai" >> ~/.hermes/.env
```

## 性能对比

### 无缓存

```
处理 10 个素材：
- 首次处理：10 × 2500 tokens = 25,000 tokens
- 重复处理：10 × 2500 tokens = 25,000 tokens
- 总计：50,000 tokens
```

### 有缓存

```
处理 10 个素材（5 个已处理过）：
- 首次处理：5 × 2500 tokens = 12,500 tokens
- 缓存命中：5 × 150 tokens = 750 tokens
- 总计：13,250 tokens
- 节省：73.5%
```

## 未来改进

### 1. 分布式缓存
支持多机共享缓存（通过 Git 或共享存储）。

### 2. 缓存预热
在批量处理前，预先计算所有素材的 hash。

### 3. 缓存统计
记录缓存命中率、节省的 token 数等统计信息。

### 4. 缓存过期
自动清理长期未使用的缓存条目。

# 删除工作流详解

> 版本: v3.0.0
> 更新: 2026-05-30

## 概述

删除工作流提供安全的素材删除机制，避免断链和数据丢失。支持扫描影响、安全删除和归档三种操作。

## 工作流程

```
扫描删除影响
    ↓
评估风险级别
    ↓
修复引用页面
    ↓
选择操作方式
    ↓
安全删除 或 归档
    ↓
更新 index.md 和日志
```

## 使用方法

### 扫描删除影响

```bash
# 扫描删除影响
bash delete-helper.sh scan entities/invest/old-book.md

# 输出示例：
# === 删除影响扫描 ===
# 目标文件: entities/invest/old-book.md
# 文件名: old-book
# 
# === 引用此文件的页面 ===
# 引用数量: 3
# 
# 引用页面:
#   - entities/invest/new-book.md
#   - concepts/value-investing.md
#   - entities/invest/buffett.md
# 
# === 此文件引用的页面 ===
# 引用数量: 2
# 
# 引用的页面:
#   - [[warren-buffett]] ✓
#   - [[charlie-munger]] ✓
# 
# === index.md 引用 ===
# ⚠️  index.md 中包含对此文件的引用
# 45: - [[old-book]] 旧的投资书
# 
# === 关联 raw 文件 ===
# 关联的 raw 文件:
#   - raw/articles/old-book.md ✓
# 
# === 风险评估 ===
# 风险级别: 中
# 风险原因: 被 3 个页面引用 在 index.md 中有引用
# 
# === 建议 ===
# ⚠️  中风险删除，建议：
# 1. 检查引用页面是否需要更新
# 2. 从 index.md 移除引用
# 3. 考虑归档: bash delete-helper.sh archive 'entities/invest/old-book.md'
# 4. 如确认删除，使用: bash delete-helper.sh delete 'entities/invest/old-book.md'
```

### 安全删除

```bash
# 安全删除
bash delete-helper.sh delete entities/invest/old-book.md

# 输出示例：
# === 安全删除 ===
# 目标文件: entities/invest/old-book.md
# 
# ⚠️  发现引用，需要先修复：
#   - entities/invest/new-book.md
#   - concepts/value-investing.md
#   - entities/invest/buffett.md
# 
# 请先修复引用，或使用归档: bash delete-helper.sh archive 'entities/invest/old-book.md'
```

**删除流程：**
1. **检查引用**: 如果有引用，拒绝删除
2. **从 index.md 移除**: 删除 index.md 中的引用
3. **删除文件**: 删除目标文件
4. **清理空目录**: 如果父目录为空，删除父目录

### 归档而非删除

```bash
# 归档文件
bash delete-helper.sh archive entities/invest/old-book.md

# 输出示例：
# === 归档文件 ===
# 原位置: entities/invest/old-book.md
# 归档位置: /root/wiki-ai/_archive/entities/invest/old-book.md
# 
# 更新 index.md...
# 更新引用页面...
#   - entities/invest/new-book.md
#   - concepts/value-investing.md
#   - entities/invest/buffett.md
# 
# ✅ 归档完成
# 文件已移动到: /root/wiki-ai/_archive/entities/invest/old-book.md
# 引用已更新为: [已归档] old-book
```

**归档流程：**
1. **创建归档目录**: 确保 `_archive/` 目录存在
2. **移动文件**: 保持目录结构移动到归档目录
3. **更新 index.md**: 将引用更新为 [已归档]
4. **更新引用页面**: 将所有引用更新为 [已归档]

### 列出孤儿页面

```bash
# 列出孤儿页面
bash delete-helper.sh orphan

# 输出示例：
# === 孤儿页面 ===
# 
# 孤儿页面数量: 72
# 
# 孤儿页面列表:
#   - entities/fajia/shenzi2.md
#   - entities/fajia/jianzhukeshu.md
#   - entities/fo/amituojing.md
#   ...
# 
# 建议：
# 1. 为孤儿页面添加交叉引用
# 2. 合并内容到相关页面
# 3. 归档不再需要的页面
```

## 风险评估

### 风险级别

| 级别 | 条件 | 建议 |
|------|------|------|
| 高 | 被 5+ 页面引用 | 强烈建议归档 |
| 中 | 被 1-5 页面引用 | 建议归档 |
| 低 | 无引用 | 可安全删除 |

### 风险因素

1. **引用数量**: 被引用越多，风险越高
2. **index.md 引用**: 在 index.md 中有引用，风险增加
3. **核心页面**: 如果是核心页面（如 warren-buffett），风险极高
4. **raw 文件关联**: 如果有关联的 raw 文件，需要考虑是否删除

## 最佳实践

### 1. 优先归档而非删除

```bash
# 优先使用归档
bash delete-helper.sh archive entities/invest/old-book.md

# 只有在确定不需要时才删除
bash delete-helper.sh delete entities/invest/old-book.md
```

**原因：**
- 归档保留了数据，可以恢复
- 删除是不可逆的
- 归档更新了引用，避免断链

### 2. 删除前先修复引用

```bash
# 先扫描影响
bash delete-helper.sh scan entities/invest/old-book.md

# 修复引用页面
# 1. 更新引用为其他页面
# 2. 或删除引用
# 3. 或标记为 [已归档]

# 确认无引用后删除
bash delete-helper.sh delete entities/invest/old-book.md
```

### 3. 定期清理孤儿页面

```bash
# 每月检查一次孤儿页面
bash delete-helper.sh orphan

# 处理孤儿页面：
# 1. 添加交叉引用
# 2. 合并到相关页面
# 3. 归档不再需要的页面
```

### 4. 与备份结合

```bash
# 删除前先备份
bash wiki-backup.sh backup

# 然后删除
bash delete-helper.sh delete entities/invest/old-book.md

# 如果误删，可以从备份恢复
```

## 常见问题

### Q: 如何恢复已删除的文件？

A: 已删除的文件无法恢复，除非：
1. **从备份恢复**: 使用备份工具恢复
2. **从 Git 恢复**: 如果使用 Git 版本控制
3. **从归档恢复**: 如果之前归档过

**建议：** 删除前先备份或归档。

### Q: 如何处理大量孤儿页面？

A: 对于大量孤儿页面：
1. **批量添加引用**: 为孤儿页面添加交叉引用
2. **批量合并**: 将相关孤儿页面合并
3. **批量归档**: 归档不再需要的孤儿页面

**示例：**
```bash
# 列出所有孤儿页面
bash delete-helper.sh orphan > orphans.txt

# 批量归档
while read -r file; do
  bash delete-helper.sh archive "$file"
done < orphans.txt
```

### Q: 如何删除整个分类？

A: 删除整个分类需要谨慎：
1. **扫描所有文件**: 确认所有文件都可以删除
2. **修复所有引用**: 更新所有引用页面
3. **批量归档**: 归档整个分类目录
4. **更新 index.md**: 移除整个分类的引用

**示例：**
```bash
# 扫描整个分类
for file in entities/old-category/*.md; do
  bash delete-helper.sh scan "$file"
done

# 批量归档
for file in entities/old-category/*.md; do
  bash delete-helper.sh archive "$file"
done
```

### Q: 如何处理循环引用？

A: 循环引用是指 A 引用 B，B 引用 A 的情况：
1. **识别循环引用**: 扫描时注意循环引用
2. **打破循环**: 删除其中一个引用
3. **然后删除**: 安全删除文件

**示例：**
```bash
# 扫描时发现循环引用
bash delete-helper.sh scan entities/a.md
# 输出: entities/b.md 引用了此文件

bash delete-helper.sh scan entities/b.md
# 输出: entities/a.md 引用了此文件

# 打破循环：删除 a.md 对 b.md 的引用
# 然后删除 a.md
```

## 高级功能

### 1. 批量删除

```bash
# 批量删除文件
for file in file1.md file2.md file3.md; do
  bash delete-helper.sh delete "$file"
done
```

### 2. 条件删除

```bash
# 删除特定条件的文件
find entities/ -name "*.md" -mtime +90 -exec bash delete-helper.sh delete {} \;
```

### 3. 删除日志

```bash
# 记录删除操作
echo "$(date): Deleted entities/invest/old-book.md" >> delete.log

# 查看删除历史
cat delete.log
```

### 4. 删除验证

```bash
# 验证删除是否成功
if [ ! -f "entities/invest/old-book.md" ]; then
  echo "删除成功"
else
  echo "删除失败"
fi
```

## 安全注意事项

1. **删除不可逆** - 删除的文件无法恢复，除非有备份
2. **先备份** - 删除前先备份或归档
3. **修复引用** - 删除前先修复所有引用页面
4. **验证影响** - 删除前先扫描影响，评估风险
5. **记录操作** - 记录所有删除操作，便于审计

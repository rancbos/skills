# Skill 审计方法论

> 来源：jw-company-analysis v3.60.8 全量审计（2026-06-07）
> 用途：对大型 skill 进行系统性健康检查，发现问题并执行修复

## 审计五步法

### Step 1：版本一致性检查（五端）

大型 skill 通常有多个文件携带版本号，必须保持一致：

| 位置 | 检查方法 |
|------|---------|
| SKILL.md frontmatter | `grep -m1 'version:' SKILL.md` |
| SKILL.md 标题 | `grep '# 技能名' SKILL.md` |
| templates/*.md | `grep -oP 'v\d+\.\d+\.\d+' templates/*.md` |
| scripts/*.py | `grep -oP 'v\d+\.\d+\.\d+' scripts/*.py` |
| references/checkpoint-schema.md | `grep 'version' references/checkpoint-schema.md` |

**格式注意**：frontmatter 中 `version: v3.60.7` 和 `version: 3.60.7` 都是合法的，但必须统一。建议统一使用 `vX.Y.Z` 格式。

### Step 2：脚本路径一致性检查

大型 skill 通常依赖外部脚本，路径必须一致：

```bash
# 检查 SKILL.md 中的路径
grep -oP '~/.hermes/skills/[^/]+' SKILL.md | sort -u

# 检查 scripts/*.py 中的路径
grep -oP '~/.hermes/skills/[^/]+' scripts/*.py | sort -u
```

**常见问题**：SKILL.md 使用 `~/.hermes/skills/rancbos-skills/` 但脚本使用 `~/.hermes/skills/`（缺少 rancbos-skills）。

### Step 3：References 文件健康检查

检查 SKILL.md 中引用的文件是否都存在：

```bash
for ref in $(grep -oP 'references/[a-zA-Z0-9_-]+\.md' SKILL.md | sort -u); do
    [ ! -f "$ref" ] && echo "❌ 引用的文件不存在：$ref"
done
```

### Step 4：孤儿文件检查

检查 references/ 中是否有文件未被 SKILL.md 引用：

```bash
for f in references/*.md; do
    base=$(basename "$f")
    grep -q "$base" SKILL.md || echo "⚠️ 未被引用：$base"
done
```

**处理原则**：
- 被其他 references 间接引用 → 保留
- 纯维护文档（如 version-history.md）→ 移出 references/
- 内容已被其他文件覆盖 → 删除
- 内容全部是引用中转站 → 删除

### Step 5：内容混入检查

检查是否有文件混入了不属于它的内容：

```bash
# 检查 industry-calibration.md 是否混入了数据源分层表
head -20 references/industry-calibration.md | grep -q "数据源" && echo "⚠️ 混入数据源内容"
```

## 执行顺序

1. 先执行 Step 1-5 诊断
2. 按 P0/P1/P2 分级：
   - P0：执行会出错（路径错误/版本不一致）
   - P1：逻辑混淆（内容混入/引用缺失）
   - P2：可优化（孤儿文件/冗余内容）
3. 一次性修复所有问题（用户偏好"全量执行"）
4. 运行自动化检查脚本验证

## 自动化检查脚本

大型 skill 应维护一个 `scripts/audit_consistency.sh`，包含上述检查步骤，每次修改后自动运行。

脚本模板：
```bash
#!/bin/bash
# 版本一致性 + 路径一致性 + 文件健康 + 标题一致性
# 详见本文件的审计五步法
```

---

## ⚠️ 关键 Pitfall

### Pitfall 1：write_file 导致文件损坏（行号前缀污染）— P0

**现象**：使用 `read_file` 读取内容后做字符串替换，再用 `write_file` 写回时，行号前缀（如 `1|1|1|1|`）被嵌入文件内容，导致文件严重损坏。

**根因**：`read_file` 的输出格式是 `LINE_NUM|CONTENT`（行号在前，用 `|` 分隔）。如果在 execute_code 中对 read_file 返回的 content 做字符串处理时未正确剥离行号前缀，这些前缀会被 write_file 原样写入文件。

**检测方法**：
```bash
head -5 SKILL.md | cat -v | grep '^[0-9]*|[0-9]*|'
# 如果输出包含 "1|1|1|1|" 这样的模式，说明文件已损坏
```

**修复方法**：
```bash
# 用 sed 剥离行号前缀（格式：N|N|N|N|content → content）
sed -i 's/^[0-9]*|[0-9]*|[0-9]*|[0-9]*|//' SKILL.md
```

**预防措施**：
1. **不要**在 execute_code 中对 read_file 的 content 做字符串处理后直接 write_file
2. **改为**使用 `terminal` 的 `cat` 命令读取原始内容，或使用 `patch` 工具做精确替换
3. 写入后立即验证文件前 5 行是否干净：`head -5 file | cat -v`

**实际案例**（jw-company-analysis v3.60.8）：
- 执行全量优化时，使用 execute_code 的 read_file + write_file 修改 SKILL.md
- 结果：SKILL.md 从正常的 ~600 行变成 ~500 行，每行前缀 `N|N|N|N|`
- 影响：bash 无法解析文件（报"未找到命令"），skill 完全不可用
- 修复：需要用 sed 剥离前缀，或从 git 历史恢复

### Pitfall 2：Shell 脚本被 write_file 损坏

**现象**：shell 脚本 (.sh) 被 write_file 写入后，开头出现行号前缀，导致 bash 无法执行。

**报错示例**：
```
/home/jw/.hermes/skills/.../audit_consistency.sh: 行 1: 1: 未找到命令
/home/jw/.hermes/skills/.../audit_consistency.sh: 行 2: 2: 未找到命令
```

**修复**：同 Pitfall 1，用 sed 剥离前缀后重新写入。

**预防**：对于 shell 脚本，优先使用 `terminal` 的 heredoc 方式写入，避免使用 write_file。

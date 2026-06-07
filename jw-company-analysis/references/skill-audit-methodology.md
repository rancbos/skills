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

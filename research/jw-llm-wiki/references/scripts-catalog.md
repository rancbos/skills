# 脚本目录

> jw-llm-wiki 的所有脚本及其功能说明。

## 工作流路由器（统一入口）

| 脚本 | 功能 | 用法 |
|------|------|------|
| `workflow-router.sh` | 统一入口，路由到各工作流 | `bash workflow-router.sh <action> [args...]` |

## 核心管线

| 脚本 | 功能 | 用法 |
|------|------|------|
| `cache.sh` | 素材缓存管理 | `check/update/invalidate/status` |
| `content-grading.sh` | 内容分级 | `grade/stats` |
| `validate-step1.sh` | Step 1 JSON 验证 | `bash validate-step1.sh <json_file>` |
| `create-source-page.sh` | 原子写入 + 缓存更新 | `bash create-source-page.sh <raw> <output> <content>` |
| `confidence-stats.sh` | 置信度统计 | `bash confidence-stats.sh <wiki_root>` |

## 健康检查

| 脚本 | 功能 | 用法 |
|------|------|------|
| `lint-runner.sh` | 机械检查 | `bash lint-runner.sh <wiki_root>` |
| `lint-fix.sh` | 自动修复 | `bash lint-fix.sh <wiki_root> [--dry-run]` |
| `source-signal-coverage.sh` | 来源覆盖检查 | `bash source-signal-coverage.sh <wiki_root> [--fix]` |

## 图谱与分析

| 脚本 | 功能 | 用法 |
|------|------|------|
| `build-graph-data.sh` | 图谱数据 + 自动洞察 | `bash build-graph-data.sh <wiki_root>` |
| `build-graph.sh` | Mermaid + HTML 可视化 | `bash build-graph.sh mermaid/html/stats` |

## 辅助工具

| 脚本 | 功能 | 用法 |
|------|------|------|
| `alias-manager.sh` | 别名管理 | `expand/search/list/get/add` |
| `crosslink.sh` | 自动跨链 | `bash crosslink.sh <wiki_root> [--full] [--dry-run]` |
| `crystallize.sh` | 结晶化工作流 | `save/list/process/stats/mark` |
| `digest.sh` | Digest 辅助 | `search/list/save` |
| `query-dedup.sh` | 查询去重 | `check/list/stats` |
| `delete-helper.sh` | 安全删除 | `scan/delete/archive/orphan` |
| `privacy-check.sh` | 隐私检查 | `scan/scan-dir/report` |
| `image-tracker.sh` | 图片追踪 | `scan/scan-dir/report` |
| `obsidian-cli.sh` | Obsidian CLI 集成 | `check/read/search/create/append/backlinks/tags` |

## 运维

| 脚本 | 功能 | 用法 |
|------|------|------|
| `migrate.sh` | 版本迁移 | `bash migrate.sh <from> <to> <wiki_root>` |
| `lib/common.sh` | 共享工具库 | `source "$SCRIPT_DIR/lib/common.sh"` |

## 共享工具库 (common.sh)

所有脚本都 source `lib/common.sh`，提供以下公共函数：

```bash
# 日志函数
log_info "message"    # 信息
log_ok "message"      # 成功
log_warn "message"    # 警告
log_error "message"   # 错误
log_verbose "message" # 详细（需 VERBOSE=true）

# 路径检测
detect_wiki_root [override]  # 检测 Wiki 根目录
validate_wiki_root <path>    # 验证目录结构

# 工具函数
check_dependency <cmd> [package]  # 检查依赖
safe_grep_count <pattern> <file>  # 安全的 grep -c
atomic_write <target> <content>   # 原子写入
```

## 工作流路由表

| 用户意图 | action | 调用的脚本 |
|----------|--------|-----------|
| URL/文件/"消化" | `ingest` | cache.sh, content-grading.sh, validate-step1.sh |
| "关于 XX"/"查询" | `query` | alias-manager.sh |
| "深度分析"/"综述" | `digest` | digest.sh |
| "检查"/"lint" | `lint` | lint-runner.sh, lint-fix.sh, source-signal-coverage.sh |
| "状态" | `status` | source-signal-coverage.sh |
| "图谱" | `graph` | build-graph-data.sh |
| "删除" | `delete` | delete-helper.sh |
| "结晶化" | `crystallize` | crystallize.sh |
| "跨链" | `crosslink` | crosslink.sh |
| "修复" | `fix` | lint-fix.sh |
| "隐私检查" | `privacy` | privacy-check.sh |
| "图片追踪" | `images` | image-tracker.sh |

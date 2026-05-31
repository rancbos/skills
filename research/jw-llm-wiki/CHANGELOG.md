# Changelog

本文件记录 jw-llm-wiki 的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [3.5.0] - 2026-05-30

### 新增
- `scripts/lib/common.sh` — 共享工具库（日志、路径检测、依赖检查）
- `scripts/workflow-router.sh` — 工作流路由器（统一入口）
- `CHANGELOG.md` — 版本变更记录

### 修复
- 统一所有脚本的 WIKI_PATH 命名
- 精简 SKILL.md（1133 → ~400 行），详细文档移至 reference 文件
- 强制两步处理流程的清晰集成点

### 优化
- 脚本现在 source lib/common.sh 获取公共功能
- 改进错误处理和日志输出
- 清理 reference 文件组织

## [3.4.0] - 2026-05-30

### 新增
- `scripts/crosslink.sh` — 自动跨链（增量/全量）
- `scripts/obsidian-cli.sh` — Obsidian CLI 集成

## [3.3.0] - 2026-05-30

### 新增
- `scripts/create-source-page.sh` — 原子写入 + 缓存更新
- `scripts/lint-fix.sh` — 自动修复低风险问题
- `scripts/image-tracker.sh` — 图片追踪
- `scripts/source-signal-coverage.sh` — 来源信号覆盖

## [3.2.0] - 2026-05-30

### 新增
- `scripts/build-graph-data.sh` — 图谱数据 + 自动洞察
- `scripts/digest.sh` — Digest 工作流辅助
- `scripts/query-dedup.sh` — 查询去重 + 自引用防护

## [3.1.0] - 2026-05-30

### 新增
- `scripts/validate-step1.sh` — Step 1 JSON 验证
- `scripts/lint-runner.sh` — 机械健康检查
- `templates/purpose-template.md` — 研究方向模板

### 优化
- 两步处理流程（Step 1 JSON 验证 + Step 2 页面生成）
- purpose.md 研究方向引导

## [3.0.0] - 2026-05-30

### 新增
- 内容分级处理（content-grading.sh）
- 隐私自查（privacy-check.sh）
- 知识图谱可视化（build-graph.sh）
- 结晶化工作流（crystallize.sh）
- 安全删除工作流（delete-helper.sh）

### 修复
- SCHEMA.md 数字更新（221 → 235）
- 死链修复（2 个）
- concept category 补全（4 个）

## [2.7.0] - 2026-05-29

### 新增
- 别名系统（alias-manager.sh）

### 优化
- 缓存机制（cache.sh）
- 置信度系统

## [2.4.0] - 2026-05-27

### 初始版本
- 基础 wiki 结构（entities/concepts/comparisons/queries）
- SCHEMA.md 规范
- index.md 索引
- log.md 日志
- 基本的 ingest/query/lint 工作流

---
name: jw-llm-wiki
description: "Karpathy's LLM Wiki：构建/查询互链式 Markdown 知识库。"
version: 3.7.2
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [wiki, knowledge-base, research, notes, markdown, rag-alternative]
    category: research
    related_skills: [obsidian, arxiv]
required_environment_variables:
  - WIKI_PATH
required_commands:
  - python3
  - grep
  - find
  - jq
---

# Karpathy's LLM Wiki

构建并维护一个持久的、可累积的知识库，以互链式 markdown 文件形式组织。

**分工原则：** 人类负责策展来源和指导分析方向。Agent 负责总结、交叉引用、归档和维护一致性。

## 激活条件

当用户执行以下操作时使用此技能：
- 要求创建、构建或启动 wiki / 知识库
- 要求将内容"加入知识库"、"收录到知识库"、"添加到知识库"
- 要求摄入、添加或处理来源到 wiki
- 要求 lint、审计或健康检查 wiki
- 在研究上下文中引用 wiki、知识库或"笔记"

## Wiki 位置

通过 `WIKI_PATH` 环境变量设置。未设置时默认 `~/wiki`。

## 工作流路由

**统一入口：** `bash ${SKILL_DIR}/scripts/workflow-router.sh <action> [args...]`

运行 `workflow-router.sh help` 查看所有可用 action。常用：
- `ingest <source>` — 摄入素材
- `query <question>` — 查询知识库
- `lint [--fix]` — 健康检查
- `status` — 查看状态

## 两步处理流程（Ingest 核心）

**必须执行两步流程，不要跳过 Step 1。**

### Step 1：结构化分析

Agent 执行结构化分析，输出 JSON 到 /tmp/step1.json，然后验证：
```bash
bash ${SKILL_DIR}/scripts/validate-step1.sh /tmp/step1.json
```

JSON 必须包含：`source_summary`, `entities`, `topics`, `connections`, `contradictions`, `new_vs_existing`

置信度：EXTRACTED（原文直接支持）| INFERRED（推断）| AMBIGUOUS（有歧义）| UNVERIFIED（背景知识）

### Step 2：页面生成

基于 Step 1 的 JSON 生成 wiki 页面：
- 新页面：满足阈值时创建（2+ 来源提及或核心内容）
- 已有页面：追加新信息，更新 `updated` 日期
- 交叉引用：每页至少 2 个出链
- 更新 index.md、log.md、缓存

## 核心操作

### 恢复已有 Wiki（每次会话必做）

读 SCHEMA.md → 读 index.md → 读 log.md 最后 20 行 → 验证 WIKI_PATH 结构

### 健康检查

```bash
bash ${SKILL_DIR}/scripts/workflow-router.sh lint "$WIKI_PATH"
bash ${SKILL_DIR}/scripts/workflow-router.sh lint --fix "$WIKI_PATH"
```

### 查询

```bash
bash ${SKILL_DIR}/scripts/alias-manager.sh expand "关键词"
search_files "关键词" path="$WIKI_PATH" file_glob="*.md"
```

## 参考文件

详细文档请参考 `references/` 目录下的文件（通过 skill_view 的 linked_files 自动发现）。

# Token 效率设计原则

> 从 jw-llm-wiki 多轮优化中提炼的经验。

## 核心原则

**SKILL.md 每次加载都消耗 token，必须保持精简。**

| 组件 | 加载时机 | 大小目标 |
|------|----------|----------|
| SKILL.md | 每次激活 | ~1000 token |
| Reference 文件 | 按需加载 | 无限制 |
| 脚本 | 按需加载 | 无限制 |

## 优化策略

### 1. 移动参考信息到 reference 文件

**可移动的内容：**
- 常见陷阱 → `references/common-pitfalls.md`
- 脚本目录 → `references/scripts-catalog.md`
- 架构规范 → `references/architecture.md`
- Frontmatter 规范 → `references/architecture.md`

**必须保留的内容：**
- 激活条件：告诉 Agent 什么时候激活
- 工作流入口：告诉 Agent 如何调用
- 核心流程：Agent 必须知道的最少步骤

### 2. 精简工作流路由

**不要在 SKILL.md 中列出所有 action，只保留常用 4 个：**
- `ingest` — 摄入素材
- `query` — 查询知识库
- `lint` — 健康检查
- `status` — 查看状态

其他 action 通过 `workflow-router.sh help` 查看。

### 3. 精简 JSON 示例

**不要在 SKILL.md 中展示完整 JSON 结构，只描述必需字段：**
```
JSON 必须包含：source_summary, entities, topics, connections, contradictions, new_vs_existing
```

### 4. 删除参考文件列表

skill_view 的 linked_files 会自动列出 reference 文件，不需要在 SKILL.md 中重复。

## 优化历程

| 版本 | SKILL.md token | 节省 | 主要优化 |
|------|---------------|------|----------|
| v3.5.0 | ~3050 | - | 基准 |
| v3.6.0 | ~1599 | -47% | 移动参考信息到 reference 文件 |
| v3.7.0 | ~951 | -68% | 精简工作流路由、JSON 示例、参考文件列表 |

## 长期收益

假设每天加载 SKILL.md 100 次：
- v3.5.0: 100 × 3050 = 305,000 token/天
- v3.7.0: 100 × 951 = 95,100 token/天
- 节省: 209,900 token/天 = ~6,297,000 token/月

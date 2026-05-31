# 整体流水线概述

## 三阶段流水线（当前版本）

```
预处理: 脚本建立全文索引（无 LLM token）→ preprocess/
阶段 1: 读取索引 + 结构路由 → stage1-understanding.md → 自动
阶段 2: execute_code 直接提取 candidates → candidates/ + clusters.json → 自动
阶段 2.5: 连接扫描（Luhmann Scan）→ luhmann_connections → 手动
阶段 3: 五问+压力测试+核心方法论+关联方法论 → SUMMARY.md → 自检交付
```

## 关键原则

**不压缩最终质量，只压缩中间阅读成本。**

- 脚本读全书，LLM 读证据
- 索引找证据，LLM 做判断
- 聚类减少重复，最终 SUMMARY 仍保留完整七段+压力测试+关联方法论输出

## 各阶段速查

| 阶段 | 核心动作 | 输入 | 输出 | 状态 |
|------|---------|------|------|------|
| **预处理** | `clean_text.py` + `build_book_index.py` 切章/抽片段/建索引 | 书本文本 | `preprocess/` | — |
| **1** | 读 `book-index.json`；判定类型；动态 extractor 路由 | preprocess | `stage1-understanding.md` | ✅ 自动 |
| **2** | `execute_code` 直接从 chapters 提取；`pipeline_phase2.py` 聚类评分 | 路由表 + chapters | `candidates/` + `clusters.json` + `summary_plan.json` | ✅ 自动 |
| **2.5** | Luhmann Scan：前置依赖/潜在连接/方法论发现 | candidates | `luhmann_connections` 字段 | 🔧 手动 |
| **3** | 五问+压力测试+核心方法论七段+关联方法论；`md_to_html.py` 同步生成 HTML | summary_plan + candidates | `SUMMARY.md` + `SUMMARY.html` | ✅ 自检交付 |

## 关键变更（相对 v3.8）

| 项目 | v3.8 | 当前版本 |
|------|------|-------|
| 阶段 2 提取 | 动态子代理 | execute_code 直接提取（子代理仅用于阶段 1/3） |
| 阶段 2 管道 | 4 脚本分步调用 | `pipeline_phase2.py` 统一管道 |
| 阶段 3 内容 | 五问+七段 | 五问+压力测试+七段+关联方法论 |
| 认知深度 | 无 | 费曼检验/案例保真/模糊词禁令/推理链审查/拓扑检验/阅读顺序 |
| 连接扫描 | 无 | 阶段 2.5 Luhmann Scan |
| 安全阀 | 无 | 候选>100 自动降级 |
| 闸口 | 用户确认 | 全量自动运行（v4.22 移除） |

## Token 节省预期（相对 v3.7）

| 优化 | 节省来源 | 预计节省 |
|------|---------|---------|
| 预处理索引 | 原文筛选由脚本完成 | 20-35% |
| glossary 脚本候选化 | 不再 LLM 全文读术语 | 10-20% |
| execute_code 替代子代理 | 消除子代理嵌套截断 | 10-30% |
| 软聚类 | 阶段 3 少读重复候选 | 10-20% |

整体在 v3.7 基础上预计再省 **25-40%**。

## 详细文件

- `scripts/clean_text.py` — 文本清洗（去噪/TOC检测/格式标准化）
- `scripts/build_book_index.py` — deterministic 预处理（切章/抽片段/建索引/书籍分类）
- `scripts/pipeline_phase2.py` — 统一管道（validate→cluster→score→plan）
- `scripts/validate_candidates.py` — 候选格式验证（schema/别名/字段完整性）
- `scripts/cluster_candidates.py` — 候选软聚类（多信号匹配+质量检测）
- `scripts/score_candidates.py` — 候选质量评分（A/B/C/D 分级）
- `scripts/build_summary_plan.py` — 生成 summary_plan.json（推荐/附录/弱候选）
- `scripts/validate_summary.py` — SUMMARY.md 交付前验证（五问/R段/I段/七段/压力测试/关联方法论）
- `scripts/md_to_html.py` — Markdown 转 HTML（暗色模式）
- `methodology/01-stage1-read-extract.md` — 阶段 1: 索引驱动结构路由
- `methodology/02-stage2-parallel-extract.md` — 阶段 2: execute_code 提取 + 管道
- `methodology/04-stage4-summarize.md` — 阶段 3: 单文件总结渲染（五问+压力测试+七段+关联方法论）

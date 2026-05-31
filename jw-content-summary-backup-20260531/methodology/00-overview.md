# 整体流水线概述

## 三阶段流水线（v3.8）

```
预处理: 脚本建立全文索引（无 LLM token）→ preprocess/
阶段 1: 读取索引 + 结构路由 → stage1-understanding.md → 自动
阶段 2: 动态子代理提取 + 统一 V1 补证 + 软聚类 → candidates/ + clusters.json → 自动
阶段 3: 单文件 SUMMARY 渲染 → SUMMARY.md → 自检交付
```

## 关键原则

**不压缩最终质量，只压缩中间阅读成本。**

- 脚本读全书，LLM 读证据
- 索引找证据，LLM 做判断
- 聚类减少重复，最终 SUMMARY 仍保留完整七段输出

## 各阶段速查

| 阶段 | 核心动作 | 输入 | 输出 | 状态 |
|------|---------|------|------|------|
| **预处理** | `build_book_index.py` 切章/抽片段/建索引 | 书本文本 | `preprocess/` | — |
| **1** | 读 `book-index.json`；判定类型；动态 extractor 路由 | preprocess | `stage1-understanding.md` | ✅ 自动 |
| **2** | 按需启动 2-5 个子代理；统一 V1 补证；软聚类 | 路由表 + snippets/chapters | `candidates/` + `clusters.json` | ✅ 自动 |
| **3** | 五问完整展开 + Top 方法论七段；md_to_html.py 同步生成 HTML | clusters/candidates | `SUMMARY.md` + `SUMMARY.html` | ✅ 自检交付 |

## 与 v3.7 的关键差异

| 项目 | v3.7 | v3.8 |
|------|------|------|
| 全文处理 | LLM 读取结构片段 | 脚本先建索引，LLM 读索引 |
| glossary | 仍可能拿全书 | 脚本候选术语 + LLM 解释 |
| extractor 数量 | 固定 5 个 | 动态 2-5 个 |
| V1 跨域验证 | 子代理切片内验证 | 主代理基于全文索引统一补证 |
| 去重 | 不去重 | 软聚类，不删除成员 |
| 快速导航 | 已删除（v4.12） | — |
| 数量闸门 | 已删除（v4.22，全量运行） | 全量展开，不中断确认 |

## Token 节省预期（相对 v3.7）

| 优化 | 节省来源 | 预计节省 |
|------|---------|---------|
| 预处理索引 | 原文筛选由脚本完成 | 20-35% |
| glossary 脚本候选化 | 不再 LLM 全文读术语 | 10-20% |
| 动态 extractor | 少跑无用子代理 | 10-30% |
| 软聚类 | 阶段 3 少读重复候选 | 10-20% |

整体在 v3.7 基础上预计再省 **25-40%**。

## 详细文件

- `scripts/build_book_index.py` — deterministic 预处理脚本
- `scripts/cluster_candidates.py` — 候选软聚类脚本
- `methodology/01-stage1-read-extract.md` — 阶段 1: 索引驱动结构路由
- `methodology/02-stage2-parallel-extract.md` — 阶段 2: 动态提取 + 统一验证 + 聚类
- `methodology/03-stage3-triple-verify.md` — 已合并（保留引用）
- `methodology/04-stage4-summarize.md` — 阶段 3: 单文件总结渲染

# Token Optimization Patterns (v4.68)

实战中发现的 token 消耗优化模式，基于巴菲特致股东的信（259章，1.29M字符）完整三阶段运行数据。

## 基准数据

| 阶段 | Input Tokens | Output Tokens | 耗时 |
|------|-------------|---------------|------|
| 阶段1 delegate_task | 743,832 | 6,090 | 136s |
| 阶段2 delegate_task | 2,873,640 | 24,309 | 535s |
| 阶段3 主代理 | ~50,000 | ~30,000 | ~120s |
| **总计** | **~3,672,472** | **~62,399** | **~880s** |

## 优化模式

### 模式1：SKILL.md Changelog 外移

**问题**：SKILL.md 前 219 行是 v4.54-v4.65 的完整 changelog，每次运行都加载到 LLM context，但对执行无指导作用。

**收益**：SKILL.md 546→334 行（-39%），每次运行减少 ~5K input tokens。

**做法**：changelog 追加到 `references/changelog.md`，SKILL.md 只保留一行引用 `> 完整版本历史见 references/changelog.md`。

### 模式2：book-index.json 段落截断

**问题**：`build_book_index.py` 输出的 `first_paragraphs` 和 `last_paragraphs` 可能很长（单段落 1000+ 字符），但阶段 1 只需要首段前 200 字符来判断书籍类型。

**收益**：book-index.json 从 255KB 降到 151KB（-40.6%），减少 ~100K input tokens。

**验证（v4.68）**：巴菲特书 pipeline 对比——未截断 vs 截断，输出完全一致：62 candidates, avg_score=89.52, 61 recommended, 1 appendix。

**做法**：
- `first_paragraphs` 截断到 200 字符（已验证：足够暴露章节主题词）
- `last_paragraphs` 删除（已验证：对 stage1 路由无帮助）

### 模式3：阶段 2 Context 嵌入强制化

**问题**：2-5 个 extractor 子代理各自独立读取 `stage1-understanding.md`，重复消耗 ~50K tokens × N。

**收益**：每个子代理减少 ~50K tokens，总计 100-200K tokens。

**做法**：主代理读取 stage1 后，将 §1 基本信息、§2 核心命题、§4 路由表嵌入 delegate_task 的 context 参数。**禁止**子代理独立读取 stage1-understanding.md。

### 模式4：阶段 2 按路由表定向读取（未实施）

**问题**：阶段 2 是最大 token 消耗者（2.87M）。execute_code 可能在读取所有章节而非按路由表定向读取。

**预期收益**：减少 40-60%（~1.1M-1.7M tokens）。

**做法**：确保 execute_code 严格按阶段 1 路由表传入章节列表，>50 章严格执行分批策略（每批 20-30 章）。

### 模式5：Changelog 去重 + 版本表裁剪（v4.67）

**问题**：`references/changelog.md` 因多次合并操作产生重复条目（v4.65-v4.54 各出现两次），539 行中有 72 行是重复。SKILL.md §12 版本表有 17 条目，超过"最近 10 个版本"的维护规则。

**收益**：changelog.md 539→467 行（-13%），SKILL.md 338→330 行。每次运行减少 ~2K input tokens。

**做法**：
- changelog.md：用 Python 正则拆分版本块，保留每个版本的最后出现，重建去重文件
- SKILL.md §12：裁至 10 条，旧版本参见 `references/changelog.md`
- methodology/04：删除过时 "Top 10 完整展开" 节

## 参考

- 巴菲特书实战数据：session 20260531_105916_c01fe9
- build_book_index.py 修改：`first_last_paras()` 函数
- methodology/02 修改：§子代理输入
- 截断验证数据：`references/book-index-truncation-validation.md`（pipeline 零质量损失）

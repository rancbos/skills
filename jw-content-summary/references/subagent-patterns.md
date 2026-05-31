# 子代理模式与替代方案

## 核心教训

**子代理的路径/格式不可控问题**：子代理（delegate_task）会写错 candidates 输出路径，或输出 markdown 而非 YAML schema，导致 validate 失败。**不要依赖子代理写 candidates 文件。**

## 两种执行路径

| 方式 | 确定性 | 适用阶段 | 风险 |
|---|---|---|---|
## §5：阶段 3 delegate_task 超时模式（v4.23 实测）

**现象**：子代理在阶段 3（SUMMARY.md 写作）频繁超时（600s），即使候选只有 30-50 个。子代理的 API call 数正常（5-25 次），但在 `write_file` SUMMARY.md 或读取大量候选人文本时卡住。

**根因**：阶段 3 需要读取全部 candidates + clusters + summary_plan + stage1-understanding，对 50 候选的书，子代理上下文消化量巨大。子代理的 600s 硬超时不够用。

**解决**：阶段 3 **不用 delegate_task**。主代理直接写 SUMMARY.md——主代理已经在上下文中持有 candidates 内容，省去子代理的重复加载开销。《投资中最简单的事》（50KB, 967行）用主代理写入耗时 <2min，《聪明的投资者》（25KB, 435行）同样。

**规则**：阶段 3 一律在主代理完成。delegate_task 仅用于阶段 1（理解分析）和阶段 2 candidates 提取的备选回退（execute_code 优先）。
| `execute_code` 直接生成 | 高 | 所有 candidates 生成 | 无 |

## 推荐策略

**Stage 2 candidates 生成用 `execute_code`**：
```python
# 从 chapters 文本直接提取，100% 确定性
# 输出 YAML 格式 candidates 文件
# 字段：- id:, source_line: (int), related: [], v3_pass: true
```
这是经过多轮失败后确认的最可靠方式。子代理的灵活性在 candidates 文件写入场景不值得那个风险。

## 子代理仍可用的场景

- Stage 1 的 `book-index.json` 分析（只读不写关键文件）
- Stage 3 的 SUMMARY 写作（输出单一 SUMMARY.md，风险低）

## V1 补证步骤（脚本模式必须执行）

`execute_code` 直接生成 candidates 时，子代理的 V1 跨域验证逻辑被绕过。**V1 补证不得跳过**，否则所有候选都是单证据来源。

完成 candidates 文件写入后，阶段 2 末尾主代理必须执行：

1. 读取 `book-index.json` 的 `snippets/quotes.json`、`snippets/cases.json`、`snippets/warnings.json`
2. 对每个候选的 `title` + `keywords` + `source_chapter`，在三个 snippets 中搜索第二证据
3. 找到则追加 `v1: {passed: true, evidence: [chXX: ...]}`；找不到则追加 `v1_status: weak`
4. V1 补证完成后再运行：`validate → cluster → score → build_summary_plan`

详见：`methodology/02-stage2-parallel-extract.md` 的「V1 跨域验证（主代理统一补证）」节。

## 失败日志（供参考）

1. 子代理写入 `/home/jw/candidates/` 而非书目录 → 迁移文件
2. 子代理输出 markdown 标题（`## case candidates`）而非 YAML `- id:` 格式 → validate 失败
3. 子代理加 format 指引后仍写错 schema → 改用 execute_code

见：`methodology/02-stage2-parallel-extract.md` 的原始子代理流程仅为参考，实际执行以本文件为准。

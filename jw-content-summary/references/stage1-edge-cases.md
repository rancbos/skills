# 阶段 1 边界案例与跳过判断

本文件记录阶段 1 结构路由的灰区案例。主文件 SKILL.md 只保留规则；具体诊断经验放在这里。

## 1. 阶段 1 可跳过的标准条件

同时满足以下条件时，可在预处理后跳过阶段 1，直接进入阶段 2：

1. 章节数 ≤15 且章节标题语义清晰
2. 书籍类型明确，非多册合集、非重复章节标题模式
3. 书籍主旨可以用一句话描述清楚
4. 书籍只有一种主要读法，无需通过四问区分不同阅读路径

审计记录示例：

```markdown
- **阶段 1 结构路由**: 未执行（预处理后跳过，书籍结构简单直接进入阶段 2）
```

## 2. 不能跳过的情况

- 多册合集，例如巴菲特致股东的信多册合并版
- 明显有多条阅读路径，例如同时面向防御型/进攻型投资者
- 章节结构不规则，目录和正文边界不清
- book_type_hint 与人工阅读判断冲突严重，且会影响 extractor 路由

## 3. 灰色地带：章节数 >15 但内容均匀

当章节数 >15，但内容实际均匀，可以由主代理判断跳过，但必须满足：

1. 确认章节数偏高是 TOC 污染或伪分割造成，而不是真实结构分歧
2. 确认书籍只有一种主要读法
3. 在 SUMMARY 审计区块注明争议理由
4. 如果章节结构显示存在多条阅读路径，不能跳过

审计记录示例：

```markdown
- **阶段 1 结构路由**: 跳过（章节数 N>15，但 toc_ratio=X 表明多数章节为 TOC 污染，内容均匀，单一读法）
```

## 4. 典型案例：《聪明的投资者》

特征：

- 68 章
- toc_ratio=0.186
- 约 12 个 TOC 条目混入正文
- 实际有效章节约 20 章

处理：

- 可跳过阶段 1
- 但必须记录争议原因
- 后续 extractor 路由以人工判断为准，不机械服从 book_type_hint

## 5. book_type_hint 人工复核

`compute_book_type_hint()` 基于结构密度指标推断书籍类型，但会误判。

常见误判：

| 脚本输出 | 真实类型 | 典型案例 |
|---|---|---|
| methodology_treatise | essay_collection（演讲/问答集） | 芒格之道 |
| essay_collection | methodology_treatise（体系化专著） | 聪明的投资者 |

处理：

1. 读取 `book-index.json` 的 `book_type_hint` 和 `structure_metrics`
2. 快速读前言、目录、任意一章首尾段
3. 人工判断与脚本不同，以人工为准
4. 在审计区块记录修正

审计记录示例：

```markdown
- **book_type_hint**: methodology_treatise（人工修正为：essay_collection）
```

## 6. TOC 空壳化

症状：

- `split_chapters()` 匹配目录页中的章节标题
- 正文被跳过或章节文件极小
- 大量 `chapters/*.txt` 小于 500 字节或 1KB

检查：

```bash
wc -c chapters/*.txt | sort -n | head
```

修复方向：

- 在 `split_chapters()` chapters loop 中过滤极短 body：`if len(body) < 50: continue`
- 或参考 `references/known-file-structures.md` 的多册合集/TOC 污染模式

验证：

```bash
wc -c chapters/*.txt | awk '$1 < 1000 {print "SMALL: " $0}'
```

## 7. 重跑时保留人工判断的规则

对已有 `stage1-understanding.md` 或 `SUMMARY.md` 的书重新跑流程时：

1. **先读旧 stage1-understanding.md**，提取已有人工判断（book_type、核心命题、extractor 路由）
2. **重建 book-index.json 后**，用旧判断覆盖 script 的 `book_type_hint`（脚本会误判）
3. **不要删旧 SUMMARY.md**，重跑完成后对比新旧质量
4. **旧 snippets 是 JSON 格式**（cases.json / definitions.json 等），新版脚本输出 .txt chapters；两者不兼容，阶段 2 必须用新版脚本生成的 txt chapters

典型场景：技能升级后，用新版重新处理旧书。

审计记录示例：

```markdown
- **book_type_hint**: academic（脚本输出，人工修正为 essay_collection）
- **phase1 rerun**: 从旧 stage1-understanding.md 继承 book_type_override_reason
```

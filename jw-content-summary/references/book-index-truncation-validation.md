# book-index.json Truncation Validation (v4.67)

## 实验设计

对比 `first_paragraphs` 截断 200 字符 + 删除 `last_paragraphs` 前后的 pipeline 输出。

| 版本 | first_paragraphs | last_paragraphs | book-index.json 大小 |
|------|-----------------|-----------------|---------------------|
| OLD | 全文（无截断） | 最后一段 | 254,650 bytes |
| NEW | 截断 200 字符 | 删除 | 151,142 bytes |
| **节省** | — | — | **-40.6%** |

## 巴菲特致股东的信验证结果

| 指标 | OLD | NEW | 差异 |
|------|-----|-----|------|
| candidates | 62 | 62 | 0 |
| clusters | 62 | 62 | 0 |
| avg_score | 89.52 | 89.52 | 0 |
| recommended | 61 | 61 | 0 |
| appendix | 1 | 1 | 0 |

**结论**：pipeline 输出完全一致，零质量损失。

## 为什么安全

1. book-index.json 对 stage1 的路由作用主要靠 **TOC 结构 + 章节标题 + headings**
2. first_paragraphs 只是辅助判断章节主题 — 200 字符的开头足够暴露主题词
3. last_paragraphs 对路由无帮助（尾段通常是过渡/总结，不是主题信号）
4. pipeline 阶段不直接使用 book-index.json（只用 candidates）

## 验证命令

```bash
# 生成新索引
python3 scripts/build_book_index.py /path/to/cleaned_text.txt /output/dir/

# 跑 pipeline 验证
python3 scripts/pipeline_phase2.py candidates/ output/ --dry-run
python3 scripts/pipeline_phase2.py candidates/ output/
```

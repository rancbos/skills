# 已知书籍结构模式 — 补充（讲话/文稿合集 + 路径处理）

## 讲话/文稿合集（纯演讲结构，无章节标题）

**结构特征**:
- 书籍为领导人讲话、演讲稿、文稿合集（如《习近平谈"一带一路"》）
- 内容按演讲日期/场合排列，无传统章节标题（无"第X章"）
- 目录区列出每篇讲话的标题和日期（如"共同建设'丝绸之路经济带'（2013年9月7日）"）
- `build_book_index.py` 按字符数固定切分（如每5000字一块），产生 `Chunk N` 格式
- `book-index.json` 中 `chapter_count` 是切分块数，不是讲话篇数
- 书名通常含"谈""论""选""集"等字眼

**诊断方式**:
```python
# 特征1: chapters/*.txt 全是 "Chunk N"，无真实章节标题
# 特征2: cleaned_text.txt 中存在大量日期标注（如"二○一三年九月七日"）
# 特征3: 目录区列出每篇讲话标题 + 日期 + 页码
# 特征4: 正文以演讲格式开头（"尊敬的..."、"女士们、先生们"等）
```

**处理方式**:
- 阶段 1/2/3 由主代理直接基于 cleaned_text.txt 完成（结构简单，无需 extractor）
- 按 TOC 区的讲话顺序编号为"第1篇""第2篇"等
- R-section 章节引用使用 `> ——第X篇` 格式（validator 正则 `r'> ——\s*第[零一二三四五六七八九十0-9篇章节]+'` 中的 `篇` 字匹配）
- 方法论单元按主题聚合（而非按讲话顺序），每篇讲话可被多个方法论单元引用
- 五问和方法论内容基于全书主题提炼，而非逐篇总结

**SUMMARY.md 写作要点**:
- 五问正常按标准格式写
- 方法论单元按全书核心主题组织（如"共商共建共享原则""五通框架""丝路精神"等）
- R段引用从不同讲话中选取最能代表该主题的段落，每段 ≤150字
- 审计信息注明"无candidates目录，阶段1/2/3由主代理基于cleaned_text.txt直接手工完成"

**已记录书籍**:
- 《习近平谈"一带一路"》（42篇讲话，2013-2018，128K字，26个chunks）

> **合卷本**（两卷合一，如《习近平谈治国理政》第一卷+第二卷）有额外结构特征（双目录区、双专题体系）和引用格式（`> ——第一卷·第X篇`），详见 `references/combined-volume-speech-collections.md`。

---

## 特殊字符目录名的路径处理

**问题**: 书籍目录名含中文全角引号（如 `习近平谈"一带一路"`）时，bash 路径处理会出错：
- `find -exec` 和 `$()` 替换会截断路径
- `cat "$BOOK_DIR/file"` 展开后路径含换行符或引号错配
- `python3 script.py "$BOOK_DIR/file"` 报 FileNotFoundError

**正确处理方式**:
```bash
# 方式1: cd 到 books 目录，用单引号包裹相对路径（推荐）
cd /root/books && python3 /path/to/script.py '习近平谈"一带一路"/SUMMARY.md'

# 方式2: find -exec 用 {} 作为占位符
find /root/books -maxdepth 1 -name "*一带一路*" -type d -exec ls {} \;

# 方式3: 用 Python 的 pathlib 处理路径
python3 -c "from pathlib import Path; p = list(Path('/root/books').glob('*一带一路*'))[0]; print(p / 'SUMMARY.md')"
```

**错误方式**:
```bash
# ✗ 变量展开后路径被截断
BOOK_DIR=$(find /root/books -maxdepth 1 -name "*一带一路*" -type d)
cat "$BOOK_DIR/file.txt"  # 可能因引号嵌套失败

# ✗ 双引号内嵌套双引号
python3 script.py "/root/books/习近平谈"一带一路"/file.txt"  # 语法错误
```

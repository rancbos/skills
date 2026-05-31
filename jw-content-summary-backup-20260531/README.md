# jw-content-summary — 书籍内容蒸馏总结

v4.0 | 2026-05-17 | 8 本书实战验证 | 12 轮迭代优化

## 一句话描述

把一本方法论类书籍蒸馏为可实操的 **R/I/A1/A2/E/P/B 七段方法论单元**。不是书摘——不做摘要，只提炼可执行的框架、原则、步骤和边界。

## 触发方式

```
帮我总结《穷查理宝典》
拆解《矛盾论》的方法论
提炼这本书的核心框架
summarize this book: /path/to/book.txt
extract methodology from this book
```

## 输出示例

最终产物是一份 `SUMMARY.md`，包含：

- **五问导读**：写作意图 → 核心主旨 → 内容结构 → 有道理吗 → 与自己的关系
- **方法论单元**（10-20 条），每条七段展开：
  - **R**eading — 原文引用（≤150字）
  - **I**nterpretation — 自述解读
  - **A**pplication 1 — 书中案例
  - **A**pplication 2 — 应用场景
  - **E**ssentials — 执行要点
  - **P**rocedure — 操作步骤（必经/条件触发/隐性前提）
  - **B**oundary — 适用边界/禁用条件
- **审计表**：字数、章节数、提取器产出、格式校验结果

详细示例见 `books/` 目录下各书的 `SUMMARY.md`。

## 执行流水线

```
书籍文本 (.txt/.md)
  │
  ├─ 阶段 0: clean_text.py 清洗（去噪音/标记TOC/格式标准化）
  ├─ 预处理: build_book_index.py 建索引（章节切分/结构密度/书类型判定）
  ├─ 阶段 1: 结构路由（确认类型→决定 extractor 策略） ✅ 自动
  ├─ 阶段 2: 子代理并行提取（2-5个 extractor）+ 聚类 ✅ 自动
  └─ 阶段 3: SUMMARY 渲染（五问 + Top N 七段展开）→ 自检交付
```

**核心理念**：脚本做机械活，LLM 做判断活。全量连续运行，不设确认闸口（v4.22）。

## 技术栈

| 层 | 组件 | 功能 |
|----|------|------|
| 清洗 | `clean_text.py` | 移除版权噪音、标记TOC/编者注、格式标准化 |
| 索引 | `build_book_index.py` | 章节切分、结构密度、书类型自动判定 |
| 提取 | 8 个 extractor 模板 | framework/principle/insight/case/glossary/procedure/boundary |
| 校验 | `validate_candidates.py` | 子代理输出格式合规检查（字段名/引文长度/v3_pass） |
| 聚类 | `cluster_candidates.py` | 候选软聚类 + 粒度检测（per_entry / per_file） |
| 验证 | `cross_validate.py` | 跨域补证：引用重叠/V3冲突/类型覆盖缺失 |
| 特殊 | `buffett-letters-parser-v3.py` | 章节标题重复的特殊文本解析器 |

## 已验证书籍

| # | 书名 | 字数 | 结构类型 | 单元数 | 关键特征 |
|---|------|------|---------|--------|---------|
| 1 | 金钱心理学 | 15万 | chapters | 13 | 早期格式，待升级到 RIAAEPB |
| 2 | 查理·芒格的投资思想 | 22万 | chunks | 54K | 纯字符切分，解读型书籍 |
| 3 | 巴菲特致股东的信 | 72万 | toc_filtered | 61K | 多册合集，TOC 重污染 |
| 4 | 价值：我对投资的思考 | 22万 | toc_filtered | 20 | 超长单目录，正文集中一章 |
| 5 | 聪明的投资者 | 18万 | chapters | 10 | 中等TOC污染，学术型 |
| 6 | 芒格之道 | 51万 | chunks | 27K | 纯字符切分，演讲集 |
| 7 | 穷查理宝典 | 38万 | chapters | 10 | 方法论专著，定义密度高 |
| 8 | 彼得林奇投资经典全集 | 196万 | chapters | — | 多册合集，仅完成预处理 |

## 版本历史

| 版本 | 核心变更 |
|------|---------|
| **v4.0** | 正式版：8书实战验证，12轮迭代，全链路修复完成 |
| v3.23 | 学术阈值下调(8→5)；定义检测+8模式；glossary 全覆盖 |
| v3.22 | Changelog 分离；extractor 新增 source_line 行号字段 |
| v3.21 | 补齐5个提取器模板 v3.19 字段；英文触发词 |
| v3.20 | 新增 clean_text.py 预处理前文档清洗 |
| v3.19 | 格式校验脚本 + 碎片率指标 + 聚类粒度统一 + 交叉引用 |

完整历史见 `references/changelog.md`。

## 目录结构

```
jw-content-summary/
├── SKILL.md                     # 主技能文件（377行）
├── extractors/                  # 8 个提取器模板
│   ├── framework-extractor.md
│   ├── principle-extractor.md
│   ├── insight-extractor.md
│   ├── case-extractor.md
│   ├── glossary-extractor.md
│   ├── procedure-extractor.md
│   └── boundary-extractor.md
├── scripts/                     # 可执行脚本
│   ├── clean_text.py            # 预处理前清洗（v3.20）
│   ├── build_book_index.py      # 全文索引构建
│   ├── cluster_candidates.py    # 候选软聚类
│   ├── validate_candidates.py   # 格式校验（v3.19）
│   ├── cross_validate.py        # 跨域补证（v3.16）
│   └── buffett-letters-parser-v3.py  # 特殊文本解析
├── methodology/                 # 阶段方法论
│   ├── 00-overview.md
│   ├── 01-stage1-read-extract.md
│   ├── 02-stage2-parallel-extract.md
│   ├── 03-stage3-triple-verify.md
│   └── 04-stage4-summarize.md
├── references/                  # 参考文档
│   ├── changelog.md             # 完整版本历史
│   └── known-file-structures.md # 已知文本结构诊断
└── books/                       # 产出示例（8本书的 SUMMARY）
```

## 设计原则

1. **确定性优先**：能用脚本的不用 LLM（章节切分/密度计算/格式校验 100% 确定性）
2. **标记不删除**：清洗阶段只标记可疑内容（TOC/编者注），不删除——防止误删方法论
3. **全量运行**：三阶段自动连续，不中断等待（v4.22）
4. **格式强制**：8 个 extractor 模板全部含字段名强制规则，validation 脚本自动检测别名错误
5. **渐进修复**：每本书处理完后分析瓶颈，将修复固化到脚本/SKILL.md——而非靠 agent 记住

## 使用前提

1. 非虚构方法论类书籍（商业/心理/哲学/自我提升/学术）
2. 纯虚构作品不适用——输出 Adler 四问导读，不生成方法论单元
3. 需要书的纯文本文件（.txt/.md），不支持 DRM 保护的 PDF/EPUB

## 安装

```bash
# 复制到 skills 目录
cp -r jw-content-summary ~/.hermes/skills/

# 或通过 .skill 文件安装（如有打包版本）
```

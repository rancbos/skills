# /root/books 来源参考

> 摄入时间: 2026-05-26
> 来源: /root/books（71 部投资 + 14 部政治理论 = 85 部，现代金融/投资/经济学/政治理论）
> 目标: /root/wiki-ai/entities/invest/
> 最后更新: 2026-05-30 | 当前: 71 部 invest 页面 + 14 部 malie 页面

## 概述


**分类体系（invest）:**

| 子分类 | 代表书目 | 标签 |
|--------|---------|------|
| 巴菲特/芒格/格雷厄姆 | 穷查理宝典、巴菲特之道、聪明的投资者、证券分析 | 价值投资、巴菲特、芒格、格雷厄姆、安全边际 |
| 交易/技术分析 | 以交易为生、股票大作手操盘术、股市真规则 | 交易、技术分析、止损 |
| 财报/估值 | 张新民系列、彼得林奇、估值的艺术 | 财报、估值、PE、ROE |
| 投资心理学 | 黑天鹅、反脆弱、随机漫步的傻瓜、稀缺 | 黑天鹅、反脆弱、行为金融 |
| 宏观/周期 | 周金涛、逃不开的经济周期、债务危机、非对称风险 | 宏观、周期、康波、债务 |
| 政治经济学 | 温铁军、黄奇帆、置身事内、筚路维艰 | 中国经济、三农、去杠杆 |
| 经济学基础 | 马歇尔经济学原理、经济解释、薛兆丰讲义 | 经济学、供需、边际效用 |
| 其他 | 原则、毛泽东文集、文明等 | 思维模型、原则 |

## 摄入工作流

### 批量处理（分批确认）

1. **扫描目录**: `find /root/books -type f`
2. **分类规划**: 按作者/主题分成 10-15 本一批
3. **读取样本**: 先读 3-5 本确认文件格式（txt/md，编码，内容结构）
4. **批量创建**:
   - `mkdir -p /root/wiki-ai/entities/invest`
   - `mkdir -p /root/wiki-ai/raw/articles/books`（原始备份）
   - 复制原文件到 raw/articles/books/
   - 生成 entity 页（含 YAML frontmatter）
5. **更新 index.md**: 新增 `### 价值投资（invest）— N本` 段落
6. **更新 log.md**: 记录批次操作
7. **汇报用户**: 列出本批书目，等待确认下一批

### Frontmatter 模板（invest 类）

```yaml
---
title: 《书名》
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity
tags: [标签1, 标签2, ...]
category: invest
sources: [raw/articles/books/原文件名]
confidence: high
contested: false
---
```

### Wikilinks 约定

投资类 entity 页的 `## 相关人物` 应链接到：
- [[warren-buffett]] 沃伦·巴菲特
- [[charlie-munger]] 查理·芒格
- [[benjamin-graham]] 本杰明·格雷厄姆

`## 相关书籍` 应链接到同批次或同主题的其他 entity 页。

### entity 页内容结构

```markdown
# 《书名》

**作者：** 作者名 译者：（如有）

## 核心定位
一句话说明本书在投资知识体系中的位置

## 主题标签
「标签1」「标签2」…

## 相关人物
[[warren-buffett]] [[charlie-munger]] [[benjamin-graham]]

## 相关书籍
[[同类书1]] [[同类书2]]

## 原始来源
> raw/articles/books/原文件名
```

## 与劝学网双支柱架构

```
/root/wiki-ai/
├── entities/rujia, dao, fo, fajia, baojia, bingjia, lishi, zhongyi, mengxue, nanhuaijin
│   └── 中华传统文化典籍（劝学网 quanxue.cn）
└── entities/invest/
    └── 现代金融/投资/经济学书籍（/root/books）
```

**SCHEMA.md 扩展标签（需添加到标签分类）：**
- 价值投资、巴菲特、芒格、格雷厄姆、安全边际
- 交易、技术分析、止损
- 财报、估值、PE、ROE
- 投资心理学、行为金融
- 宏观、周期、康波、债务
- 中国经济、政治经济学

## 注意事项

- /root/books 文件编码多为 UTF-8，读取时用 `errors='replace'` 处理少量乱码
- 同一书名可能出现 .txt 和 .md 两个版本，取 .md 版本（或合并）
- 部分书籍超大（如巴菲特致股东的信及伯克希尔股东大会实录 476万字），读取时只用前 5000 字生成摘要
- 巴菲特相关书籍互相之间高度相关，建档时优先建立 `[[buffett-xxx]]` 互链

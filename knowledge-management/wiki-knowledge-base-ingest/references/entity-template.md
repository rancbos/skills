---
category: knowledge-management
description: Entity 页完整模板，含 YAML frontmatter 和正文结构
---

# Entity 页完整模板

## 标准格式

```markdown
---
category: invest          # 分类：rujia/dao/fo/fajia/baojia/lishi/zhongyi/mengxue/bingjia/invest
entity_id: buffett-zhi-dao
title: 巴菲特之道
author: 罗伯特·哈格斯特朗（美国）
source: /root/books/巴菲特之道.txt
created: 2026-05-26
tags: [巴菲特, 价值投资, 企业分析, 护城河]
---

# 巴菲特之道

**作者**: 罗伯特·哈格斯特朗（美国）

**类别**: 价值投资

**核心标签**: #巴菲特 #价值投资 #企业分析 #护城河 #长期投资

---

## 一句话简介

巴菲特亲笔作序，讲述其购买企业12条准则、9个普通股投资案例，系统总结价值投资方法论。

---

## 核心观点

- **购买企业12条准则**：从财务指标（ROE、债务结构）到管理质量（理性、坦诚）的全面评估
- **护城河理论**：无形资产、成本优势、转换成本、网络效应构成竞争壁垒
- **正确对待价格与价值**：内在价值用现金流折现法估算，价格是你支付的，价值是你得到的
- **集中投资**：将资金集中在少数优秀企业，而非分散到许多平庸标的
- **长期持有**：优秀企业应持有十年以上，不轻易买卖

---

## 与其他典籍的关联

- [[buffett-zhi-gudong-de-xin]] — 巴菲特致股东的信，方法论实践
- [[congming-de-touzizhe]] — 格雷厄姆奠基，价值投资起点
- [[qiong-charlie-munger-baodian]] — 芒格误判心理学，决策框架补充
- [[bamang-yanyi]] — 唐朝章回体故事，方法论演化

---

## 原始来源

📁 `/root/books/巴菲特之道.txt`

---

*本条目最后更新：2026-05-26*
```

## 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `category` | 是 | 分类目录名（rujia/dao/fo/fajia/baojia/bingjia/lishi/zhongyi/mengxue/invest） |
| `entity_id` | 是 | 文件名去掉 .md 后的 ID，全小写，英文/拼音 |
| `title` | 是 | 书名（中文） |
| `author` | 否 | 作者名+国籍 |
| `source` | 否 | 原始文件路径 |
| `created` | 是 | 创建日期 YYYY-MM-DD |
| `tags` | 否 | 主题标签数组 |

## 最小格式（可省略 frontmatter）

```markdown
# 书名

**作者**: 作者名

**类别**: 分类

**核心标签**: #标签1 #标签2

---

## 一句话简介

简洁描述书的核心价值。

---

## 核心观点

- 要点1
- 要点2

---

## 与其他典籍的关联

- [[other_entity_id]] — 关联说明

---

## 原始来源

📁 `/{path}/{filename}`

---

*本条目由系统自动创建 · YYYY-MM-DD*
```
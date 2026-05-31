# 阶段 1 — 索引驱动的结构路由

## 目标

不直接读全书。先运行 deterministic 预处理脚本建立全文索引，然后让 LLM 只读取 `book-index.json` 和必要片段，完成书籍类型判断、章节角色判断、动态 extractor 路由。

## 预处理（无 LLM token）

在阶段 1 开始前运行：

```bash
python ~/.hermes/skills/jw-content-summary/scripts/build_book_index.py \
  /path/to/book.txt \
  books/<slug>/preprocess
```

产出：

```
books/<slug>/preprocess/
├── book-index.json
├── chapters/
│   ├── ch001.txt
│   ├── ch002.txt
│   └── ...
└── snippets/
    ├── definitions.json
    ├── cases.json
    ├── warnings.json
    └── quotes.json
```

## 阶段 1 读取内容

LLM 只读取：

1. `book-index.json`
2. 必要时读取少量 `snippets/*.json`
3. 不直接读取完整章节正文

## 执行步骤

### 步骤 1 — 类型判定

基于目录、章节标题、首尾段、关键词判断书籍类型：

| 类型 | 判定信号 | 默认 extractor |
|------|---------|---------------|
| 方法论专著 | 目录呈框架/步骤结构，章节间递进 | framework, principle, case, boundary |
| 学术/理论著作 | 术语密集，论证链清晰 | framework, glossary |
| 传记/案例集 | 按时间/事件排列，故事密集 | case, principle, boundary |
| 散文/随笔集 | 章节独立，洞见碎片化 | principle, insight |
| 实操手册 | 步骤/清单/工具明显 | procedure, boundary, case |
| 虚构作品 | 叙事结构，无方法论骨架 | 不适用，终止 |
| 其他 | 无文本论证结构 | 不适用，终止 |

### 步骤 2 — 章节角色标注

给每章打一个或多个角色标签：

| 标签 | 含义 |
|------|------|
| `setup` | 问题背景 / 写作动机 |
| `thesis` | 核心主张 |
| `framework` | 框架 / 模型 / 方法 |
| `principle` | 原则 / 判断 / 定律 |
| `case` | 案例 / 故事 / 实践 |
| `warning` | 误区 / 失败 / 反例 / 边界 |
| `glossary` | 术语定义密集 |
| `application` | 应用展开 |

### 步骤 3 — 动态 extractor 路由

不要固定 5 个 extractor。根据书籍类型和章节角色启动 2-5 个。

输出路由表：

```yaml
extractors:
  framework:
    enabled: true
    inputs: [preprocess/chapters/ch002.txt, preprocess/chapters/ch003.txt]
  principle:
    enabled: true
    inputs: [preprocess/chapters/ch001.txt, preprocess/snippets/quotes.json]
  case:
    enabled: false
    reason: "案例片段不足"
  boundary:
    enabled: true
    inputs: [preprocess/snippets/warnings.json]
  glossary:
    enabled: true
    inputs: [preprocess/snippets/definitions.json]
```

### 步骤 4 — 核心路由摘要

阶段 1 只写路由需要的信息，不追求完整理解。

## 产出

写入 `books/<slug>/stage1-understanding.md`：

```markdown
# {{BOOK_TITLE}} — 结构路由（阶段 1）

## 基本信息
- 书名 / 作者 / 出版年
- 类型: {{...}}
- 主旨一句话: {{...}}
- 总字数: {{来自 book-index.json}}
- 分块模式: {{≥3 万字是，否则否}}

## 章节角色表
| chapter | title | roles | reason |
|---------|-------|-------|--------|
| ch001 | ... | setup, thesis | ... |

## 核心命题（路由级）
{{3-5 个，一句话级别}}

## 动态 extractor 路由表
{{yaml 路由表}}

## 风险提示
- 可能误判的章节: {{...}}
- 需要补读的片段: {{...}}
```

## 自动进入阶段 2

阶段 1 完成后，自动进入阶段 2，不等待用户确认。书类型判断、extractor 路由直接应用到阶段 2。

## 常见失败模式

1. **把阶段 1 写成总结** — 阶段 1 只负责路由，不负责完整理解
2. **动态路由太激进** — 不确定就保留 extractor，不要为了省 token 漏掉关键维度
3. **忽略 snippets** — glossary/case/warning 应优先用脚本片段，不要直接读全章
4. **虚构作品误入流程** — 无方法论骨架时应终止

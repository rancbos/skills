---
name: jw-llm-wiki
description: |
  个人知识库构建系统。支持消化网页、文档、书籍等素材，自动整理为互相链接的 wiki。
  触发词：知识库、wiki、初始化知识库、消化素材、批量整理、查询知识库、知识图谱、
  深度分析、对比分析、健康检查、结晶化。
metadata:
  hermes:
    tags: [knowledge-base, wiki, research, note-taking]
---

# jw-llm-wiki — 个人知识库构建系统

> 把碎片化的信息变成持续积累、互相链接的知识库。你只需要提供素材，AI 做所有的整理工作。

## Iron Law（核心约束）

1. **知识积累优先**：宁可少收录，不可收录错误信息。不确定时标注 `UNVERIFIED`。
2. **幂等性**：对同一素材重复 ingest 应产生相同结果（依赖缓存机制）。
3. **渐进式丰富**：首次 ingest 只创建必要页面，后续 ingest 逐步完善。

## Anti-Patterns（禁止事项）

- ❌ 不要在 ingest 时一次性读取整个长文档（>5000字），应分块处理
- ❌ 不要跳过缓存检查直接处理
- ❌ 不要手动更新缓存，必须使用 `create-source-page.sh`
- ❌ 不要在 query 时自动创建实体页，query 是即时回答
- ❌ 不要在 ingest 时讨论个股投资（这是知识库，不是投资建议）

---

## 快速开始

1. **初始化**：说"帮我初始化一个知识库"
2. **添加素材**：给一个链接或文件，说"帮我消化这篇"

## Script Directory

Scripts located in `scripts/` subdirectory.

**Path Resolution**:
1. `SKILL_DIR` = this SKILL.md's directory
2. Script path = `${SKILL_DIR}/scripts/<script-name>`

## Templates

Templates located in `templates/` subdirectory:
- `schema-template.md` — 知识库配置模板
- `index-template.md` — 索引模板
- `log-template.md` — 日志模板
- `source-template.md` — 素材摘要模板
- `entity-template.md` — 实体页模板
- `topic-template.md` — 主题页模板
- `query-template.md` — 查询记录模板
- `synthesis-template.md` — 综合分析模板

## References

Reference files located in `references/` subdirectory:
- `privacy-checklist.md` — 隐私自查清单（ingest 时加载）
- `step1-json-schema.md` — Step 1 JSON 格式（ingest 时加载）
- `digest-templates.md` — Digest 模板 A/B/C（digest 时加载）
- `graph-workflow.md` — Graph 工作流详情（graph 时加载）
- `delete-workflow.md` — Delete 工作流详情（delete 时加载）
- `crystallize-workflow.md` — Crystallize 工作流详情（crystallize 时加载）

---

## 依赖检查

核心主线（本地文件、纯文本、已有知识库操作）默认不需要这些提取依赖。

只有当用户给的是 URL 类来源，并且明确要自动提取网页 / X / 微信公众号 / YouTube / 知乎内容时，才检查以下可选依赖。

如果缺失，提示用户运行：

```bash
bash ${SKILL_DIR}/install.sh --platform <当前平台> --with-optional-adapters
```

可选依赖 skill / 工具：
- `baoyu-url-to-markdown` — 普通网页、X/Twitter、部分知乎提取
- `wechat-article-to-markdown` — 微信公众号提取
- `youtube-transcript` — YouTube 字幕提取

即使这些依赖缺失，skill 仍可工作（用户可以直接提供本地文件、粘贴文本，或改走手动入口）。

---

## 工作流路由

| 用户意图关键词 | 工作流 |
|---|---|
| "初始化知识库"、"新建 wiki" | → **init** |
| URL / 文件路径 / "消化" / 书籍路径 | → **ingest** |
| "批量消化" / 文件夹路径 / "把XX书存入知识库" | → **batch-ingest** |
| "关于 XX"、"查询" | → **query** |
| "深度分析"、"综述" | → **digest** |
| "对比 X 和 Y" | → **digest**（对比格式） |
| "健康检查"、"lint" | → **lint** |
| "知识库状态" | → **status** |
| "知识图谱"、"graph" | → **graph** |
| "删除素材" | → **delete** |
| "结晶化"、"记进知识库" | → **crystallize** |

**重要**：如果用户直接给了 URL 或文件，但没有明确说要做什么，默认走 **ingest**。如果知识库还不存在，先自动走 **init** 再走 **ingest**。

---

## 通用前置检查

除 `init` 外，其他工作流默认先执行这段检查：

1. 先检查**当前工作目录**是否包含 `.wiki-schema.md`
   - 如果包含 → 用当前目录作为知识库根路径
   - 如果不包含 → 回退到读取 `~/.llm-wiki-path`
2. 如果两者都没有：
   - `ingest` / `batch-ingest` → 先运行 `init`
   - `query` / `lint` / `status` / `digest` / `graph` / `delete` → 提示用户先初始化知识库
3. 读取知识库根目录下的 `.wiki-schema.md`
4. 从 `.wiki-schema.md` 的"语言"字段判断 `WIKI_LANG`
   - `语言：中文` → `WIKI_LANG=zh`
   - `语言：English` → `WIKI_LANG=en`
   - 字段缺失 → 默认 `WIKI_LANG=zh`

---

## 输出语言规则

所有面向用户的输出和新写入的 wiki 内容，都按 `WIKI_LANG` 生成。

---

## 工作流 1：init（初始化知识库）

### 步骤

1. **询问知识库主题**（先向用户提问）
2. **询问知识库语言**（默认中文）
3. **询问保存位置**（默认 `~/Documents/我的知识库/`）
4. **运行初始化脚本**：
   ```bash
   bash ${SKILL_DIR}/scripts/init-wiki.sh "<路径>" "<主题>"
   ```
5. **补充初始化结果说明**：提醒用户填写 `purpose.md`
6. **写入语言配置并本地化种子文件**
7. **记录路径**到 `~/.llm-wiki-path`
8. **输出引导**

---

## 工作流 2：ingest（消化素材）

⚠️ 这是最核心的工作流。

### 前置检查

执行**通用前置检查**。

### 隐私自查提示（首次进入 ingest 必须执行）

加载 `references/privacy-checklist.md` 获取完整的自查清单和流程规则。

### 素材提取路由

**外挂前置判断**：

```bash
# URL 类素材
bash ${SKILL_DIR}/scripts/source-registry.sh match-url "<url>"
bash ${SKILL_DIR}/scripts/adapter-state.sh check <source_id>

# 本地文件
bash ${SKILL_DIR}/scripts/source-registry.sh match-file "<path>"
```

- 如果 `state=available` → 继续自动提取
- 如果 `state=not_installed` / `env_unavailable` / `unsupported` → 按 `fallback_hint` 告诉用户

### 内容分级处理

- 素材内容 > 1000 字 → **完整处理**
- 素材内容 <= 1000 字 → **简化处理**

### 完整处理流程（长素材 > 1000 字）

1. **提取素材内容**：按上面的路由获取素材文本

2. ⚠️ **保存原始素材**到 `raw/` 对应目录
   - 文件名格式：`{日期}-{短标题}.md`

3. **读取上下文**：优先顺序：`purpose.md` > `.wiki-schema.md` > `index.md`

4. ⚠️ **缓存检查**：
   ```bash
   bash ${SKILL_DIR}/scripts/cache.sh check "<raw 文件路径>"
   ```
   - `HIT` → 跳过处理，直接复用已有结果
   - `MISS` → 继续执行

5. **Step 1：结构化分析**
   - 加载 `references/step1-json-schema.md` 获取 JSON 格式和验证步骤
   - 输出：JSON 格式的分析结果，不持久化

6. **Step 2：页面生成**
   - 输入：原始内容 + `purpose.md` + Step 1 的分析结果 + 现有相关 wiki 页面
   - 输出：所有需要创建或更新的 wiki 页面内容

7. **容错回退**：如果 Step 1 不是有效 JSON，自动回退到单步流程

8. ⚠️ **生成素材摘要页**（`wiki/sources/{日期}-{短标题}.md`）
   - **必须使用 `create-source-page.sh`**（自动更新缓存）

9. **更新或创建实体页**（`wiki/entities/`）

10. **更新或创建主题页**（`wiki/topics/`）

11. ⚠️ **更新 index.md**

12. ⚠️ **更新 log.md**

13. **向用户展示结果**

### 简化处理流程（短素材 <= 1000 字）

适用于短推文、小红书笔记等。跳过主题页创建/更新、overview 更新。

---

## 工作流 3：batch-ingest（批量消化）

1. **确认知识库路径**
2. **列出所有可处理文件**（.md, .txt, .pdf, .html）
3. ⛔ **展示文件列表**，确认处理范围
4. **逐个处理**：每个文件执行 ingest 工作流
5. **每 5 个文件后暂停**，展示进度
6. **全部完成后**：运行一次 index.md 全量更新

---

## 工作流 4：query（查询知识库）

1. **确认知识库路径**
2. **读取 index.md** 了解知识库全貌
3. **搜索相关页面**（支持别名展开）
4. **综合回答**（标注来源）
5. **判断是否值得持久化**（≥3 个来源时提示保存）
6. **重复检测**（避免重复保存）
7. **保存 query 页面**（`wiki/queries/{date}-{short-hash}.md`）
8. **自引用防护**（query 页面视为二级来源）
9. **更新索引和日志**

---

## 工作流 5：lint（健康检查）

1. **确定检查范围**（最近更新 10 页 + 随机抽查 10 页）
2. ⚠️ **Step 0：调用脚本做机械检查**
   ```bash
   bash ${SKILL_DIR}/scripts/lint-runner.sh <wiki_root>
   ```
3. **逐项检查**（矛盾信息、交叉引用缺失、置信度报告）
4. **输出报告**
5. **询问用户**：要自动修复哪些问题？

---

## 工作流 6：status（查看状态）

1. 运行 `bash ${SKILL_DIR}/scripts/source-registry.sh list`
2. 获取知识库路径
3. 统计各类页面数量
4. 读取 `log.md` 最后 5 条记录
5. 运行 `bash ${SKILL_DIR}/scripts/adapter-state.sh summary-human`
6. 运行 `node ${SKILL_DIR}/scripts/source-signal-coverage.js <wiki_root>`
7. **输出报告**

---

## 工作流 7：digest（深度综合报告）

**区别于 query**：query 是快速问答，不生成新页面；digest 是跨素材深度综合，生成持久化报告。

1. **搜索相关页面**（支持别名展开）
2. **深度阅读所有相关页面 + 选择输出格式**
3. **生成结构化深度报告**（加载 `references/digest-templates.md` 获取模板）
4. **更新 index.md 和 log.md**
5. **向用户展示结果**

---

## 工作流 8：graph（知识图谱）

加载 `references/graph-workflow.md` 获取完整工作流。

---

## 工作流 9：delete（删除素材）

加载 `references/delete-workflow.md` 获取完整工作流。

⚠️ 必须在删除前执行安全确认。

---

## 工作流 10：crystallize（结晶化）

加载 `references/crystallize-workflow.md` 获取完整工作流。

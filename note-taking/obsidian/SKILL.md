---
name: obsidian
description: Read, search, create, and edit notes in the Obsidian vault.
platforms: [linux, macos, windows]
---

# Obsidian Vault

Use this skill for filesystem-first Obsidian vault work: reading notes, listing notes, searching note files, creating notes, appending content, and adding wikilinks.

## Vault path

Use a known or resolved vault path before calling file tools.

The documented vault-path convention is the `OBSIDIAN_VAULT_PATH` environment variable, for example from `~/.hermes/.env`. If it is unset, use `~/Documents/Obsidian Vault`.

File tools do not expand shell variables. Do not pass paths containing `$OBSIDIAN_VAULT_PATH` to `read_file`, `write_file`, `patch`, or `search_files`; resolve the vault path first and pass a concrete absolute path. Vault paths may contain spaces, which is another reason to prefer file tools over shell commands.

If the vault path is unknown, `terminal` is acceptable for resolving `OBSIDIAN_VAULT_PATH` or checking whether the fallback path exists. Once the path is known, switch back to file tools.

## Read a note

Use `read_file` with the resolved absolute path to the note. Prefer this over `cat` because it provides line numbers and pagination.

## List notes

Use `search_files` with `target: "files"` and the resolved vault path. Prefer this over `find` or `ls`.

- To list all markdown notes, use `pattern: "*.md"` under the vault path.
- To list a subfolder, search under that subfolder's absolute path.

## Search

Use `search_files` for both filename and content searches. Prefer this over `grep`, `find`, or `ls`.

- For filenames, use `search_files` with `target: "files"` and a filename `pattern`.
- For note contents, use `search_files` with `target: "content"`, the content regex as `pattern`, and `file_glob: "*.md"` when you want to restrict matches to markdown notes.

## Create a note

Use `write_file` with the resolved absolute path and the full markdown content. Prefer this over shell heredocs or `echo` because it avoids shell quoting issues and returns structured results.

## Append to a note

Prefer a native file-tool workflow when it is not awkward:

- Read the target note with `read_file`.
- Use `patch` for an anchored append when there is stable context, such as adding a section after an existing heading or appending before a known trailing block.
- Use `write_file` when rewriting the whole note is clearer than constructing a fragile patch.

For an anchored append with `patch`, replace the anchor with the anchor plus the new content.

For a simple append with no stable context, `terminal` is acceptable if it is the clearest safe option.

## Targeted edits

Use `patch` for focused note changes when the current content gives you stable context. Prefer this over shell text rewriting.

## Wikilinks

Obsidian links notes with `[[Note Name]]` syntax. When creating notes, use these to link related content.

## Batch note creation via delegation

When creating many notes across multiple categories (e.g., a full classical texts corpus), delegate subagents to parallelize the work. Each subagent should write directly to the resolved vault absolute path — file tools do not auto-create parent directories when called from a subagent's context.

**Common issue**: Subagents may write files to `/root/` instead of the intended `/root/obsidian/Category/` subdirectory if the parent directory doesn't exist. Fix: create all needed subdirectories in the orchestrating session before dispatching workers.

**Pattern**:
```python
# Before delegation - ensure structure exists
terminal(command="mkdir -p /root/obsidian/{儒家,道家,佛家,法家,历史,中医,蒙学}")
```

## 已验证的采集模式

当采集 quanxue.cn 典籍时：

1. **预建目录**：先 `mkdir -p /root/obsidian/{儒家,道家,...}` 再 delegation
2. **传完整路径**：subagent 必须收到 `/root/obsidian/儒家/诗经.md` 而非 `诗经.md`
3. **404处理**：左传/公羊传/谷梁传索引页返回404 → 改用 `/ct_rujia/chunqiuindex.html` 合集或外部重建
4. **工具选择**：`ddg_fetch_content` 优先（大页面稳定），`tavily_crawl` 易超时
5. **事后验证**：完成后 `find /root/obsidian -name "*.md" | sort` 检查文件位置

## 采集结果记录（已采集典籍）

> **wiki-ai 模式（2026-05-26 完成）**：56本典籍统一在 `/root/obsidian/wiki-ai/entities/` 下，按学派分类子目录存储，每本含 YAML frontmatter + 内容摘要 + wikilinks 跨典籍互链。
>
> **原始采集模式**：文本直接采集到各学派子目录（/root/obsidian/{儒家,道家,...}/）。

### wiki-ai 模式典籍（56本）

| 学派 | 数量 | 已生成 entity 页 |
|------|------|------------------|
| 儒家 | 35 | ✅ entities/rujia/ |
| 道家 | 5 | ✅ entities/dao/ |
| 佛家 | 2 | ✅ entities/fo/ |
| 法家 | 2 | ✅ entities/fajia/ |
| 百家 | 3 | ✅ entities/baojia/ |
| 历史 | 2 | ✅ entities/lishi/ |
| 中医 | 2 | ✅ entities/zhongyi/ |
| 蒙学 | 4 | ✅ entities/mengxue/ |
| 南怀瑾 | 1 | ✅ entities/nanhuaijin/ |

**合计：56本**，已生成 entity 页，原始采集文件保留在各分类子目录。

### 原始采集目录（/root/obsidian/）

| 分类 | 已采集 | 待采集 |
|------|--------|--------|
| 儒家 | 论语、大学、中庸、孟子、周易、诗经、尚书、礼记、荀子、春秋、左传、公羊传、谷梁传、周礼、仪礼、大戴礼记、孔子家语、传习录（19本） | 国语、春秋繁露、法言、韩诗外传、烈女传、韩愈文集、正蒙、近思录、象山语要、大学问、日知录、明夷待访录、困知记、周子全书 |
| 道家 | 老子、庄子、列子、阴符经、鬼谷子（5本） | 关尹子、黄帝四经、鬻子、文子、清静经、抱朴子、周易参同契、悟真篇、黄庭经 |
| 历史 | 史记、三国志（2本） | 资治通鉴（外部重建）、汉书、后汉书、晋书、宋史等二十七史 |
| 法家 | 韩非子、管子（2本） | 商君书、申子、慎子、邓析子 |
| 中医 | 黄帝内经、伤寒论（2本） | 本草纲目（外部重建）、金匮要略、神农本草经 |
| 蒙学 | 三字经、百家姓、千字文、弟子规（4本） | 孝经、增广贤文、朱子家训、幼学琼林、古文观止 |
| 佛学 | 金刚经、阿弥陀经（2本） | 楞严经、心经、法华经、六祖坛经等（劝学网佛学典籍极庞大） |
| 南怀瑾 | 全集目录（1本） | — |

*最后更新：2026-05-26（wiki-ai entity 模式更新）*

---

See `references/quanxue-catalog-pattern.md` for a ready-made template and source URL map when building a classical Chinese texts corpus from quanxue.cn.

## Handling 404 / missing index pages

When a source page returns 404 but the site has related content (e.g., individual chapter pages exist), fall back to reconstructing the catalog from authoritative external sources (Wikipedia, Baidu Baike, original text sites). Document the reconstruction clearly with source attribution.

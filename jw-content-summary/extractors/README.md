# extractors/ — 历史参考

这些文件是 v4.22 之前旧架构（delegate_task 子代理）的 extractor prompt 模板。

当前架构（v4.22+）使用 `execute_code` 直接从 chapters 文本提取，不再使用独立的 extractor 子代理。

这些文件保留作为每种候选类型的 schema 参考：
- `framework-extractor.md` — 框架类候选的提取模式
- `principle-extractor.md` — 原则类候选的提取模式
- `case-extractor.md` — 案例类候选的提取模式
- `boundary-extractor.md` — 边界类候选的提取模式
- `insight-extractor.md` — 洞见类候选的提取模式
- `glossary-extractor.md` — 术语类候选的提取模式
- `procedure-extractor.md` — 步骤类候选的提取模式

如需理解候选文件的格式规范，参考 `references/extractor-schema-mapping.md`。

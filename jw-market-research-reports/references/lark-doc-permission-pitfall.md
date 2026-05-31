# 飞书文档权限与 URL 域名陷阱

## 问题描述

`lark-cli docs +create` 创建文档后，用户通过返回的 URL 无法打开文档。

## 根因

1. **URL 域名错误**：API 返回的 URL 域名是 `my.feishu.cn`，不适用于所有租户。`drive +inspect` 返回的 `www.feishu.cn` 域名更通用。
2. **权限不足**：默认 `link_share_entity` 是 `tenant_readable`（仅组织内可读），需改为 `anyone_readable`。

## 修复流程（每次创建文档后必须执行）

```bash
# 1. 创建文档
lark-cli docs +create --api-version v2 --content '...'

# 2. 从返回 JSON 提取 document_id

# 3. 修复权限
lark-cli drive permission.public patch \
  --params '{"token":"<document_id>","type":"docx"}' \
  --data '{"link_share_entity":"anyone_readable"}' --yes

# 4. 获取正确 URL
lark-cli drive +inspect --url "<document_id>" --type docx | grep '"url"'

# 5. 将 www.feishu.cn 域名的 URL 发给用户
```

## 验证权限状态

```bash
lark-cli drive permission.public get \
  --params '{"token":"<document_id>","type":"docx"}'
```

应返回 `"link_share_entity": "anyone_readable"`。

## 注意事项

- `drive permission.public patch` 的参数用 `--params`（路径+查询参数）和 `--data`（请求体），不是 `--body`
- `drive +inspect` 的参数用 `--url` 和 `--type`，不是 positional argument
- **链接必须通过纯文本发送，不使用飞书消息卡片**（消息卡片会对URL做转义/编码，导致链接无法打开）
- 直接在消息文本中贴 `https://www.feishu.cn/docx/xxx` 格式的链接即可

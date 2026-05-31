---
name: financial-data-mcp
description: "Connect to real-time financial data MCP servers (Jin10,行情,期货,大宗商品). Includes MCP client config, Bearer token gotcha with YAML, and Python direct-call fallback for verification."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [MCP, financial-data, commodities, futures, quotes, XAUUSD, USOIL, Jin10]
    related_skills: [native-mcp, jw-stock-value-analyzer]
---

# Financial Data MCP

Connect to real-time financial data MCP servers (Jin10,行情,期货,大宗商品) via HTTP/SSE transport with Bearer token auth.

## Quick Config

```yaml
mcp_servers:
  jin10:
    url: "https://mcp.jin10.com/mcp"
    headers:
      Authorization: "Bearer sk-1Pk...WYxU"
    timeout: 30
    connect_timeout: 15
```

**Recommended protocol version:** `2025-11-25`
**Preferred response field:** `result.structuredContent`
**Pagination:** `cursor` / `data.next_cursor`

## Jin10 MCP Tools

| Tool | Description |
|------|-------------|
| `get_quote` | 实时行情（代码：XAUUSD, USOIL, etc.） |
| `get_kline` | 分钟级K线数据 |
| `list_flash` | 快讯分页列表 |
| `search_flash` | 关键词搜索快讯 |
| `list_news` / `search_news` | 文章列表/搜索 |
| `get_news` | 文章详情 |
| `list_calendar` | 财经日历（当前自然周） |

## Bearer Token YAML Gotcha ⚠️

**CRITICAL: YAML interprets `...` as an ellipsis node and `---` as document boundary.**

If your Bearer token contains `...` (e.g. `sk-1Pk...WYxU`), and you write it directly in config.yaml as:

```yaml
Authorization: "Bearer sk-1Pk...WYxU"
```

YAML will silently truncate the token. The `...` gets consumed as syntax, not data.

**Solution:** Write the full token value as a literal block scalar, or ensure no ambiguous sequences. When in doubt, read the file back as raw bytes and verify the token length.

**ALSO CHECK for trailing quotes:** A trailing `"` at the end of the Authorization line (e.g., `Authorization: "Bearer sk-1Pk...WYxU"`) causes `ValueError: Invalid header value` in the HTTP client — even though the token bytes are correct. If `hermes mcp test` connects but tool calls fail with 401, hex-inspect the config line.

## SSE Response Parsing

Jin10 MCP returns responses as SSE streams (`data: {...}` prefix). Parse like this:

```python
raw = r.text.split('data: ')[1]          # strip SSE prefix
data = json.loads(raw)                   # parse JSON body
inner = json.loads(data['result']['content'][0]['text'])  # nested JSON string
items = inner['data']['items']           # actual data list
```

## Encoding Fix for Chinese Text

`list_flash` / `search_flash` content may appear as garbled Chinese. Fix with:

```python
def fix(s):
    return s.encode('iso-8859-1').decode('utf-8')

content = fix(item.get('content', ''))
```

## Python Direct-Call Verification Script

When `hermes mcp test` shows "8 tools discovered" but actual tool calls return 401, the token may be corrupted in config.yaml. Use this to verify:

```python
import requests

with open('/root/.hermes/config.yaml', 'rb') as f:
    content = f.read()
idx = content.find(b'sk-1Pk')
token = content[idx:idx+46].decode()  # read exact bytes, not string

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json',
    'mcp-protocol-version': '2025-11-25'
}

# Initialize
r = requests.post('https://mcp.jin10.com/mcp', headers=headers, json={
    'jsonrpc':'2.0','id':1,'method':'initialize',
    'params':{'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'hermes','version':'1.0'}}
}, timeout=15)
session_id = r.headers.get('mcp-session-id')
print('Session:', session_id)

# Send notifications/initialized
requests.post('https://mcp.jin10.com/mcp', headers={**headers, 'mcp-session-id': session_id}, json={
    'jsonrpc':'2.0','method':'notifications/initialized','params':{}
}, timeout=10)

# Call tool
r = requests.post('https://mcp.jin10.com/mcp', headers={**headers, 'mcp-session-id': session_id}, json={
    'jsonrpc':'2.0','id':2,'method':'tools/call',
    'params':{'name':'get_quote','arguments':{'code':'XAUUSD'}}
}, timeout=15)

import json
data = json.loads(r.text.split('data: ')[1])
print(data['result']['structuredContent'])
```

## Common Codes

- `XAUUSD` — 现货黄金
- `USOil` / `USOIL` — WTI原油
- `GBOil` — 布伦特原油

## MCP Initialization Sequence

1. `POST /mcp` with `initialize` → get `mcp-session-id` header
2. `POST /mcp` with `notifications/initialized` (no id)
3. `POST /mcp` with `tools/list` or `tools/call` using session cookie

Tool discovery (`hermes mcp test`) does NOT require full initialization — it works with just the transport handshake. But actual tool calls require a valid initialized session.

## Verification

See `references/jin10-verify.md` for a standalone verification script that reads the token as raw bytes (bypassing YAML interpretation) and tests the full MCP call sequence.
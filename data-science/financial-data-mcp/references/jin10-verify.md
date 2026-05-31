# Jin10 MCP Verification Script

## Problem
`hermes mcp test jin10` shows "Connected (8 tools discovered)" but actual HTTP calls return 401 "invalid token". This happens when the Bearer token is corrupted in config.yaml (e.g., YAML truncated the `...` sequence in `sk-1Pk...WYxU`).

## Root Cause
YAML interprets `...` as an ellipsis node and consumes it as syntax. The token gets truncated from 66 chars to 13 chars (`sk-1Pk...WYxU`).

## Verification Script

```python
#!/usr/bin/env python3
"""Verify Jin10 MCP connection with exact token from config."""
import requests, json, sys

with open('/root/.hermes/config.yaml', 'rb') as f:
    content = f.read()

# Read token as raw bytes (not string) to avoid YAML interpretation
idx = content.find(b'sk-1Pk')
if idx < 0:
    print("ERROR: sk-1Pk token not found in config.yaml")
    sys.exit(1)

token = content[idx:idx+46].decode()
print(f"Token length: {len(token)}")
print(f"Token start: {token[:10]}...{token[-6:]}")

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json',
    'mcp-protocol-version': '2025-11-25'
}
url = 'https://mcp.jin10.com/mcp'

# Initialize
r = requests.post(url, headers=headers, json={
    'jsonrpc':'2.0','id':1,'method':'initialize',
    'params':{'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'verify','version':'1.0'}}
}, timeout=15)

if r.status_code != 200:
    print(f"FAILED: {r.status_code} {r.text[:100]}")
    sys.exit(1)

session_id = r.headers.get('mcp-session-id')
print(f"Session: {session_id}")

# notifications/initialized
requests.post(url, headers={**headers, 'mcp-session-id': session_id}, json={
    'jsonrpc':'2.0','method':'notifications/initialized','params':{}
}, timeout=10)

# Test get_quote
r = requests.post(url, headers={**headers, 'mcp-session-id': session_id}, json={
    'jsonrpc':'2.0','id':2,'method':'tools/call',
    'params':{'name':'get_quote','arguments':{'code':'XAUUSD'}}
}, timeout=15)

data = json.loads(r.text.split('data: ')[1])
quote = data['result']['structuredContent']['data']
def fix(s):
    return s.encode('iso-8859-1').decode('utf-8')

# Parse SSE
raw = r.text.split('data: ')[1]
data = json.loads(raw)
inner = json.loads(data['result']['content'][0]['text'])
items = inner['data']['items']

print(f"Flash items: {len(items)}")
for i, item in enumerate(items[:5], 1):
    content = fix(item.get('content', ''))
    time = item.get('time', '')[-8:-3]
    print(f"{i}. {content} [{time}]")

print("\nOK")
```

## Token Pattern Reference

- **search_news returns SSE parsing error**: Use `list_flash` + `search_flash` for real-time news instead — they return properly formatted JSON without SSE wrapping issues.
- **list_flash content is garbled Chinese**: Apply encoding fix before displaying:
  ```python
  def fix(s):
      return s.encode('iso-8859-1').decode('utf-8')
  content = fix(item.get('content', ''))
  ```
- **Trailing quote in config.yaml**: A trailing `"` on the Authorization line causes `ValueError: Invalid header value`. Hex-inspect byte 0x22 at end of token area.

## How to Use

```bash
python3 ~/.hermes/skills/data-science/financial-data-mcp/references/jin10-verify.py
```

Expected output:
```
Token length: 46
Token start: sk-1PkxCss...n2-WYxU
Session: FYEQ5L5RDYOPJKBFMFTBXLMSYQ
XAUUSD: $4567.71 (+1.34%)
OK
```

## Known Good Codes

| Code | Name |
|------|------|
| XAUUSD | 现货黄金 |
| USOIL / USOil | WTI原油 |
| GB Oil | 布伦特原油 |

## Token Pattern Reference

If `Token length:` shows 13 instead of 46, the token is corrupted by YAML `...` interpretation. Must re-enter the full 66-char token manually.
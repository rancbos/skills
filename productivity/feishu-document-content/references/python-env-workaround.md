# Feishu API Debug Log — Session Notes

## Issue: .env vars not auto-loaded into Python os.environ

**Symptom:** Running `os.environ.get('FEISHU_APP_ID')` in `execute_code` or a Python subprocess returns empty string `''`, even though the vars exist in `~/.hermes/.env`.

**Root cause:** Hermes profile `.env` files are NOT automatically loaded into `os.environ` for:
- `execute_code` Python sandbox
- `subprocess.run(['python3', ...])` calls from any tool
- Any Python process spawned via the terminal tool that inherits the parent environment

The variables ARE visible via `env | grep` in the terminal (because the shell has already sourced them), but Python's `os.environ` doesn't see them.

**Working pattern — manual .env parsing:**
```python
import os

env_vars = {}
with open(os.path.expanduser('~/.hermes/.env')) as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            env_vars[k] = v

app_id = env_vars.get('FEISHU_APP_ID', '')
app_secret = env_vars.get('FEISHU_APP_SECRET', '')
```

**Alternative — shell-based extraction (messy):**
```bash
source ~/.hermes/.env && python3 -c "import os; print(os.environ['FEISHU_APP_ID'])"
```
This works in a `terminal()` heredoc but breaks when Python subprocess doesn't inherit shell vars.

**Key insight:** For any Python code doing API calls (Feishu, OpenAI, SiliconFlow, etc.), always read `.env` manually at the top of the script. Do NOT assume `os.environ['KEY']` will work just because `env | grep KEY` shows the value in terminal.

---

## Session transcript (relevant excerpt)

```
APP_ID: cli_aa9b397824b85bc3
APP_SECRET set: True
Token response code: 0
Tenant token: t-g1045piaI3XSHKWCJOK5LKH53H4S...
✓ Got token: t-g1045piaI3XSHKWCJOK5LKH...
Upload result: {"code": 0, "data": {"file_token": "PgIrbESuEoQW6rxqgjCcTUOFnNd", ...
Import result: {"code": 0, "data": {"ticket": "7643783249911712717"}, ...
Status: {"code": 0, "data": {"result": {"job_status": 0, "token": "KqmPdU...anRh", "url": "https://my.feishu.cn/docx/KqmPdUqRnoUNl1xfXQGcpW2anRh"}}}
✅ 文档创建成功!
```

Pipeline worked end-to-end: Markdown → Drive upload → async import → docx URL.

---

## Feishu Import API complete working pipeline

```python
import json, urllib.request, os, time

# 1. Parse .env manually (required!)
env_vars = {}
with open(os.path.expanduser('~/.hermes/.env')) as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            env_vars[k] = v

app_id = env_vars.get('FEISHU_APP_ID', '')
app_secret = env_vars.get('FEISHU_APP_SECRET', '')

# 2. Get tenant access token
url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
data = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode()
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=10) as resp:
    tenant_token = json.loads(resp.read()).get('tenant_access_token', '')

# 3. Upload markdown file
with open('/path/to/file.md', 'rb') as f:
    file_content = f.read()

boundary = '----PythonFormBoundary7MA4YWxkTrZu0gW'
file_name = 'document-name.md'
file_size = len(file_content)

body = (
    f'--{boundary}\r\nContent-Disposition: form-data; name="file_name"\r\n\r\n{file_name}\r\n'
    f'--{boundary}\r\nContent-Disposition: form-data; name="parent_type"\r\n\r\nexplorer\r\n'
    f'--{boundary}\r\nContent-Disposition: form-data; name="parent_node"\r\n\r\n\r\n'
    f'--{boundary}\r\nContent-Disposition: form-data; name="size"\r\n\r\n{file_size}\r\n'
    f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{file_name}"\r\n'
    f'Content-Type: text/markdown\r\n\r\n'
).encode() + file_content + f'\r\n--{boundary}--\r\n'.encode()

req = urllib.request.Request(
    'https://open.feishu.cn/open-apis/drive/v1/files/upload_all',
    data=body,
    headers={
        'Authorization': f'Bearer {tenant_token}',
        'Content-Type': f'multipart/form-data; boundary={boundary}',
    }
)
with urllib.request.urlopen(req, timeout=30) as resp:
    file_token = json.loads(resp.read())['data']['file_token']

# 4. Create import task
payload = {
    "file_extension": "md",
    "file_name": file_name,
    "file_token": file_token,
    "type": "docx",
    "point": {"mount_type": 1, "mount_node_token": "", "mount_key": ""}
}
req = urllib.request.Request(
    'https://open.feishu.cn/open-apis/drive/v1/import_tasks',
    data=json.dumps(payload).encode(),
    headers={"Authorization": f"Bearer {tenant_token}", "Content-Type": "application/json"}
)
with urllib.request.urlopen(req, timeout=10) as resp:
    ticket = json.loads(resp.read())['data']['ticket']

# 5. Poll for completion
time.sleep(5)
req = urllib.request.Request(
    f"https://open.feishu.cn/open-apis/drive/v1/import_tasks/{ticket}",
    headers={"Authorization": f"Bearer {tenant_token}"}
)
with urllib.request.urlopen(req, timeout=10) as resp:
    result = json.loads(resp.read())

job_status = result['data']['result']['job_status']
if job_status == 0:
    doc_token = result['data']['result']['token']
    doc_url = result['data']['result']['url']
    print(f"✅ Document created: {doc_url}")
```
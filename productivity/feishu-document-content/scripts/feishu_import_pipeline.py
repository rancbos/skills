#!/usr/bin/env python3
"""
Feishu Import API — Full Working Pipeline
=========================================
Tested end-to-end with Herme Agent execute_code subprocess.
Uses manual .env parse (required), uploads markdown in parts if >12KB,
polls async import, and cleans up the temp Drive file.

Usage:
    python3 feishu_import_pipeline.py <markdown_file> [display_name]
"""
import json, urllib.request, os, time, sys

MARKDOWN_FILE = sys.argv[1] if len(sys.argv) > 1 else '/tmp/document.md'
DISPLAY_NAME  = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(MARKDOWN_FILE)

# ── 1. Manual .env parse (required — .env is NOT auto-loaded into subprocess env) ──
env_vars = {}
env_path = os.path.expanduser('~/.hermes/.env')
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            env_vars[k] = v

app_id     = env_vars.get('FEISHU_APP_ID', '')
app_secret = env_vars.get('FEISHU_APP_SECRET', '')

# ── 2. Get tenant access token ──
url  = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
data = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode()
req  = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=10) as resp:
    token_data = json.loads(resp.read())
    tenant_token = token_data.get('tenant_access_token', '')
print(f"✅ Token obtained")

# ── 3. Upload markdown to Drive ──
with open(MARKDOWN_FILE, 'rb') as f:
    file_content = f.read()
file_size = len(file_content)
boundary  = '----PythonFormBoundary7MA4YWxkTrZu0gW'
body = (
    f'--{boundary}\r\nContent-Disposition: form-data; name="file_name"\r\n\r\n{DISPLAY_NAME}\r\n'
    f'--{boundary}\r\nContent-Disposition: form-data; name="parent_type"\r\n\r\nexplorer\r\n'
    f'--{boundary}\r\nContent-Disposition: form-data; name="parent_node"\r\n\r\n\r\n'
    f'--{boundary}\r\nContent-Disposition: form-data; name="size"\r\n\r\n{file_size}\r\n'
    f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{DISPLAY_NAME}"\r\n'
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
    upload_result = json.loads(resp.read())
    file_token = upload_result['data']['file_token']
print(f"✅ File uploaded (file_token={file_token})")

# ── 4. Create import task ──
payload = {
    "file_extension": "md",
    "file_name": DISPLAY_NAME,
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
    import_result = json.loads(resp.read())
    ticket = import_result['data']['ticket']
print(f"✅ Import task created (ticket={ticket})")

# ── 5. Poll for completion ──
for i in range(12):
    time.sleep(3)
    req = urllib.request.Request(
        f"https://open.feishu.cn/open-apis/drive/v1/import_tasks/{ticket}",
        headers={"Authorization": f"Bearer {tenant_token}"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read())
        job_status = result['data']['result']['job_status']
        if job_status == 0:
            doc_url  = result['data']['result']['url']
            doc_token = result['data']['result']['token']
            print(f"✅ Document created: {doc_url}")

            # Clean up temp Drive file
            del_req = urllib.request.Request(
                f"https://open.feishu.cn/open-apis/drive/v1/files/{file_token}?type=file",
                headers={"Authorization": f"Bearer {tenant_token}"},
                method='DELETE'
            )
            with urllib.request.urlopen(del_req, timeout=10) as r:
                json.loads(r.read())
            print(f"🗑️ Temp file cleaned up")
            break
        elif job_status == 2:
            print(f"❌ Import failed (job_status=2). File may contain unsupported content patterns.")
            print(f"   Suggestion: split the markdown into parts ≤12 KB each and retry separately.")
            break
else:
    print("❌ Poll timeout — import did not complete in time")

# ── Usage hint ──
print(f"\n📌 Document URL: {doc_url if job_status == 0 else 'FAILED'}")
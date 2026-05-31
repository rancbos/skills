# Cloud Server Headless Browser Setup

## When to Use
Cloud server (Ubuntu/Debian) with no GUI. Need browser automation via CDP.

## Prerequisites
- Google Chrome installed (`apt install google-chrome-stable` or download .deb)
- Node.js 22+ (for cdp-proxy.mjs native WebSocket)

## Verified Commands (Chrome 148, Ubuntu 24.04)

### Start Chrome Headless
```bash
google-chrome-stable \
  --headless=new \
  --no-sandbox \
  --disable-gpu \
  --disable-dev-shm-usage \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-clean
```

**Critical flags:**
- `--headless=new` — new headless mode (NOT `--headless` alone, which uses deprecated old mode)
- `--no-sandbox` — **required** on servers, no GUI means no user namespace for sandbox
- `--disable-dev-shm-usage` — prevents /dev/shm exhaustion in containers/small-memory VPS
- `--user-data-dir=/tmp/chrome-clean` — clean profile each start, avoids stale state

### Verify CDP Ready
```bash
curl http://127.0.0.1:9222/json/version
# Should return Browser version, Protocol-Version, webSocketDebuggerUrl
```

### Start CDP Proxy
```bash
cd /root/.hermes/skills/web-access/scripts
node cdp-proxy.mjs
```

### Verify Proxy Healthy
```bash
curl http://localhost:3456/health
# Should return {"status":"ok","connected":true,"sessions":0,"chromePort":9222}
```

## Systemd Auto-Start (Optional)

```bash
# Chrome headless service
sudo tee /etc/systemd/system/chrome-headless.service << 'EOF'
[Unit]
Description=Chrome Headless for CDP
After=network.target

[Service]
ExecStart=/usr/bin/google-chrome-stable --headless=new --no-sandbox --disable-gpu --disable-dev-shm-usage --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-clean
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

# CDP Proxy service
sudo tee /etc/systemd/system/cdp-proxy.service << 'EOF'
[Unit]
Description=CDP Proxy for web-access
After=network.target chrome-headless.service

[Service]
ExecStart=/root/.hermes/node/bin/node /root/.hermes/skills/web-access/scripts/cdp-proxy.mjs
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable chrome-headless cdp-proxy
sudo systemctl start chrome-headless cdp-proxy
```

## Common Pitfalls

1. **`--no-sandbox` is mandatory** — without it, Chrome's sandbox fails in headless server environments (no user namespace, no display). Error: "Failed to move to new namespace"

2. **First navigation may return empty content** — `/new?url=X` creates a tab and navigates, but the page may not fully load on first attempt. Follow up with `/navigate?target=ID&url=X` + `sleep 2` to ensure content loads. See "Pitfall: First Navigation Empty" below.

3. **WebSocket URL localhost vs 127.0.0.1** — Chrome returns `ws://localhost:9222/...` but Node.js may resolve localhost to IPv6 (::1) which Chrome doesn't listen on. cdp-proxy.mjs handles this rewrite, but if writing custom scripts, always replace `localhost` with `127.0.0.1` in WebSocket URLs.

4. **Port 9222 already in use** — Kill existing Chrome before restart: `pkill -f "chrome.*remote-debugging"`

5. **`/devtools/browser` vs `/devtools/page/{id}`** — In `headless=new` mode, the browser-level WebSocket endpoint may not work. Use HTTP JSON API (`/json/new`, `/json`, `/json/close/{id}`) for lifecycle management, and per-page WebSocket for CDP commands.

## Pitfall: First Navigation Empty (Verified 2026-05-29)

**Symptom:** `GET /new?url=https://www.baidu.com` returns targetId, but `POST /eval` returns empty title, and `/screenshot` shows blank white page.

**Root cause:** Page creation + initial navigation race condition in headless=new mode. The HTTP response returns before the page finishes loading.

**Fix:** After `/new`, follow up with explicit `/navigate` + sleep:
```bash
# Create tab
TARGET=$(curl -s "http://localhost:3456/new?url=https://www.baidu.com" | jq -r .targetId)
sleep 2
# Re-navigate to ensure load
curl -s "http://localhost:3456/navigate?target=$TARGET&url=https://www.baidu.com"
sleep 3
# Now eval returns correct title
curl -s -X POST "http://localhost:3456/eval?target=$TARGET" -d 'document.title'
# → {"value":"百度一下，你就知道"}
```

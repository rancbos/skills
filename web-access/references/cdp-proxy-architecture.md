# CDP Proxy 架构与已知问题

> 更新日期：2026-05-26  
> 背景：headless=new Chrome 的 CDP 协议行为与旧版有重大变化，本文件记录验证过的架构决策

---

## 核心架构决策

### headless=new vs headless=old

| 特性 | `headless=old` | `headless=new`（当前主力）|
|------|----------------|--------------------------|
| `/devtools/browser` WebSocket | ✅ 可用 | ❌ **不存在**，HTTP 400 或 WS 失败 |
| `/devtools/page/{id}` WebSocket | ✅ 可用 | ✅ 可用 |
| HTTP JSON API | ❌ 不可用 | ✅ 可用（`/json/new`, `/json`, `/json/close/{id}`）|

**结论：始终用 HTTP JSON API 管理 target 生命周期，per-target page WS 发送命令。**

### 命令发送架构

```
browser WS (ws://127.0.0.1:9222/devtools/browser/{uuid})
  └─ 仅用于初始连接握手，获取 target 列表

target WS Map (targetWsMap: Map<targetId, pageWs>)
  └─ 每条 CDP 命令通过 sendCDPToWs(targetId, method, params)
       └─ pageWs = targetWsMap.get(targetId)
       └─ sendCDPOnWs(pageWs, method, params)
            └─ 每条命令独立 addEventListener/removeEventListener
               （不用全局 pending Map，避免多路复用冲突）
```

**关键陷阱：不要用 browser WS 发 per-target 命令。**  
`sendCDP` 若写到 browser WS 而 target 实际在 page WS，两边状态不同步，导致 `/info`、`/screenshot` 等操作超时。

### 等待页面加载

```javascript
// ✅ 正确：绑定到具体 page WebSocket
function waitForLoadOnWs(pageWs, timeoutMs = 15000) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('load timeout')), timeoutMs);
    const handler = (evt) => {
      const data = typeof evt === 'string' ? evt : (evt.data || evt);
      const msg = JSON.parse(data.toString());
      if (msg.method === 'Page.loadEventFired') {
        clearTimeout(timer);
        pageWs.removeEventListener('message', handler);
        resolve();
      }
    };
    pageWs.addEventListener('message', handler);
  });
}

// ❌ 错误：等待 browser WS 的事件，但页面事件只发到 page WS
function waitForLoad(browserWs) { ... } // 不存在 browser 级别的 load 事件
```

### localhost vs 127.0.0.1

Chrome DevTools 协议返回的 `webSocketDebuggerUrl` 通常是 `ws://localhost:...`，但 Node.js 优先 IPv6 解析（`::1`）可能导致连接失败。

**修复：** 将 URL 中的 `localhost` 替换为 `127.0.0.1` 再连接。

```javascript
wsUrl = wsUrl.replace('localhost', '127.0.0.1');
```

---

## 已知行为

### Chrome 实例共享冲突

headless Chrome 实例共享同一个 `--user-data-dir` 时会报 `ProcessSingleton` 冲突：

```
Failed to create a ProcessSingleton for your profile directory.
Aborting now to avoid profile corruption.
```

**解决：** 每次启动用不同的 `--user-data-dir`，如 `/tmp/chrome-1`、`/tmp/chrome-2`。

### headless=new 的 GPU 限制

云服务器无 GPU，`--disable-gpu` 必需。部分 GPU 相关警告（如 SwiftShader、on-device ML）可忽略，不影响功能。

```
[ERROR] on_device_model service disconnect — Required limit (14336) > supported limit (8192)
```

这是 Chrome 尝试用软件渲染器，警告不影响浏览器自动化。

### SingletonLock 文件残留

`/tmp/chrome-clean/SingletonLock` 文件存在会导致后续启动失败：

```
Failed to create /tmp/chrome-clean/SingletonLock: File exists (17)
```

**解决：** 启动前 `pkill -f chrome` 清理进程，或手动 `rm /tmp/chrome-*/SingletonLock`。

---

## 验证流程

```bash
# 1. 启动 Chrome（如未运行）
google-chrome --headless=new --no-sandbox --disable-gpu \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-clean

# 2. 启动 Proxy（如未运行）
node /root/.hermes/skills/web-access/scripts/cdp-proxy.mjs

# 3. 健康检查
curl http://localhost:3456/health
# 期望: {"status":"ok","connected":true,"sessions":0,"chromePort":9222}

# 4. 功能验证
TARGET=$(curl -s "http://localhost:3456/new?url=https://www.baidu.com" | jq -r '.targetId')
sleep 3
curl -s "http://localhost:3456/info?target=$TARGET"
# 期望: {"title":"百度一下，你就知道","url":"https://www.baidu.com/","ready":"complete"}
```

---

## 参考

- Chrome DevTools Protocol JSON API: https://chromedevtools.github.io/devtools-protocol/
- cdp-proxy.mjs 源码: `/root/.hermes/skills/web-access/scripts/cdp-proxy.mjs`
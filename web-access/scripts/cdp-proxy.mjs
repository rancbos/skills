#!/usr/bin/env node
// CDP Proxy - 通过 HTTP API 操控用户日常 Chrome
// 要求：Chrome 已开启 --remote-debugging-port
// Node.js 22+（使用原生 WebSocket）

import http from 'node:http';
import { URL } from 'node:url';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import net from 'node:net';

const PORT = parseInt(process.env.CDP_PROXY_PORT || '3456');
let ws = null;
let cmdId = 0;
const pending = new Map(); // id -> {resolve, timer}
const sessions = new Map(); // targetId -> sessionId

// --- WebSocket 兼容层 ---
let WS;
if (typeof globalThis.WebSocket !== 'undefined') {
  // Node 22+ 原生 WebSocket（浏览器兼容 API）
  WS = globalThis.WebSocket;
} else {
  // 回退到 ws 模块
  try {
    WS = (await import('ws')).default;
  } catch {
    console.error('[CDP Proxy] 错误：Node.js 版本 < 22 且未安装 ws 模块');
    console.error('  解决方案：升级到 Node.js 22+ 或执行 npm install -g ws');
    process.exit(1);
  }
}

// --- 自动发现 Chrome 调试端口 ---
async function discoverChromePort() {
  // 1. 尝试读 DevToolsActivePort 文件
  const possiblePaths = [];
  const platform = os.platform();

  if (platform === 'darwin') {
    const home = os.homedir();
    possiblePaths.push(
      path.join(home, 'Library/Application Support/Google/Chrome/DevToolsActivePort'),
      path.join(home, 'Library/Application Support/Google/Chrome Canary/DevToolsActivePort'),
      path.join(home, 'Library/Application Support/Chromium/DevToolsActivePort'),
    );
  } else if (platform === 'linux') {
    const home = os.homedir();
    possiblePaths.push(
      path.join(home, '.config/google-chrome/DevToolsActivePort'),
      path.join(home, '.config/chromium/DevToolsActivePort'),
    );
  } else if (platform === 'win32') {
    const localAppData = process.env.LOCALAPPDATA || '';
    possiblePaths.push(
      path.join(localAppData, 'Google/Chrome/User Data/DevToolsActivePort'),
      path.join(localAppData, 'Chromium/User Data/DevToolsActivePort'),
    );
  }

  for (const p of possiblePaths) {
    try {
      const content = fs.readFileSync(p, 'utf-8').trim();
      const lines = content.split('\n');
      const port = parseInt(lines[0]);
      if (port > 0 && port < 65536) {
        const ok = await checkPort(port);
        if (ok) {
          // 第二行是带 UUID 的 WebSocket 路径（如 /devtools/browser/xxx-xxx）
          // 非显式 --remote-debugging-port 启动时，Chrome 可能只接受此路径
          const wsPath = lines[1] || null;
          console.log(`[CDP Proxy] 从 DevToolsActivePort 发现端口: ${port}${wsPath ? ' (带 wsPath)' : ''}`);
          return { port, wsPath };
        }
      }
    } catch { /* 文件不存在，继续 */ }
  }

  // 2. 扫描常用端口
  const commonPorts = [9222, 9229, 9333];
  for (const port of commonPorts) {
    const ok = await checkPort(port);
    if (ok) {
      console.log(`[CDP Proxy] 扫描发现 Chrome 调试端口: ${port}`);
      return { port, wsPath: null };
    }
  }

  return null;
}

// 用 TCP 探测端口是否监听——避免 WebSocket 连接触发 Chrome 安全弹窗
// （WebSocket 探测会被 Chrome 视为调试连接，弹出授权对话框）
function checkPort(port) {
  return new Promise((resolve) => {
    const socket = net.createConnection(port, '127.0.0.1');
    const timer = setTimeout(() => { socket.destroy(); resolve(false); }, 2000);
    socket.once('connect', () => { clearTimeout(timer); socket.destroy(); resolve(true); });
    socket.once('error', () => { clearTimeout(timer); resolve(false); });
  });
}

function getWebSocketUrl(port, wsPath) {
  if (wsPath) return `ws://127.0.0.1:${port}${wsPath}`;
  return `ws://127.0.0.1:${port}/devtools/browser`;
}

// --- WebSocket 连接管理 ---
let chromePort = null;
let chromeWsPath = null;
const targetWsMap = new Map(); // targetId -> WebSocket

async function connectToBrowserTarget(port) {
  // New headless Chrome doesn't expose /devtools/browser WS endpoint.
  // Instead we use the HTTP JSON API to discover page targets and connect directly.
  try {
    const httpRes = await fetch(`http://127.0.0.1:${port}/json`);
    const targets = await httpRes.json();
    
    // Find a page target
    const page = targets.find(t => t.type === 'page');
    if (!page) throw new Error('没有找到页面 target');
    
    const wsUrl = page.webSocketDebuggerUrl;
    console.log(`[CDP Proxy] 连接页面 target: ${page.id} (${page.url})`);
    console.log(`[CDP Proxy] WS URL: ${wsUrl}`);
    
    return new Promise((resolve, reject) => {
      ws = new WS(wsUrl);
      let resolved = false;
      const onOpen = () => {
        if (resolved) return;
        resolved = true;
        cleanup();
        console.log(`[CDP Proxy] 已连接 Chrome (页面模式, 端口 ${port})`);
        resolve();
      };
      const onError = (e) => {
        if (resolved) return;
        resolved = true;
        cleanup();
        const msg = e.message || e.error?.message || '连接失败';
        console.error('[CDP Proxy] 连接错误:', msg);
        reject(new Error(msg));
      };
      const onClose = () => {
        console.log('[CDP Proxy] 连接断开');
        ws = null;
        targetWsMap.clear();
        sessions.clear();
      };
      const onMessage = (evt) => {
        const data = typeof evt === 'string' ? evt : (evt.data || evt);
        const msg = JSON.parse(typeof data === 'string' ? data : data.toString());
        if (msg.method === 'Target.attachedToTarget') {
          const { sessionId, targetInfo } = msg.params;
          sessions.set(targetInfo.targetId, sessionId);
        }
        if (msg.id && pending.has(msg.id)) {
          const { resolve, timer } = pending.get(msg.id);
          clearTimeout(timer);
          pending.delete(msg.id);
          resolve(msg);
        }
      };
      function cleanup() {
        ws.removeEventListener?.('open', onOpen);
        ws.removeEventListener?.('error', onError);
        ws.removeEventListener?.('close', onClose);
        ws.removeEventListener?.('message', onMessage);
      }
      if (ws.on) {
        ws.on('open', onOpen);
        ws.on('error', onError);
        ws.on('close', onClose);
        ws.on('message', onMessage);
      } else {
        ws.addEventListener('open', onOpen);
        ws.addEventListener('error', onError);
        ws.addEventListener('close', onClose);
        ws.addEventListener('message', onMessage);
      }
    });
  } catch (e) {
    throw new Error('无法通过 /json 接口连接 Chrome: ' + e.message);
  }
}

async function connect() {
  if (ws && (ws.readyState === WS.OPEN || ws.readyState === 1)) return;

  if (!chromePort) {
    const discovered = await discoverChromePort();
    if (!discovered) {
      throw new Error(
        'Chrome 未开启远程调试端口。请用以下方式启动 Chrome：\n' +
        '  macOS: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222\n' +
        '  Linux: google-chrome --remote-debugging-port=9222\n' +
        '  或在 chrome://flags 中搜索 "remote debugging" 并启用'
      );
    }
    chromePort = discovered.port;
    chromeWsPath = discovered.wsPath;
  }

  // 直接使用页面级 WS 连接（绕过 /devtools/browser）
  await connectToBrowserTarget(chromePort);
}

// Page-level WS: no session wrapping needed, send commands directly
// (Only used for the initial browser connection; per-target commands go through sendCDPToWs)
function sendCDP(method, params = {}, sessionId = null) {
  return new Promise((resolve, reject) => {
    if (!ws || (ws.readyState !== WS.OPEN && ws.readyState !== 1)) {
      return reject(new Error('WebSocket 未连接'));
    }
    const id = ++cmdId;
    const msg = { id, method, params };
    // Note: page-level WS doesn't use sessionId wrapping
    const timer = setTimeout(() => {
      pending.delete(id);
      reject(new Error('CDP 命令超时: ' + method));
    }, 30000);
    pending.set(id, { resolve, timer });
    ws.send(JSON.stringify(msg));
  });
}

// --- 发送 CDP 命令到指定 WebSocket（带独立 message handler）---
function sendCDPOnWs(pageWs, method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++cmdId;
    const timer = setTimeout(() => {
      pending.delete(id);
      reject(new Error('CDP 命令超时: ' + method));
    }, 30000);

    const handler = (evt) => {
      const data = typeof evt === 'string' ? evt : (evt.data || evt);
      const msg = JSON.parse(typeof data === 'string' ? data : data.toString());
      if (msg.id === id) {
        clearTimeout(timer);
        pageWs.removeEventListener('message', handler);
        pending.delete(id);
        resolve(msg);
      }
    };

    pageWs.addEventListener('message', handler);
    pageWs.send(JSON.stringify({ id, method, params }));
  });
}

// --- 发送 CDP 命令到特定 target 的 WS ---
function sendCDPToWs(targetId, method, params = {}) {
  const pageWs = targetWsMap.get(targetId);
  if (!pageWs) throw new Error('未找到 target ' + targetId + ' 的 WS 连接');
  return sendCDPOnWs(pageWs, method, params);
}

// --- 等待页面加载（给定任意 WebSocket）---
function waitForLoadOnWs(pageWs, timeoutMs = 15000) {
  return new Promise((resolve, reject) => {
    let localCmdId = 100;
    let resolved = false;
    const pendingLocal = new Map();

    const timer = setTimeout(() => {
      if (!resolved) { resolved = true; resolve('timeout'); }
    }, timeoutMs);

    const onMsg = (evt) => {
      const data = typeof evt === 'string' ? evt : (evt.data || evt);
      const msg = JSON.parse(typeof data === 'string' ? data : data.toString());
      if (msg.id && pendingLocal.has(msg.id)) {
        const { resolve, timer } = pendingLocal.get(msg.id);
        clearTimeout(timer);
        pendingLocal.delete(msg.id);
        resolve(msg);
      }
    };
    pageWs.addEventListener('message', onMsg);

    function doCheck() {
      if (resolved) return;
      const id = ++localCmdId;
      const timer2 = setTimeout(() => {
        if (!resolved) {
          resolved = true;
          clearTimeout(timer);
          pageWs.removeEventListener('message', onMsg);
          resolve('complete');
        }
      }, 15000);

      pendingLocal.set(id, { resolve: (r) => {
        if (resolved) return;
        if (r.result?.result?.value === 'complete') {
          resolved = true;
          clearTimeout(timer);
          clearTimeout(timer2);
          pageWs.removeEventListener('message', onMsg);
          resolve('complete');
        } else {
          clearTimeout(timer2);
          setTimeout(doCheck, 500);
        }
      }});

      pageWs.send(JSON.stringify({ id, method: 'Runtime.evaluate', params: { expression: 'document.readyState', returnByValue: true } }));
    }

    doCheck();
  });
}

// Page-level WS 直接发送命令，不需要 ensureSession（页面即 session）
async function ensureSession(targetId) {
  // 在 page-level WS 模式下，连接的页面就是 session，无需 attach
  return null;
}

// --- 等待页面加载 ---
async function waitForLoad(sessionId, timeoutMs = 15000) {
  // 启用 Page 域
  await sendCDP('Page.enable', {}, sessionId);

  return new Promise((resolve) => {
    let resolved = false;
    const done = (result) => {
      if (resolved) return;
      resolved = true;
      clearTimeout(timer);
      clearInterval(checkInterval);
      resolve(result);
    };

    const timer = setTimeout(() => done('timeout'), timeoutMs);
    const checkInterval = setInterval(async () => {
      try {
        const resp = await sendCDP('Runtime.evaluate', {
          expression: 'document.readyState',
          returnByValue: true,
        }, sessionId);
        if (resp.result?.result?.value === 'complete') {
          done('complete');
        }
      } catch { /* 忽略 */ }
    }, 500);
  });
}

// --- 读取 POST body ---
async function readBody(req) {
  let body = '';
  for await (const chunk of req) body += chunk;
  return body;
}

// --- HTTP API ---
const server = http.createServer(async (req, res) => {
  const parsed = new URL(req.url, `http://localhost:${PORT}`);
  const pathname = parsed.pathname;
  const q = Object.fromEntries(parsed.searchParams);

  res.setHeader('Content-Type', 'application/json; charset=utf-8');

  try {
    // /health 不需要连接 Chrome
    if (pathname === '/health') {
      const connected = ws && (ws.readyState === WS.OPEN || ws.readyState === 1);
      res.end(JSON.stringify({ status: 'ok', connected, sessions: sessions.size, chromePort }));
      return;
    }

    await connect();

    // GET /targets - 列出所有页面（通过 HTTP JSON API）
    if (pathname === '/targets') {
      const httpRes = await fetch(`http://127.0.0.1:${chromePort}/json`);
      const targets = await httpRes.json();
      const pages = targets.filter(t => t.type === 'page');
      res.end(JSON.stringify(pages, null, 2));
    }

    // GET /new?url=xxx - 创建新后台 tab（通过 HTTP JSON API）
    else if (pathname === '/new') {
      const targetUrl = q.url || 'about:blank';
      // 通过 Chrome HTTP API 创建 target（绕过 /devtools/browser WS 限制）
      const httpRes = await fetch(`http://127.0.0.1:${chromePort}/json/new?url=${encodeURIComponent(targetUrl)}`, { method: 'PUT' });
      const newTarget = await httpRes.json();
      const targetId = newTarget.id;
      const wsUrl = newTarget.webSocketDebuggerUrl;

      // 为新 target 建立独立的 WS 连接
      const pageWs = await new Promise((resolve, reject) => {
        const pw = new WS(wsUrl);
        pw.onopen = () => resolve(pw);
        pw.onerror = (e) => reject(new Error(e.message || 'WS连接失败'));
        setTimeout(() => reject(new Error('连接新页面 WS 超时')), 10000);
      });
      targetWsMap.set(targetId, pageWs);

      // 等待页面加载
      if (targetUrl !== 'about:blank') {
        try {
          await waitForLoadOnWs(pageWs, 15000);
        } catch { /* 非致命，继续 */ }
      }

      res.end(JSON.stringify({ targetId, wsUrl }));
    }

    // GET /close?target=xxx - 关闭 tab（通过 HTTP JSON API）
    else if (pathname === '/close') {
      const httpRes = await fetch(`http://127.0.0.1:${chromePort}/json/close/${q.target}`, { method: 'DELETE' });
      const result = await httpRes.json();
      targetWsMap.delete(q.target);
      sessions.delete(q.target);
      res.end(JSON.stringify(result));
    }

    // GET /navigate?target=xxx&url=yyy - 导航（通过目标 WS）
    else if (pathname === '/navigate') {
      const targetId = q.target;
      if (!targetWsMap.has(targetId)) {
        res.statusCode = 400;
        res.end(JSON.stringify({ error: '未找到 target ' + targetId + '，请先用 /new 创建' }));
        return;
      }
      await sendCDPToWs(targetId, 'Page.navigate', { url: q.url });
      await waitForLoadOnWs(targetWsMap.get(targetId), 15000);
      res.end(JSON.stringify({ ok: true }));
    }

    // GET /back?target=xxx - 后退
    else if (pathname === '/back') {
      if (!targetWsMap.has(q.target)) {
        res.statusCode = 400;
        res.end(JSON.stringify({ error: '未找到 target' }));
        return;
      }
      await sendCDPToWs(q.target, 'Runtime.evaluate', { expression: 'history.back()' });
      await waitForLoadOnWs(targetWsMap.get(q.target), 15000);
      res.end(JSON.stringify({ ok: true }));
    }

    // POST /eval?target=xxx - 执行 JS
    else if (pathname === '/eval') {
      if (!targetWsMap.has(q.target)) {
        res.statusCode = 400;
        res.end(JSON.stringify({ error: '未找到 target' }));
        return;
      }
      const body = await readBody(req);
      const expr = body || q.expr || 'document.title';
      const resp = await sendCDPToWs(q.target, 'Runtime.evaluate', {
        expression: expr,
        returnByValue: true,
        awaitPromise: true,
      });
      if (resp.result?.result?.value !== undefined) {
        res.end(JSON.stringify({ value: resp.result.result.value }));
      } else if (resp.result?.exceptionDetails) {
        res.statusCode = 400;
        res.end(JSON.stringify({ error: resp.result.exceptionDetails.text }));
      } else {
        res.end(JSON.stringify(resp.result));
      }
    }

    // POST /click?target=xxx - 点击（body 为 CSS 选择器）
    else if (pathname === '/click') {
      if (!targetWsMap.has(q.target)) {
        res.statusCode = 400;
        res.end(JSON.stringify({ error: '未找到 target' }));
        return;
      }
      const selector = await readBody(req);
      if (!selector) {
        res.statusCode = 400;
        res.end(JSON.stringify({ error: 'POST body 需要 CSS 选择器' }));
        return;
      }
      const selectorJson = JSON.stringify(selector);
      const js = `(() => {
        const el = document.querySelector(${selectorJson});
        if (!el) return { error: '未找到元素: ' + ${selectorJson} };
        el.scrollIntoView({ block: 'center' });
        el.click();
        return { clicked: true, tag: el.tagName, text: (el.textContent || '').slice(0, 100) };
      })()`;
      const resp = await sendCDPToWs(q.target, 'Runtime.evaluate', {
        expression: js,
        returnByValue: true,
        awaitPromise: true,
      });
      if (resp.result?.result?.value) {
        const val = resp.result.result.value;
        if (val.error) {
          res.statusCode = 400;
          res.end(JSON.stringify(val));
        } else {
          res.end(JSON.stringify(val));
        }
      } else {
        res.end(JSON.stringify(resp.result));
      }
    }

    // POST /clickAt?target=xxx — CDP 浏览器级真实鼠标点击
    else if (pathname === '/clickAt') {
      if (!targetWsMap.has(q.target)) {
        res.statusCode = 400;
        res.end(JSON.stringify({ error: '未找到 target' }));
        return;
      }
      const selector = await readBody(req);
      if (!selector) {
        res.statusCode = 400;
        res.end(JSON.stringify({ error: 'POST body 需要 CSS 选择器' }));
        return;
      }
      const selectorJson = JSON.stringify(selector);
      const js = `(() => {
        const el = document.querySelector(${selectorJson});
        if (!el) return { error: '未找到元素: ' + ${selectorJson} };
        el.scrollIntoView({ block: 'center' });
        const rect = el.getBoundingClientRect();
        return { x: rect.x + rect.width / 2, y: rect.y + rect.height / 2, tag: el.tagName, text: (el.textContent || '').slice(0, 100) };
      })()`;
      const coordResp = await sendCDPToWs(q.target, 'Runtime.evaluate', {
        expression: js,
        returnByValue: true,
        awaitPromise: true,
      });
      const coord = coordResp.result?.result?.value;
      if (!coord || coord.error) {
        res.statusCode = 400;
        res.end(JSON.stringify(coord || coordResp.result));
        return;
      }
      await sendCDPToWs(q.target, 'Input.dispatchMouseEvent', {
        type: 'mousePressed', x: coord.x, y: coord.y, button: 'left', clickCount: 1
      });
      await sendCDPToWs(q.target, 'Input.dispatchMouseEvent', {
        type: 'mouseReleased', x: coord.x, y: coord.y, button: 'left', clickCount: 1
      });
      res.end(JSON.stringify({ clicked: true, x: coord.x, y: coord.y, tag: coord.tag, text: coord.text }));
    }

    // POST /setFiles?target=xxx — 给 file input 设置本地文件
    else if (pathname === '/setFiles') {
      if (!targetWsMap.has(q.target)) {
        res.statusCode = 400;
        res.end(JSON.stringify({ error: '未找到 target' }));
        return;
      }
      const body = JSON.parse(await readBody(req));
      if (!body.selector || !body.files) {
        res.statusCode = 400;
        res.end(JSON.stringify({ error: '需要 selector 和 files 字段' }));
        return;
      }
      await sendCDPToWs(q.target, 'DOM.enable');
      const doc = await sendCDPToWs(q.target, 'DOM.getDocument');
      const node = await sendCDPToWs(q.target, 'DOM.querySelector', {
        nodeId: doc.result.root.nodeId,
        selector: body.selector
      });
      if (!node.result?.nodeId) {
        res.statusCode = 400;
        res.end(JSON.stringify({ error: '未找到元素: ' + body.selector }));
        return;
      }
      await sendCDPToWs(q.target, 'DOM.setFileInputFiles', {
        nodeId: node.result.nodeId,
        files: body.files
      });
      res.end(JSON.stringify({ success: true, files: body.files.length }));
    }

    // GET /scroll?target=xxx&y=3000 - 滚动
    else if (pathname === '/scroll') {
      if (!targetWsMap.has(q.target)) {
        res.statusCode = 400;
        res.end(JSON.stringify({ error: '未找到 target' }));
        return;
      }
      const y = parseInt(q.y || '3000');
      const direction = q.direction || 'down';
      let js;
      if (direction === 'top') {
        js = 'window.scrollTo(0, 0); "scrolled to top"';
      } else if (direction === 'bottom') {
        js = 'window.scrollTo(0, document.body.scrollHeight); "scrolled to bottom"';
      } else if (direction === 'up') {
        js = `window.scrollBy(0, -${Math.abs(y)}); "scrolled up ${Math.abs(y)}px"`;
      } else {
        js = `window.scrollBy(0, ${Math.abs(y)}); "scrolled down ${Math.abs(y)}px"`;
      }
      const resp = await sendCDPToWs(q.target, 'Runtime.evaluate', {
        expression: js,
        returnByValue: true,
      });
      await new Promise(r => setTimeout(r, 800));
      res.end(JSON.stringify({ value: resp.result?.result?.value }));
    }

    // GET /screenshot?target=xxx&file=/tmp/x.png - 截图
    else if (pathname === '/screenshot') {
      if (!targetWsMap.has(q.target)) {
        res.statusCode = 400;
        res.end(JSON.stringify({ error: '未找到 target' }));
        return;
      }
      const format = q.format || 'png';
      const resp = await sendCDPToWs(q.target, 'Page.captureScreenshot', {
        format,
        quality: format === 'jpeg' ? 80 : undefined,
      });
      if (q.file) {
        fs.writeFileSync(q.file, Buffer.from(resp.result.data, 'base64'));
        res.end(JSON.stringify({ saved: q.file }));
      } else {
        res.setHeader('Content-Type', 'image/' + format);
        res.end(Buffer.from(resp.result.data, 'base64'));
      }
    }

    // GET /info?target=xxx - 获取页面信息
    else if (pathname === '/info') {
      if (!targetWsMap.has(q.target)) {
        res.statusCode = 400;
        res.end(JSON.stringify({ error: '未找到 target' }));
        return;
      }
      const resp = await sendCDPToWs(q.target, 'Runtime.evaluate', {
        expression: 'JSON.stringify({title: document.title, url: location.href, ready: document.readyState})',
        returnByValue: true,
      });
      res.end(resp.result?.result?.value || '{}');
    }

    else {
      res.statusCode = 404;
      res.end(JSON.stringify({
        error: '未知端点',
        endpoints: {
          '/health': 'GET - 健康检查',
          '/targets': 'GET - 列出所有页面 tab',
          '/new?url=': 'GET - 创建新后台 tab（自动等待加载）',
          '/close?target=': 'GET - 关闭 tab',
          '/navigate?target=&url=': 'GET - 导航（自动等待加载）',
          '/back?target=': 'GET - 后退',
          '/info?target=': 'GET - 页面标题/URL/状态',
          '/eval?target=': 'POST body=JS表达式 - 执行 JS',
          '/click?target=': 'POST body=CSS选择器 - 点击元素',
          '/scroll?target=&y=&direction=': 'GET - 滚动页面',
          '/screenshot?target=&file=': 'GET - 截图',
        },
      }));
    }
  } catch (e) {
    res.statusCode = 500;
    res.end(JSON.stringify({ error: e.message }));
  }
});

// 检查端口是否被占用
function checkPortAvailable(port) {
  return new Promise((resolve) => {
    const s = net.createServer();
    s.once('error', () => resolve(false));
    s.once('listening', () => { s.close(); resolve(true); });
    s.listen(port, '127.0.0.1');
  });
}

async function main() {
  // 检查是否已有 proxy 在运行
  const available = await checkPortAvailable(PORT);
  if (!available) {
    // 验证已有实例是否健康
    try {
      const ok = await new Promise((resolve) => {
        http.get(`http://127.0.0.1:${PORT}/health`, { timeout: 2000 }, (res) => {
          let d = '';
          res.on('data', c => d += c);
          res.on('end', () => resolve(d.includes('"ok"')));
        }).on('error', () => resolve(false));
      });
      if (ok) {
        console.log(`[CDP Proxy] 已有实例运行在端口 ${PORT}，退出`);
        process.exit(0);
      }
    } catch { /* 端口占用但非 proxy，继续报错 */ }
    console.error(`[CDP Proxy] 端口 ${PORT} 已被占用`);
    process.exit(1);
  }

  server.listen(PORT, '127.0.0.1', () => {
    console.log(`[CDP Proxy] 运行在 http://localhost:${PORT}`);
    // 启动时尝试连接 Chrome（非阻塞）
    connect().catch(e => console.error('[CDP Proxy] 初始连接失败:', e.message, '（将在首次请求时重试）'));
  });
}

// 防止未捕获异常导致进程崩溃
process.on('uncaughtException', (e) => {
  console.error('[CDP Proxy] 未捕获异常:', e.message);
});
process.on('unhandledRejection', (e) => {
  console.error('[CDP Proxy] 未处理拒绝:', e?.message || e);
});

main();

---
topic: Camofox 故障排查与手动修复
updated: 2026-06-01
---

# Camofox 故障排查

## 核心问题：自动下载的破坏性循环

**根因**：`camoufox-js` 的 `pkgman.js` 中 `install()` 方法执行顺序为：
1. `this.init()` — 从 GitHub API 获取最新 release 信息
2. `CamoufoxFetcher.cleanup()` — **删除整个 `~/.cache/camoufox/` 目录**
3. 从 GitHub 下载 ~631MB zip
4. 解压 + 写入 `version.json`

当 GitHub 连接超时（中国大陆常见），步骤 3 失败，但步骤 2 已经把本地安装删了。下次启动时又从步骤 1 开始，形成**删了装不上、装不上又删**的死循环。

**日志特征**：
```
ConnectTimeoutError: Connect Timeout Error (attempted address: github.com:443, timeout: 10000ms)
} retrying (X/5)...
```

## 依赖缺失导致 SIGSEGV

Camofox 在无 GUI 服务器上启动需要以下依赖，否则浏览器进程 SIGSEGV 崩溃：

### 1. 字体

```bash
apt-get install -y fonts-noto-cjk fonts-noto
```

日志特征：`GraphicsCriticalError: |[0][GFX1]: no fonts`

### 2. glxtest 二进制

Camoufox 启动时会调用 `~/.cache/camoufox/glxtest` 做 GPU 测试。服务器无 GPU 时需要一个空壳：

```bash
cat > /root/.cache/camoufox/glxtest << 'EOF'
#!/bin/bash
exit 0
EOF
chmod +x /root/.cache/camoufox/glxtest
```

日志特征：`FireTestProcess failed: Failed to spawn child process "glxtest" (No such file or directory)`

## 手动安装 Camoufox 二进制

当自动下载因网络问题失败时，手动安装步骤：

### 步骤 1：停止服务

```bash
systemctl stop camofox
```

### 步骤 2：下载二进制

从 GitHub releases 下载（使用 ghfast.top 镜像绕过网络问题）：

```bash
# 获取最新 release 的下载链接
curl -s "https://api.github.com/repos/daijro/camoufox/releases" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data[:3]:
    for a in r.get('assets', []):
        if 'lin' in a['name'] and 'x86_64' in a['name'] and a['name'].endswith('.zip'):
            print(a['browser_download_url'])
            sys.exit(0)
"

# 使用 ghfast.top 镜像下载（~631MB，约 2 分钟）
mkdir -p /root/.cache/camoufox
curl -L -C - --max-time 600 -o /tmp/camoufox.zip \
  "https://ghfast.top/https://github.com/daijro/camoufox/releases/download/<TAG>/<FILENAME>"
```

### 步骤 3：解压并配置

```bash
cd /root/.cache/camoufox
unzip -o /tmp/camoufox.zip
# version.json 的 release 和 version 必须与下载的二进制匹配
# 格式：zip 文件名 camoufox-{version}-{release}-{os}.{arch}.zip
echo '{"release":"alpha.26","version":"150.0.2"}' > version.json
# glxtest 空壳
cat > glxtest << 'EOF'
#!/bin/bash
exit 0
EOF
chmod +x glxtest
```

### 步骤 4：清理旧 profile 并启动

```bash
rm -rf /root/.camofox/profiles/hermes_*
systemctl start camofox
sleep 5
curl -s http://127.0.0.1:9377/health
```

健康检查应返回 `"ok":true`。

## version.json 格式

`installedVerStr()` 函数读取 `~/.cache/camoufox/version.json`，返回 `{version}-{release}`。

```json
{"release":"alpha.26","version":"150.0.2"}
```
→ `installedVerStr()` = `"150.0.2-alpha.26"`

版本必须与 camofox-browser 的 `pkgman.js` 中 `CamoufoxFetcher` 期望的版本匹配，否则会触发重新下载。

## 已知未解决问题

**自动下载循环**：即使手动安装成功，`camofox server start` 仍可能在启动时触发版本检查并尝试重新下载。如果 GitHub 连接超时，会反复重试。目前没有环境变量可以完全跳过此检查（`PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD` 只跳过检测，不阻止 `install()`）。

**可能的修复方向**：patch `pkgman.js` 中 `install()` 方法，注释掉 `await CamoufoxFetcher.cleanup()` 行，使已有的本地安装不被删除。

## 排查命令速查

```bash
# 服务状态
systemctl status camofox --no-pager

# 实时日志
journalctl -u camofox -f

# 健康检查
curl -s http://127.0.0.1:9377/health

# 检查二进制是否存在
ls -la /root/.cache/camoufox/camoufox-bin
cat /root/.cache/camoufox/version.json

# 检查 profile 目录
ls -la /root/.camofox/profiles/

# 检查字体
fc-list | grep -i noto | head -3

# 检查缺失的共享库
ldd /root/.cache/camoufox/camoufox-bin 2>&1 | grep "not found"
```

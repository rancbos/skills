# 云服务器无 GUI 环境配置指南

Chrome headless + CDP Proxy + systemd 自启 + 中文字体安装。

> **替代方案**：如果只需反检测浏览器能力，可直接安装 [Camofox](SKILL.md#camofox-反检测浏览器hermes-原生集成)（单端口 9377，Hermes 原生集成，无需 CDP Proxy）。两个方案可并存。

## 1. 安装 Google Chrome

```bash
curl -o /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i /tmp/chrome.deb
sudo apt-get install -y -f
```

## 2. 安装中文字体（必须）

不安装中文字体，headless Chrome 渲染中文会显示为方块。

```bash
apt-get install -y fonts-noto-cjk
fc-cache -fv
```

安装后**必须重启 Chrome** 才能加载新字体。

## 3. systemd 服务配置

### Chrome headless 服务

```bash
sudo tee /etc/systemd/system/chrome-headless.service > /dev/null << 'EOF'
[Unit]
Description=Chrome Headless for CDP
After=network.target

[Service]
ExecStart=/usr/bin/google-chrome-stable --headless=new --no-sandbox --disable-gpu --disable-dev-shm-usage --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-clean
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
EOF
```

### CDP Proxy 服务

```bash
sudo tee /etc/systemd/system/cdp-proxy.service > /dev/null << 'EOF'
[Unit]
Description=CDP Proxy for web-access
After=network.target chrome-headless.service

[Service]
ExecStart=/root/.hermes/node/bin/node /root/.hermes/skills/web-access/scripts/cdp-proxy.mjs
Restart=always
RestartSec=5
User=root
Environment=HOME=/root

[Install]
WantedBy=multi-user.target
EOF
```

### 启用并启动

```bash
sudo systemctl daemon-reload
sudo systemctl enable chrome-headless cdp-proxy
sudo systemctl start chrome-headless cdp-proxy
```

## 4. 验证

```bash
# Chrome CDP
curl -s http://127.0.0.1:9222/json/version

# CDP Proxy
curl -s http://localhost:3456/health
```

## 5. 常见问题

### 端口被占用

手动启动的 Chrome/CDP Proxy 进程会占用端口，导致 systemd 服务启动失败。

```bash
# 查找占用端口的进程
lsof -ti:9222  # Chrome
lsof -ti:3456  # CDP Proxy

# 杀掉后重启服务
kill -9 $(lsof -ti:3456)
sudo systemctl restart cdp-proxy
```

### 中文显示为方块

1. 确认已安装 `fonts-noto-cjk`
2. 重启 Chrome：`sudo systemctl restart chrome-headless`
3. 重启 CDP Proxy：`sudo systemctl restart cdp-proxy`

### 首次导航空白

`/new?url=X` 创建页面后首次截图可能白屏。解决：跟一次 `/navigate` + `sleep 2`。

## 6. 服务管理命令

```bash
# 查看状态
sudo systemctl status chrome-headless cdp-proxy

# 重启
sudo systemctl restart chrome-headless cdp-proxy

# 停止
sudo systemctl stop chrome-headless cdp-proxy

# 查看日志
journalctl -u chrome-headless -f
journalctl -u cdp-proxy -f
```

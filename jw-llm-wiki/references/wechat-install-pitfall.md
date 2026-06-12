# wechat-article-to-markdown 安装坑坑

## 背景

wechat-article-to-markdown 是 llm-wiki/jw-llm-wiki 的微信公众号自动提取依赖。安装时容易遇到网络问题。

## 问题1: uv tool install 超时

**症状**：`uv tool install "git+https://github.com/jackwener/wechat-article-to-markdown.git"` 在下载 playwright (47.5MB) 时超时。
**根因**：默认 PyPI 源下载速度慢（~15KB/s）。
**解法**：
```bash
# 1. 清理残留的 uv 环境
uv tool uninstall wechat-article-to-markdown 2>/dev/null

# 2. SSH clone 到本地
git clone --depth=1 git@github.com:jackwener/wechat-article-to-markdown.git /tmp/wechat-wjm

# 3. 用清华镜像 pip install
cd /tmp/wechat-wjm
pip install --break-system-packages -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn .

# 4. 验证
command -v wechat-article-to-markdown
```

## 问题2: HTTPS Git 克隆失败 (GnuTLS -110)

**症状**：`git clone https://github.com/...` 报 `GnuTLS recv error (-110)`
**根因**：本机 HTTPS Git 连接不稳定。
**解法**：改用 SSH（`git clone git@github.com:...`），已验证可用。

## 问题3: pip install 报 externally-managed-environment

**症状**：`pip install .` 报错说环境是 externally-managed。
**解法**：加 `--break-system-packages` 参数。

## 依赖关系

wechat-article-to-markdown 的关键依赖：
- `camoufox[geoip]` — 反指纹浏览器
- `playwright` — 浏览器自动化（47.5MB，下载瓶颈）
- `markdownify` — HTML 转 Markdown
- `beautifulsoup4` — 解析

## 安装后验证

```bash
# 检查命令可用
command -v wechat-article-to-markdown

# 检查 llm-wiki adapter 状态
bash ~/.hermes/skills/jw-llm-wiki/scripts/adapter-state.sh check wechat_article
# 应返回 state=available
```

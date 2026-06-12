# wechat-article-to-markdown 安装 Pitfall

## 问题

`uv tool install "git+https://github.com/jackwener/wechat-article-to-markdown.git"` 在某些机器上会超时：
- HTTPS Git 连接不稳定（GnuTLS recv error -110）
- 大包下载慢（playwright 47.5MB，原源速度 ~15KB/s）

## 解决方案

**方法：SSH clone 到本地 + 清华 PyPI 镜像**

```bash
# 1. SSH clone 到本地（绕过 HTTPS Git 问题）
cd /tmp
git clone --depth 1 git@github.com:jackwener/wechat-article-to-markdown.git /tmp/wechat-wjm-ssh

# 2. 使用清华镜像 pip install（下载速度 1.7MB/s vs 原源 15KB/s）
cd /tmp/wechat-wjm-ssh
pip install --break-system-packages -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn .

# 3. 清理临时文件
rm -rf /tmp/wechat-wjm-ssh
```

## 验证安装

```bash
command -v wechat-article-to-markdown
# 应输出: /usr/local/bin/wechat-article-to-markdown

bash ${SKILL_DIR}/scripts/adapter-state.sh check wechat_article
# 应输出: state=available
```

## 注意事项

- 安装到系统 Python（pip --break-system-packages），命令在 `/usr/local/bin/wechat-article-to-markdown`
- 依赖 playwright（大包），需要足够的磁盘空间
- 如果 SSH 也不可用，可以尝试手动下载 zip 包后本地安装

---
name: bili-transcript
version: "1.1.0"
author: "jw"
description: "B站视频音频提取 + 语音转文字 + 逐字稿生成 + 存入 Obsidian。直接走B站 API，绕过 yt-dlp 412 问题。"
tags:
  - bilibili
  - transcript
  - whisper
  - obsidian
  - speech-to-text
related_skills:
  - obsidian
  - lark-minutes
  - youtube-content
---

# bili-transcript：B站视频 → 逐字稿

从B站视频提取音频，语音转文字生成逐字稿，存入 Obsidian vault。

## 工具链

```
B站 API → curl 下载音频 → ffmpeg 转 WAV → faster-whisper 转写 → opencc 繁简转换 → 存入 Obsidian
```

**不依赖 yt-dlp**（B站 412 问题），直接走 B站公开 API。

## 快速使用

```bash
# 单个视频（最简）
python3 ~/.hermes/skills/bili-transcript/scripts/bili-to-local.py "BV1xzGH6uEG8"

# 指定输出目录和模型
python3 ~/.hermes/skills/bili-transcript/scripts/bili-to-local.py "BV1xzGH6uEG8" "/root/obsidian/B站教程/Claude" "medium"

# 从 URL 解析
python3 ~/.hermes/skills/bili-transcript/scripts/bili-to-local.py "https://www.bilibili.com/video/BV1xzGH6uEG8"
```

## 依赖

| 工具 | 用途 | 状态 |
|------|------|------|
| Python 3 | 脚本运行 | ✅ |
| faster-whisper | 语音转文字 | ✅ 已安装 |
| opencc | 繁简转换 | ✅ 已安装 |
| ffmpeg | 音频格式转换 | ✅ 已安装 |
| yt-dlp | **不使用**（B站 412） | — |

## 流程详解

1. **解析 BV 号** — 从 URL 或纯 BV 号提取
2. **B站 API 获取视频信息** — `api.bilibili.com/x/web-interface/view`
3. **获取音频流 URL** — `api.bilibili.com/x/player/playurl?fnval=16`（DASH 格式）
4. **下载音频** — 用 urllib 下载 .m4s 文件
5. **ffmpeg 转 WAV** — 转为 16kHz 单声道 WAV
6. **faster-whisper 转写** — CPU 模式，small 模型
7. **opencc 繁简转换** — whisper 输出繁体，转为简体
8. **存入 Obsidian** — YAML frontmatter + 逐字稿

## 输出格式

文件存入 `/root/obsidian/B站教程/{上传日期}_{标题}.md`：

```markdown
---
title: "视频标题"
date: 2026-05-24
tags: [B站, 逐字稿]
source: "https://bilibili.com/video/BVxxxxx"
uploader: "UP主名"
duration: "7m37s"
transcript_chars: 2283
transcript_model: "small"
---

# 视频标题

> UP主: xxx | 时长: 7m37s | 日期: 2026-05-24
> 来源: [B站原视频](https://bilibili.com/video/BVxxxxx)

## 逐字稿

[00:00] 大家好今天我们来聊...
[00:15] 首先第一个概念是...
...

---
*由 faster-whisper (small) 自动生成，2283字 ≈ 1598 tokens*
```

## 性能参考

| 视频时长 | CPU small 模型转写时间 | 说明 |
|----------|----------------------|------|
| 3分钟 | ~90秒 | 短视频快 |
| 7分钟 | ~325秒 | 中等 |
| 15分钟 | ~600秒 | 较慢 |
| 30分钟+ | 建议用 medium 模型 | 或走飞书妙记 |

## Whisper 模型选择

| 模型 | 大小 | CPU速度 | 准确率 | 推荐 |
|------|------|---------|--------|------|
| tiny | 75MB | 最快 | 低 | ❌ |
| base | 142MB | 快 | 一般 | ❌ |
| small | 466MB | 中等 | 好 | ✅ 默认 |
| medium | 1.5GB | 慢 | 很好 | 长视频 |
| large-v3 | 3GB | 很慢 | 最好 | 有GPU时 |

## 批量处理

```bash
for bvid in "BV1xxx" "BV2xxx" "BV3xxx"; do
  python3 ~/.hermes/skills/bili-transcript/scripts/bili-to-local.py "$bvid"
  sleep 5
done
```

## Pitfalls

- **yt-dlp 对 B站返回 412 Precondition Failed**：yt-dlp（至少到 2026.03.17 版本）的 BiliBili 提取器在服务器环境下被 B站反爬拦截，即使提供浏览器 cookie 也无法绕过。**解决方案**：用 Python 脚本直接走 B站公开 API（`bili-to-local.py`），不依赖 yt-dlp。
- **HuggingFace 国内不可达**：faster-whisper 模型下载会连接 `huggingface.co`，在国内服务器超时。**解决方案**：设置 `HF_ENDPOINT=https://hf-mirror.com`。
- **whisper 输出繁体中文**：faster-whisper 的 small/medium 模型对中文音频默认输出繁体。**解决方案**：用 `opencc-python-reimplemented`（`OpenCC('t2s')`），脚本已内置。
- **纯音乐视频转写为空**：whisper 对纯音乐（无人声）识别结果为空，这是正常行为。
- **CPU 转写速度参考**：small 模型在 CPU 上约 0.3x 实时（7分钟视频约 325 秒），长视频建议走飞书妙记云端转写。
- **飞书妙记异步生成**：`lark-cli minutes +upload` 立即返回 `minute_url`，但转写是异步的，需轮询状态直到完成。
- **npm proxy 环境变量**：服务器上 `http_proxy`/`https_proxy` 可能指向未运行的本地代理（127.0.0.1:7890），导致 npm install 超时。解决：`unset http_proxy https_proxy` 或用 `npm --registry https://registry.npmmirror.com`。
- B站 API 不需要登录，但有频率限制（建议间隔 5 秒）
- 模型首次下载约 466MB（small），后续使用缓存

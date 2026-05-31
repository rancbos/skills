---
name: jw-bili-summary
description: "B站视频 → 逐字稿 → Obsidian 自动化：下载音频、whisper转写、生成带frontmatter的Markdown文档"
version: 1.0.0
agent_created: true
---

# B站视频 → 逐字稿 → Obsidian

一条命令完成：B站视频音频提取 → faster-whisper 转写 → Obsidian Markdown 生成。

## 触发条件

用户要求：
- 将 B站视频转为文字/逐字稿
- 下载 B站视频的音频并转写
- 把 B站视频内容存入 Obsidian

## 技术链路

```
B站 BV号
  → B站 API 获取视频信息 + 音频流 URL
  → curl 下载 m4a 音频
  → ffmpeg 转 16kHz WAV
  → faster-whisper (CPU) 转写
  → 繁简转换
  → 生成 Obsidian Markdown（含 frontmatter）
```

## 使用方法

### 基本用法

```bash
# 默认 tiny 模型（最快，48秒/7.5分钟视频）
bili-to-obsidian.sh BV1xzGH6uEG8

# 用 small 模型（更准，但 CPU 需要 5+ 分钟）
bili-to-obsidian.sh BV1xzGH6uEG8 small

# 传完整 URL 也行
bili-to-obsidian.sh https://www.bilibili.com/video/BV1xzGH6uEG8
```

### 从 agent 调用

```bash
/root/.hermes/scripts/bili-to-obsidian.sh <BV号> [模型大小]
```

## 模型选择

| 模型 | 速度（7.5min视频） | 准确度 | 推荐场景 |
|------|-------------------|--------|----------|
| tiny | ~48秒 | 一般，专业术语差 | 快速验证、非技术内容 |
| small | ~5分钟 | 较好 | 日常使用（需耐心等待） |
| medium | ~15分钟 | 好 | 重要内容 |
| large | ~30分钟 | 最好 | 高精度需求 |

> **CPU 限制**：当前服务器 2核 Xeon，small 以上模型较慢。tiny 模型是速度和可用性的最佳平衡。

## 输出格式

文件保存到 `/root/obsidian/B站教程/`，命名格式：`YYYY-MM-DD_标题.md`

```yaml
---
title: "视频标题"
date: 2026-05-24
tags: [B站, 逐字稿]
source: "https://bilibili.com/video/BVxxxxx"
uploader: "UP主名"
duration: "7m37s"
transcript_chars: 2219
transcript_model: "tiny"
---

# 视频标题

> UP主: xxx | 时长: 7m37s | 日期: 2026-05-24
> 来源: [B站原视频](https://bilibili.com/video/BVxxxxx)

## 逐字稿

[00:00] 第一段内容
[00:05] 第二段内容
...
```

## 依赖

| 组件 | 版本 | 状态 |
|------|------|------|
| yt-dlp | 2026.03.17 | 已安装（备用，脚本实际用 B站 API） |
| faster-whisper | 1.2.1 | 已安装 |
| ffmpeg | 系统自带 | 已安装 |
| whisper tiny 模型 | ~75MB | 已缓存（hf-mirror.com 下载） |
| whisper small 模型 | ~464MB | 已缓存 |

## 已知限制

1. **yt-dlp 412 问题**：B站对服务器 IP 返回 412，脚本改用 B站 API 直接获取音频流
2. **HuggingFace 不可达**：服务器在国内，模型需从 hf-mirror.com 下载（已缓存 tiny + small）
3. **tiny 模型专业术语差**："DeepSeek" → "DFC"，"Node.js" → "Note-S"。重要视频用 small+
4. **CPU 模式慢**：2核 Xeon，small 模型转写 7.5 分钟音频需 5+ 分钟
5. **繁简转换**：内置 100+ 常见投资/技术术语映射，但不覆盖所有生僻字

## Pitfall

1. **B站 API 需要正确 CID**：先调 `view` API 获取 cid，再用 cid 调 `playurl` API
2. **音频流有时效**：获取的音频 URL 有签名参数，需立即下载，过期需重新获取
3. **ffmpeg 必须转 16kHz 单声道**：whisper 要求 16000Hz mono WAV
4. **文件名特殊字符**：B站标题可能含 `\/:*?"<>|` 等字符，需替换为下划线
5. **长视频超时**：超过 30 分钟的视频，tiny 模型也可能需要 3+ 分钟转写

## 脚本路径

```
/root/.hermes/scripts/bili-to-obsidian.sh
```

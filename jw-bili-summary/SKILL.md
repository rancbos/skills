---
name: jw-bili-summary
description: "B站视频 → 逐字稿 → Obsidian 自动化：下载音频、whisper转写、生成带frontmatter的Markdown文档。触发词：B站视频转文字、B站视频转逐字稿、下载B站音频、B站视频存Obsidian、bilibili transcript。英文触发词：bilibili to text, b站 transcript, youtube-style transcript for bilibili."
version: 1.0.0
agent_created: true
---

# B站视频 → 逐字稿 → Obsidian

一条命令完成：B站视频音频提取 → faster-whisper 转写 → Obsidian Markdown 生成。

> **TL;DR**：`获取视频信息 → 下载音频 → whisper转写 → 繁简转换 → 生成Obsidian Markdown`。支持 tiny/small/medium/large 模型，自动处理繁简转换和文件命名。

## Iron Law（铁律）

1. **音频质量优先**：必须转换为 16kHz 单声道 WAV，确保 whisper 转写准确
2. **文件可追溯**：输出文件必须包含完整 frontmatter（标题、日期、来源、UP主、时长、模型）
3. **错误可恢复**：保留原始音频文件，转写失败时可重试
4. **命名规范化**：文件名格式 `YYYY-MM-DD_标题.md`，特殊字符替换为下划线

## 触发条件

用户要求：
- 将 B站视频转为文字/逐字稿
- 下载 B站视频的音频并转写
- 把 B站视频内容存入 Obsidian
- B站视频转文字
- B站视频转逐字稿
- 下载B站音频
- B站视频存Obsidian
- bilibili transcript
- bilibili to text
- b站 transcript
- youtube-style transcript for bilibili

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

## 工作流步骤

### Step 1: 获取视频信息 ⚠️ REQUIRED

1. 调用 B站 API 获取视频信息（标题、UP主、时长、CID）
2. 获取音频流 URL
3. **检查点**：确认视频信息正确，记录标题和时长
4. **确认门**：确认视频信息正确后继续，如信息错误需重新获取

```bash
# 从 agent 调用
/root/.hermes/scripts/bili-to-obsidian.sh <BV号> [模型大小]
```

### Step 2: 下载音频 ⚠️ REQUIRED

1. 使用 curl 下载 m4a 音频
2. 使用 ffmpeg 转换为 16kHz 单声道 WAV
3. **检查点**：确认音频文件存在且大小合理

### Step 3: whisper 转写 ⚠️ REQUIRED

1. 使用 faster-whisper 进行转写
2. 根据视频长度选择模型（tiny/small/medium/large）
3. **检查点**：确认转写文本长度合理（通常 1000-5000 字）

### Step 4: 繁简转换

1. 使用内置术语映射表进行繁简转换
2. **检查点**：抽样检查专业术语是否正确转换

### Step 5: 生成 Obsidian Markdown ⚠️ REQUIRED

1. 生成包含完整 frontmatter 的 Markdown 文件
2. 文件名格式：`YYYY-MM-DD_标题.md`
3. **检查点**：确认 frontmatter 字段完整，文件名规范
4. **确认门**：确认输出文件存在且可读后继续，如文件不存在需重新生成

### Step 6: 安全收尾

1. 删除临时文件（m4a、WAV）
2. 提示用户转写完成，告知文件位置
3. **检查点**：确认输出文件存在且可读

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

核心依赖：yt-dlp（备用）、faster-whisper（转写引擎）、ffmpeg（音频转换）。

模型选择：
- tiny：最快（48秒/7.5分钟视频），适合快速验证
- small：较好（5分钟/7.5分钟视频），日常使用
- medium：好（15分钟/7.5分钟视频），重要内容
- large：最好（30分钟/7.5分钟视频），高精度需求

> 详细依赖信息详见 `references/dependencies.md`。

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
4. **文件名特殊字符**：B站标题可能含特殊字符，需替换为下划线
5. **长视频超时**：超过 30 分钟的视频，tiny 模型也可能需要 3+ 分钟转写

## Anti-Patterns（反模式）

1. **跳过音频格式转换**：直接使用 m4a 格式转写，导致 whisper 准确度下降
2. **忽略 frontmatter**：不生成完整 frontmatter，导致 Obsidian 无法正确索引
3. **文件名不规范**：使用原始标题作为文件名，包含特殊字符导致路径错误
4. **不检查转写质量**：直接输出转写结果，不检查专业术语是否正确
5. **长视频不拆分**：超过 30 分钟的视频不拆分处理，导致转写超时

## Pre-Delivery Checklist（交付前检查）

在完成转写后，必须验证以下项目：

- [ ] 输出文件存在且可读
- [ ] frontmatter 包含完整字段（title、date、tags、source、uploader、duration、transcript_chars、transcript_model）
- [ ] 文件名格式正确（YYYY-MM-DD_标题.md）
- [ ] 转写文本长度合理（通常 1000-5000 字）
- [ ] 专业术语转换正确（抽样检查 5-10 个术语）
- [ ] 临时文件已清理（m4a、WAV）
- [ ] 用户确认转写结果

## 脚本路径

主脚本：`/root/.hermes/scripts/bili-to-obsidian.sh`

脚本功能：
- 从 B站 API 获取视频信息和音频流
- 下载音频并转换为 16kHz WAV
- 使用 faster-whisper 进行转写
- 生成 Obsidian Markdown 文件

使用方式：
```bash
# 从 agent 调用
/root/.hermes/scripts/bili-to-obsidian.sh <BV号> [模型大小]

# 示例
/root/.hermes/scripts/bili-to-obsidian.sh BV1xzGH6uEG8
/root/.hermes/scripts/bili-to-obsidian.sh BV1xzGH6uEG8 small
```

## 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| 1.0.0 | 2026-05-30 | 初始版本：B站视频 → 逐字稿 → Obsidian 自动化 |
| 1.0.1 | 2026-06-06 | 添加 Iron Law、工作流步骤、Anti-Patterns、Pre-Delivery Checklist |
| 1.0.2 | 2026-06-06 | 添加确认门、统一工作流步骤格式、优化触发条件 |

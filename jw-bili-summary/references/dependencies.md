# 依赖组件

## 核心依赖

| 组件 | 版本 | 状态 | 说明 |
|------|------|------|------|
| yt-dlp | 2026.03.17 | 已安装（备用） | 脚本实际用 B站 API |
| faster-whisper | 1.2.1 | 已安装 | 转写引擎 |
| ffmpeg | 系统自带 | 已安装 | 音频格式转换 |

## 模型依赖

| 模型 | 大小 | 状态 | 说明 |
|------|------|------|------|
| whisper tiny | ~75MB | 已缓存 | 最快，48秒/7.5分钟视频 |
| whisper small | ~464MB | 已缓存 | 较好，5分钟/7.5分钟视频 |
| whisper medium | ~1.5GB | 未缓存 | 好，15分钟/7.5分钟视频 |
| whisper large | ~3GB | 未缓存 | 最好，30分钟/7.5分钟视频 |

## 模型下载

模型从 hf-mirror.com 下载（服务器在国内，HuggingFace 不可达）。

```bash
# 下载 tiny 模型
huggingface-cli download Systran/faster-whisper-tiny --local-dir ~/.cache/huggingface/hub/models--Systran--faster-whisper-tiny

# 下载 small 模型
huggingface-cli download Systran/faster-whisper-small --local-dir ~/.cache/huggingface/hub/models--Systran--faster-whisper-small
```

## 模型选择建议

| 场景 | 推荐模型 | 原因 |
|------|----------|------|
| 快速验证、非技术内容 | tiny | 速度最快 |
| 日常使用 | small | 速度和准确度平衡 |
| 重要内容 | medium | 准确度较好 |
| 高精度需求 | large | 准确度最高 |

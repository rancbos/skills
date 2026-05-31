# B站（Bilibili）音频转写管线

> 适用于：B站视频→逐字稿→文字输出。与 YouTube 不同，B站无内置字幕 API，需下载音频后本地转写。

## 架构

```
B站 BV号 → bili_api.py 获取音频URL → curl 下载 .aac → ffmpeg 转 WAV → faster-whisper 转写 → 繁简转换 → 输出
```

## 核心依赖

```bash
pip install faster-whisper -i https://mirrors.aliyun.com/pypi/simple/
apt install ffmpeg -y
```

## B站 API 流程（绕过 412 反爬）

yt-dlp 的 BiliBili 提取器在国内服务器常返回 412。替代方案：

```python
# 1. 用浏览器获取 Cookie（必须包含 buvid3、b_nut、SESSDATA）
# 2. 请求视频 info API
GET https://api.bilibili.com/x/web-interface/view?bvid=BVID
Headers: Cookie=<browser_cookie>

# 3. 获取 cid → 请求音频流 API
GET https://api.bilibili.com/x/player/playurl?bvid=BVID&cid=CID&fnval=16
Headers: Cookie=<browser_cookie>

# 4. 从 dash.audio[0].base_url 下载音频
#    必须带 Referer: https://www.bilibili.com
```

## faster-whisper 转写

```python
from faster_whisper import WhisperModel
model = WhisperModel("small", device="cpu", compute_type="int8")
segments, info = model.transcribe("audio.wav", language="zh")
text = " ".join(s.text for s in segments)
```

- **small 模型 + CPU**：7分半视频约 3 分钟转写
- 输出常为**繁体中文**，需用 `opencc` 转简体：
  ```bash
  pip install opencc-python-reimplemented
  ```
  ```python
  from opencc import OpenCC
  cc = OpenCC('t2s')
  simplified = cc.convert(traditional_text)
  ```

## 已知问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| yt-dlp 返回 412 | B站反爬 | 改用 API 直接获取音频流 |
| 转写为繁体 | faster-whisper 默认繁体输出 | opencc t2s 转换 |
| 专业术语识别错 | whisper small 模型精度有限 | 关键术语人工校正 |
| 纯音乐视频转写为空 | 无人声 | 正常行为，提示用户 |

## 完整脚本

参考 `SKILL_DIR/scripts/bili_api.py`（B站 API 音频下载）和 `SKILL_DIR/scripts/bili-to-local.sh`（完整管线）。

如果这两个脚本不存在，说明此参考文档是独立添加的。按上述 API 流程自行实现即可。

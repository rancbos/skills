# B站 API 音频提取

B站的 yt-dlp 提取器在服务器环境返回 412 Precondition Failed。解决方案是直接走 B站公开 API。

## API 端点

### 1. 获取视频信息
```
GET https://api.bilibili.com/x/web-interface/view?bvid={bvid}
```
返回：title, duration, aid, cid, owner.name, pubdate

### 2. 获取音频流 URL（DASH 格式）
```
GET https://api.bilibili.com/x/player/playurl?avid={aid}&cid={cid}&fnval=16&qn=64
```
返回：`data.dash.audio[0].baseUrl`（音频流 URL）

### 3. 下载音频
```
GET {audio_url}
Header: Referer: https://www.bilibili.com
Header: User-Agent: Mozilla/5.0 ...
```
返回：.m4s 文件（ISO Media, MP4 Base Media）

## 关键参数

| 参数 | 值 | 说明 |
|------|-----|------|
| fnval | 16 | 请求 DASH 格式（分离音视频流） |
| qn | 64 | 音质等级（64=标准，80=高） |
| audio[0].id | 30232 | 标准音质 ID |

## 格式转换

下载的 .m4s 文件需要用 ffmpeg 转为 WAV 才能给 faster-whisper 处理：
```bash
ffmpeg -y -i audio.m4s -vn -acodec pcm_s16le -ar 16000 -ac 1 audio.wav
```

或者转为 m4a 供飞书妙记处理：
```bash
ffmpeg -y -i audio.m4s -vn -acodec copy audio.m4a
```

## 为什么 yt-dlp 失败

B站对非浏览器请求返回 412 Precondition Failed。yt-dlp 的 BiliBili 提取器无法通过：
- User-Agent 检查
- Cookie 验证（即使提供完整浏览器 cookie）
- Referer 检查

原因是 B站 还检查 TLS 指纹、JavaScript 执行环境等浏览器特征。直接用 urllib 走 API 端点则不受此限制（API 端点的反爬策略更宽松）。

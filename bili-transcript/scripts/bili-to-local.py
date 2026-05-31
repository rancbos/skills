#!/usr/bin/env python3
"""
bili-to-local.py — B站视频 → 音频下载 + faster-whisper 转写 + 存入 Obsidian
绕过 yt-dlp 的 412 问题，直接走 B站 API

用法: python3 bili-to-local.py <B站URL或BV号> [输出目录] [whisper模型]
"""
import sys
import os
import re
import json
import time
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

# ── 配置 ──
DEFAULT_OUTDIR = "/root/obsidian/B站教程"
DEFAULT_MODEL = "small"
DEVICE = "cpu"
COMPUTE_TYPE = "int8"

# ── 工具检查 ──
def check_deps():
    try:
        import faster_whisper
    except ImportError:
        print("⚠️  faster-whisper 未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "faster-whisper",
                       "-i", "https://mirrors.aliyun.com/pypi/simple/", "-q"], check=True)
    
    try:
        from opencc import OpenCC
    except ImportError:
        print("⚠️  opencc 未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "opencc-python-reimplemented",
                       "-i", "https://mirrors.aliyun.com/pypi/simple/", "-q"], check=True)

# ── 解析 BV 号 ──
def parse_bvid(input_str):
    """从 URL 或纯 BV 号提取 bvid"""
    match = re.search(r'(BV[\w]{10})', input_str)
    if match:
        return match.group(1)
    raise ValueError(f"无法解析 BV 号: {input_str}")

# ── B站 API ──
def get_video_info(bvid):
    """通过 B站 API 获取视频信息"""
    import urllib.request
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.bilibili.com"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    if data["code"] != 0:
        raise RuntimeError(f"B站 API 错误: {data}")
    d = data["data"]
    return {
        "title": d["title"],
        "duration": d["duration"],
        "aid": d["aid"],
        "cid": d["cid"],
        "owner": d["owner"]["name"],
        "upload_date": d["pubdate"],
        "bvid": bvid,
    }

def get_audio_url(aid, cid):
    """获取音频流 URL"""
    import urllib.request
    url = f"https://api.bilibili.com/x/player/playurl?avid={aid}&cid={cid}&fnval=16&qn=64"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.bilibili.com"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    if data["code"] != 0:
        raise RuntimeError(f"获取音频 URL 失败: {data}")
    audio = data["data"]["dash"]["audio"][0]
    return audio.get("baseUrl") or audio.get("base_url")

def download_audio(audio_url, output_path):
    """下载音频文件"""
    import urllib.request
    req = urllib.request.Request(audio_url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.bilibili.com"
    })
    with urllib.request.urlopen(req, timeout=120) as resp:
        with open(output_path, "wb") as f:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                f.write(chunk)
    return os.path.getsize(output_path)

def convert_to_wav(input_path, output_path):
    """用 ffmpeg 转换为 WAV"""
    subprocess.run([
        "ffmpeg", "-y", "-i", input_path,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        output_path
    ], capture_output=True, check=True)
    return os.path.getsize(output_path)

def transcribe(audio_path, model_name):
    """用 faster-whisper 转写"""
    from faster_whisper import WhisperModel
    
    print(f"  加载模型: {model_name}...", flush=True)
    model = WhisperModel(model_name, device=DEVICE, compute_type=COMPUTE_TYPE)
    
    print(f"  转写中...", flush=True)
    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        language="zh",
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )
    
    lines = []
    for seg in segments:
        start_min = int(seg.start // 60)
        start_sec = int(seg.start % 60)
        line = f"[{start_min:02d}:{start_sec:02d}] {seg.text.strip()}"
        lines.append(line)
    
    return "\n".join(lines)

def to_simplified(text):
    """繁简转换"""
    try:
        from opencc import OpenCC
        cc = OpenCC('t2s')
        return cc.convert(text)
    except:
        return text

def get_audio_duration(wav_path):
    """获取音频时长"""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", wav_path],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())

def save_to_obsidian(info, transcript, outdir):
    """保存到 Obsidian"""
    os.makedirs(outdir, exist_ok=True)
    
    date_str = datetime.fromtimestamp(info["upload_date"]).strftime("%Y-%m-%d")
    safe_title = re.sub(r'[\/\\:*?"<>|]', '_', info["title"])[:100]
    duration_min = info["duration"] // 60
    duration_sec = info["duration"] % 60
    duration_fmt = f"{duration_min}m{duration_sec}s"
    char_count = len(transcript)
    est_tokens = char_count * 7 // 10
    
    md_file = os.path.join(outdir, f"{date_str}_{safe_title}.md")
    
    md_content = f"""---
title: "{info['title']}"
date: {date_str}
tags: [B站, 逐字稿]
source: "https://bilibili.com/video/{info['bvid']}"
uploader: "{info['owner']}"
duration: "{duration_fmt}"
transcript_chars: {char_count}
transcript_model: "small"
---

# {info['title']}

> UP主: {info['owner']} | 时长: {duration_fmt} | 日期: {date_str}
> 来源: [B站原视频](https://bilibili.com/video/{info['bvid']})

## 逐字稿

{transcript}

---
*由 faster-whisper (small) 自动生成，{char_count}字 ≈ {est_tokens} tokens*
"""
    
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    return md_file, char_count, est_tokens

# ── 主流程 ──
def main():
    if len(sys.argv) < 2:
        print("用法: python3 bili-to-local.py <B站URL或BV号> [输出目录] [whisper模型]")
        sys.exit(1)
    
    input_str = sys.argv[1]
    outdir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUTDIR
    model_name = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_MODEL
    
    check_deps()
    
    bvid = parse_bvid(input_str)
    
    # Step 1: 获取视频信息
    print("📡 获取视频信息...", flush=True)
    info = get_video_info(bvid)
    duration_min = info["duration"] // 60
    duration_sec = info["duration"] % 60
    est_time = info["duration"] * 3 // 10  # CPU small 模型约 0.3x 实时
    
    print(f"  标题: {info['title']}", flush=True)
    print(f"  UP主: {info['owner']}", flush=True)
    print(f"  时长: {duration_min}m{duration_sec}s", flush=True)
    print(f"  预估转写时间: ~{est_time}秒", flush=True)
    
    # Step 2: 获取音频 URL
    print("\n🔗 获取音频流...", flush=True)
    audio_url = get_audio_url(info["aid"], info["cid"])
    print(f"  获取成功", flush=True)
    
    # Step 3: 下载音频
    print("\n⬇️  下载音频...", flush=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        m4s_path = os.path.join(tmpdir, "audio.m4s")
        wav_path = os.path.join(tmpdir, "audio.wav")
        
        size = download_audio(audio_url, m4s_path)
        print(f"  下载完成: {size / 1024 / 1024:.1f}MB", flush=True)
        
        # Step 4: 转换为 WAV
        print("\n🔄 转换格式...", flush=True)
        convert_to_wav(m4s_path, wav_path)
        duration = get_audio_duration(wav_path)
        print(f"  WAV: {duration:.0f}秒", flush=True)
        
        # Step 5: 转写
        print(f"\n🎙️  开始转写 (模型: {model_name})...", flush=True)
        start = time.time()
        transcript = transcribe(wav_path, model_name)
        elapsed = time.time() - start
        print(f"  转写完成: {len(transcript)}字, 耗时 {elapsed:.0f}秒", flush=True)
    
    # Step 6: 繁简转换
    print("\n🔤 繁简转换...", flush=True)
    transcript_simplified = to_simplified(transcript)
    
    # Step 7: 存入 Obsidian
    print("\n📝 存入 Obsidian...", flush=True)
    md_file, char_count, est_tokens = save_to_obsidian(info, transcript_simplified, outdir)
    
    print(f"\n{'='*50}", flush=True)
    print(f"  标题: {info['title']}", flush=True)
    print(f"  字数: {char_count}", flush=True)
    print(f"  Tokens: ~{est_tokens}", flush=True)
    print(f"  文件: {md_file}", flush=True)
    print(f"{'='*50}", flush=True)

if __name__ == "__main__":
    main()
